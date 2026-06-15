import json
import datetime
import random
from app.llm_helper import LLMHelper
from app.tools.reporting import ReportGenerator
from app.memory_store import EpisodicMemory, ChromaVectorStore
from app.tools.financial_engine import FinancialRecommendationEngine
from app.tools.yfinance_client import fetch_yfinance_facts, generate_candlestick_chart

MAX_ITER = 12

class ReActAgent:
    """Orchestrates the ReAct reasoning loops (Thought -> Action -> Observation) and memory writes."""
    
    def __init__(self, provider="gemini", api_key=None, max_steps=MAX_ITER, temperature=0.3):
        self.provider = provider
        self.api_key = api_key
        self.max_steps = min(max_steps, MAX_ITER)
        self.temperature = temperature
        self.episodic_memory = EpisodicMemory()
        self.vector_store = ChromaVectorStore()

    def _check_if_query_answered(self, query: str, context: str) -> bool:
        """Determines if the current retrieved context satisfies the user query using the LLM."""
        if not context:
            return False
            
        # Bypass LLM validation to save severe rate-limit quotas (5 requests/min)
        query_words = [w.strip("?,.!:;()\"'") for w in query.lower().split() if len(w) > 3]
        if not query_words:
            return False
        match_count = sum(1 for word in query_words if word in context.lower())
        if match_count >= max(1, len(query_words) * 0.75):
            return True
        return False

    def _format_sse(self, event_type: str, content: str, tier: int, iteration: int) -> dict:
        data = {
            "type": event_type,
            "content": content,
            "tier": tier,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "iteration": iteration
        }
        return {"data": json.dumps(data)}

    def run(self, query: str, ticker: str = None):
        """Runs the 2-Tier ReAct agent cycle for a given query."""
        tools_used = []
        failures = "None"
        recovery = "N/A"
        early_stopped = False
        stopping_stage = 0

        accumulated_context = ""
        iteration = 0

        # --- INTENT CLASSIFIER ---
        yield self._format_sse("thought", "Classifying query intent...", 0, iteration)
        intent_prompt = f"Does the following user query ask for a stock recommendation/financial analysis of a company, or is it asking to analyze uploaded documents/custom data? (Hint: if the query asks to 'summarize', mentions a 'section', or asks questions about text, it is likely 'ANALYSIS'). Reply with exactly 'RECOMMENDATION' or 'ANALYSIS'.\n\nQuery: {query}"
        intent_response = LLMHelper.generate_text(intent_prompt, provider=self.provider, api_key=self.api_key)
        
        intent = "ANALYSIS" if "ANALYSIS" in intent_response.upper() and "RECOMMENDATION" not in intent_response.upper() else "RECOMMENDATION"
        
        # If both words appear (e.g. "It is RECOMMENDATION, not ANALYSIS"), default to RECOMMENDATION
        if "RECOMMENDATION" in intent_response.upper():
            intent = "RECOMMENDATION"
        elif "ANALYSIS" in intent_response.upper():
            intent = "ANALYSIS"
            
        if "[DEMO MODE]" in intent_response:
            intent = "RECOMMENDATION"

        yield self._format_sse("observation", f"Intent Classified as: {intent}", 0, iteration)

        if intent == "ANALYSIS":
            yield self._format_sse("thought", "Executing Document Analysis Branch...", 0, iteration)
            q_emb = LLMHelper.generate_embeddings([query], provider=self.provider, api_key=self.api_key)[0]
            
            yield self._format_sse("action", "vector_store.similarity_search(source_type='user_upload', k=22)", 0, iteration)
            doc_results = self.vector_store.similarity_search(q_emb, k=22, custom_where={"source_type": "user_upload"})
            
            if not doc_results:
                yield self._format_sse("error", "No uploaded documents found to analyze. Please upload a PDF document first.", 0, iteration)
                yield self._format_sse("done", "Episode complete", 0, iteration)
                return
            
            context = "\n\n".join([res['snippet'] for res in doc_results])
            yield self._format_sse("observation", f"Retrieved {len(doc_results)} chunks from uploaded documents.", 0, iteration)
            
            yield self._format_sse("thought", "Generating answer based on uploaded documents...", 0, iteration)
            analysis_prompt = f"""SYSTEM ROLE: You are a strict, precise financial document analyst.
You must use ONLY the provided Document Text to answer the user's query.

RULES:
1. If the user requests a summary, provide a concise, structured summary of the relevant sections.
2. ALWAYS provide a conversational, fully-formed contextual answer. Do NOT answer with just a single number or word (e.g. "8%"). Explain your reasoning and quote the relevant figures.
3. When analyzing tabular data, synthesize and summarize the table's contents, trends, and key metrics. Do NOT just copy-paste the raw table, and do NOT skip over important context.
4. Answer ONLY from the retrieved context. Do not use outside knowledge.
5. Do not provide investment recommendations unless explicitly requested.
6. Do not assume facts that are not present, BUT you may recognize standard financial synonyms (e.g., Turnover = Revenue) when interpreting the user's query against the context.
7. Do NOT introduce yourself. Do not say "I am a financial document analyst" or ask for a question. Just output the final answer directly.
8. If the requested information is completely missing and cannot be found in the context, respond EXACTLY with: "The information is not available in the provided document."

---
DOCUMENT TEXT:
{context}

---
USER QUERY: {query}

CRITICAL INSTRUCTION: Based ONLY on the DOCUMENT TEXT above, fulfill the USER QUERY. Do not write anything else except the direct answer.
FINAL ANSWER:"""
            report = LLMHelper.generate_text(analysis_prompt, provider=self.provider, api_key=self.api_key)
            
            if "Error executing text generation" in report and ("429" in report or "quota" in report.lower()):
                yield self._format_sse("rate_limit_error", "Gemini Free-Tier Rate Limit Hit (429). Please switch to OpenAI or Ollama.", 0, iteration)
                yield self._format_sse("done", "Episode complete", 0, iteration)
                return

            yield self._format_sse("report", report, 0, iteration)
            yield self._format_sse("done", "Episode complete", 0, iteration)
            return

        # Check Vector DB Cache first (Recommendation Branch)
        yield self._format_sse("thought", "Checking Vector DB for cached answers...", 0, iteration)
        try:
            q_emb = LLMHelper.generate_embeddings([query], provider=self.provider, api_key=self.api_key)[0]
            cached_results = self.vector_store.collection.query(
                query_embeddings=[q_emb],
                n_results=1,
                where={"$and": [{"source_type": "cache"}, {"query": query}]}
            )
            if cached_results and cached_results.get('documents') and cached_results['documents'][0]:
                doc = cached_results['documents'][0][0]
                meta = cached_results['metadatas'][0][0]
                cached_time_str = meta.get("timestamp", "")
                if cached_time_str:
                    # Handle python 3.10 fromisoformat which might not support the Z suffix properly if we used it, but we used standard isoformat
                    # Actually standard isoformat doesn't have Z unless appended. In memory_store we did `.isoformat()`
                    # but let's be safe:
                    clean_time_str = cached_time_str.replace("Z", "+00:00")
                    cached_time = datetime.datetime.fromisoformat(clean_time_str)
                    # Convert to naive if it's aware to match utcnow(), or convert utcnow() to aware
                    if cached_time.tzinfo is not None:
                        cached_time = cached_time.replace(tzinfo=None)
                    
                    if (datetime.datetime.utcnow() - cached_time).total_seconds() < 86400:
                        yield self._format_sse("observation", "Found valid cached report in Vector DB (under 24 hours old).", 0, iteration)
                        
                        # Retrieve and send the cached chart if it exists
                        ticker_meta = meta.get("ticker", "")
                        if ticker_meta and ticker_meta != "GENERIC":
                            import os, base64
                            chart_path = os.path.join(os.path.dirname(__file__), "..", "temp_charts", f"{ticker_meta}_chart.png")
                            if os.path.exists(chart_path):
                                try:
                                    with open(chart_path, "rb") as image_file:
                                        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                                    yield self._format_sse("chart", f"data:image/png;base64,{encoded_string}", 0, iteration)
                                except Exception as e:
                                    pass

                        yield self._format_sse("report", doc, 0, iteration)
                        yield self._format_sse("done", "Episode complete (served from cache)", 0, iteration)
                        return
        except Exception as e:
            yield self._format_sse("error", f"Cache lookup failed: {str(e)}", 0, iteration)

        # Stage 1: Local SEC Vector DB (Tier 1)
        if iteration < self.max_steps:
            yield self._format_sse("thought", "Search Stage 1: Querying local Vector DB for verified SEC Filings (Tier 1).", 1, iteration)
            
            # Generate query embedding
            q_emb = LLMHelper.generate_embeddings([query], provider=self.provider, api_key=self.api_key)[0]
            
            yield self._format_sse("action", "vector_store.similarity_search()", 1, iteration)
            sec_results = self.vector_store.similarity_search(q_emb, k=3, filter_ticker=ticker)
            tools_used.append("vector_store")
            
            if sec_results:
                sec_snippet = sec_results[0]["snippet"]
                yield self._format_sse("observation", f"Retrieved {len(sec_results)} relevant chunks from local database. Top chunk: {sec_snippet[:200]}...", 1, iteration)
                accumulated_context += "SEC Filings (Tier 1):\n"
                for res in sec_results:
                    accumulated_context += f"- {res['snippet']}\n"
            else:
                yield self._format_sse("observation", "No relevant SEC filings found in local Vector DB.", 1, iteration)

            if self._check_if_query_answered(query, accumulated_context):
                early_stopped = True
                stopping_stage = 1
                yield self._format_sse("thought", "Query fully answered at Stage 1 (SEC Filings). Stopping search early.", 1, iteration)
            
            iteration += 1


        if iteration >= self.max_steps:
            yield self._format_sse("error", "MAX_ITER overflow reached. Forcing report generation.", 0, iteration)

        yield self._format_sse("thought", "Extracting exact financial metrics using live Yahoo Finance data...", 0, iteration)

        # Dynamic Ticker Resolution via CSV Mapping
        if not ticker:
            import os
            import csv
            csv_path = os.path.join(os.path.dirname(__file__), "ticker_mapping.csv")
            try:
                if os.path.exists(csv_path):
                    with open(csv_path, mode='r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None) # skip header
                        
                        # Filter out empty rows to prevent list index out of range errors
                        rows = [row for row in reader if len(row) >= 2]
                        # Sort by length descending to match longest names first (e.g. "Tata Motors" before "Tata")
                        rows.sort(key=lambda x: len(x[0]), reverse=True)
                        
                        for row in rows:
                            company_name = row[0]
                            mapped_ticker = row[1]
                            
                            clean_name = company_name.lower()
                            for suffix in [" limited", " ltd.", " ltd", " incorporation", " inc.", " inc", " corporation", " corp.", " corp"]:
                                if clean_name.endswith(suffix):
                                    clean_name = clean_name[:-len(suffix)].strip()
                                    
                            import re
                            if re.search(rf"\b{re.escape(clean_name)}\b", query.lower()) and len(clean_name) > 2:
                                ticker = mapped_ticker
                                yield self._format_sse("thought", f"Dynamically mapped '{company_name}' to ticker {ticker} from local registry.", 0, iteration)
                                break
            except Exception as e:
                yield self._format_sse("error", f"Failed to load ticker mapping: {str(e)}", 0, iteration)

        if not ticker:
            yield self._format_sse("error", "Failed to resolve a valid stock ticker from the query. Aborting financial analysis.", 0, iteration)
            yield self._format_sse("done", "Episode complete", 0, iteration)
            return

        metrics = {}
        if ticker:
            yield self._format_sse("action", f"fetch_yfinance_facts(ticker='{ticker}')", 0, iteration)
            try:
                raw_metrics = fetch_yfinance_facts(ticker)
                
                if "error" in raw_metrics:
                    yield self._format_sse("error", f"Data Extraction Failed: {raw_metrics['error']}", 0, iteration)
                    yield self._format_sse("done", "Episode complete", 0, iteration)
                    return
                    
                yield self._format_sse("observation", f"Retrieved official yfinance fundamental facts.", 0, iteration)
                metrics = raw_metrics
            except Exception as e:
                yield self._format_sse("error", f"Failed to retrieve yfinance facts: {str(e)}", 0, iteration)

        # Run the deterministic math engine
        engine = FinancialRecommendationEngine()
        engine_result = engine.calculate(query, metrics)
        
        # Override raw metrics with the ones containing the engine's computed ratios (ROE, FCF Yield, etc.)
        metrics = engine_result.get("computed_metrics", metrics)
        
        yield self._format_sse("observation", f"Math Engine Final Output: {json.dumps(engine_result)}", 0, iteration)

        # Generate chart and evaluate sentiment only if requested
        chart_sentiment = "UNAVAILABLE"
        chart_path = None
        wants_chart = any(word in query.lower() for word in ['chart', 'visual', 'graph', 'plot', 'candlestick'])
        
        if wants_chart:
            yield self._format_sse("thought", "User requested visualization. Generating 2-month candlestick chart...", 0, iteration)
            chart_path = generate_candlestick_chart(ticker)
        
        if chart_path:
            yield self._format_sse("thought", "Evaluating visual market sentiment...", 0, iteration)
            sentiment_prompt = "Analyze this 2-month candlestick chart. Evaluate the trend and reply with exactly one word representing the overall technical market sentiment: POSITIVE, NEGATIVE, or NEUTRAL."
            raw_sentiment = LLMHelper.generate_text(sentiment_prompt, provider=self.provider, api_key=self.api_key, image_path=chart_path)
            
            if "Error executing text generation" in raw_sentiment and ("429" in raw_sentiment or "quota" in raw_sentiment.lower()):
                yield self._format_sse("error", "Vision API limit exceeded. Skipping visual sentiment analysis.", 0, iteration)
                chart_sentiment = "UNAVAILABLE"
            else:
                # Clean response to 1 word just in case
                if "POSITIVE" in raw_sentiment.upper(): chart_sentiment = "POSITIVE"
                elif "NEGATIVE" in raw_sentiment.upper(): chart_sentiment = "NEGATIVE"
                elif "NEUTRAL" in raw_sentiment.upper(): chart_sentiment = "NEUTRAL"
                else: chart_sentiment = "UNAVAILABLE"
            
            yield self._format_sse("observation", f"Visual Sentiment Output: {chart_sentiment}", 0, iteration)
            
            # Send chart image to frontend
            try:
                import base64
                with open(chart_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                yield self._format_sse("chart", f"data:image/png;base64,{encoded_string}", 0, iteration)
            except Exception as e:
                yield self._format_sse("error", f"Failed to encode chart image: {str(e)}", 0, iteration)

        yield self._format_sse("thought", "Math engine & chart execution complete. Compiling final report...", 0, iteration)

        # Basic report generation
        # Format large numbers to prevent LLM zero-counting hallucinations
        def humanize_number(val):
            if isinstance(val, dict):
                return {k: humanize_number(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [humanize_number(v) for v in val]
            elif isinstance(val, (int, float)) and val != 0:
                abs_val = abs(val)
                if abs_val >= 1e12:
                    return f"{val / 1e12:.2f} Trillion"
                elif abs_val >= 1e9:
                    return f"{val / 1e9:.2f} Billion"
                elif abs_val >= 1e6:
                    return f"{val / 1e6:.2f} Million"
                return round(val, 2)
            return val

        formatted_metrics = humanize_number(metrics)

        prompt = f"""You are an elite, top-tier Wall Street Financial Analyst AI evaluating the stock {ticker}.

Analyze the following computed scores, chart sentiment, and raw data.
Your goal is to write a highly impressive, sophisticated, and institutional-grade financial report. Use elegant, professional Wall Street terminology and speak with absolute authority. Do not use boring, robotic, or generic phrasing.

ENGINE OUTPUT:
Final Score: {engine_result.get('final_score', 50):.1f}/100
Recommendation: {engine_result.get('recommendation', 'HOLD')}
Technical Chart Sentiment (2-Month): {chart_sentiment}

Category Scores:
- Growth Score: {engine_result.get('growth_score', 50)}
- Profitability Score: {engine_result.get('profitability_score', 50)}
- Health Score: {engine_result.get('health_score', 50)}
Reasoning: {', '.join(engine_result.get('reasoning', []))}

RAW METRICS & COMPUTED RATIOS:
{json.dumps(formatted_metrics, indent=2)}

User Query: {query}

Retrieved Context:
{accumulated_context}

Report Format:
1. Executive Summary (Directly state the engine's {engine_result.get('recommendation', 'HOLD')} recommendation and final score in the first sentence)
2. Recommendation Reasoning 
   - Use a simple bulleted list to explicitly explain WHY this recommendation was given.
   - Use ✓ to list the top 2-3 Strengths (e.g. ✓ Strong cash flow generation)
   - Use ⚠ to list the top 1-2 Weaknesses/Risks (e.g. ⚠ High debt to equity ratio)
3. Key Financial Ratios
   - Explicitly list the following ratios if available in the RAW METRICS (format cleanly): ROE, ROIC, Current Ratio, Debt/Equity, Net Debt/EBITDA, Interest Coverage, and FCF Yield.
4. Scoring & Calculation 
   - Display the exact Engine Output provided above.
   - DATA GAPS: If any metric or historical year is missing from the raw data, explicitly state that it is missing. Do not invent it.
   - TONE: The writing should be highly impressive and sophisticated. Weave the data into a compelling institutional narrative rather than just robotically listing numbers.
   - CRITICAL: These financial metrics are denominated in '{metrics.get('currency', 'USD')}'. Ensure you use the correct currency symbol (e.g., ₹ for INR, $ for USD).
   - ANTI-HALLUCINATION GUARDRAIL: You are STRICTLY FORBIDDEN from calculating your own percentages, ratios, or math. You must ONLY use the exact numbers provided in the RAW METRICS. Do NOT invent or hallucinate metrics (like "-4.2% growth") that do not exist in the context above.
5. Investment Thesis
   - Bull Case: Provide 3 short bullet points outlining the core strengths of the company.
   - Bear Case: Provide 3 short bullet points outlining the core risks or weaknesses.
6. Qualitative Insights & Forward-Looking Risks (Based on Context/News)
   - Explain management plans, why profit fell/rose, and any risks explicitly mentioned in the context.
7. Sources & Verification
   - Use this exact sentence: "This report is based on publicly available financial statements, market data, and company disclosures." Do not mention SEC filings unless they are explicitly in the context.
"""
        report = LLMHelper.generate_text(prompt, provider=self.provider, api_key=self.api_key)
        
        if "Error executing text generation" in report and ("429" in report or "quota" in report.lower()):
            yield self._format_sse("rate_limit_error", "Gemini Free-Tier Rate Limit Hit (429). Please switch to OpenAI or Ollama.", 0, iteration)
            yield self._format_sse("done", "Episode complete", 0, iteration)
            return

        yield self._format_sse("report", report, 0, iteration)

        # Save report to Vector DB Cache
        try:
            cache_meta = [{
                "source_type": "cache",
                "tier": "Cache",
                "ticker": ticker or "GENERIC",
                "source_name": "Agent Cache",
                "query": query,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }]
            # We use q_emb if available, otherwise generate it
            c_emb = LLMHelper.generate_embeddings([query], provider=self.provider, api_key=self.api_key)[0]
            self.vector_store.add_documents([report], [c_emb], cache_meta)
        except Exception as e:
            yield self._format_sse("error", f"Failed to cache final report: {str(e)}", 0, iteration)

        status_str = "EARLY_STOPPED" if early_stopped else "SUCCESS"
        if not early_stopped:
            self.episodic_memory.log_episode(
                episode_id=f"EP-{random.randint(1000, 9999)}",
                query=query,
                status=status_str,
                tools_used=tools_used,
                failures=failures,
                recovery=recovery,
                strategy=f"2-Tier strategy executed. Early stopped: {early_stopped} at Stage {stopping_stage}."
            )

        yield self._format_sse("done", "Episode complete", 0, iteration)
