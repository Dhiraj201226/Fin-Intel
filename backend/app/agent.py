import json
import datetime
import random
from app.llm_helper import LLMHelper
from app.tools.research import tavily_web_search
from app.tools.reporting import ReportGenerator
from app.memory_store import EpisodicMemory, ChromaVectorStore
from app.tools.financial_engine import FinancialRecommendationEngine
from app.tools.yfinance_client import fetch_yfinance_facts

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

        # Stage 2: Tavily Web Search (Tier 2)
        if not early_stopped and iteration < self.max_steps:
            yield self._format_sse("thought", "Search Stage 2: Query not fully answered. Falling back to Tavily Web Search (Tier 2) for live internet data.", 2, iteration)
            
            yield self._format_sse("action", f"tavily_web_search(query='{query}')", 2, iteration)
            tavily_results = tavily_web_search(query, max_results=3)
            tools_used.append("tavily_web_search")
            
            if tavily_results:
                top_snippet = tavily_results[0]["snippet"]
                yield self._format_sse("observation", f"Tavily Search returned {len(tavily_results)} results. Top result: {top_snippet[:200]}...", 2, iteration)
                accumulated_context += "Tavily Web Search (Tier 2):\n"
                
                # Semantic Caching: Store these web results into the Vector DB for future queries
                web_chunks = []
                web_metadata = []
                for res in tavily_results:
                    accumulated_context += f"- [{res['title']}] {res['snippet']} ({res['url']})\n"
                    # Limit chunk size to ~800 chars for vector db
                    chunk = res['snippet'][:800]
                    web_chunks.append(chunk)
                    web_metadata.append({
                        "ticker": "WEB", 
                        "tier": "Tier 2 (Web Cache)", 
                        "source_name": res['title'], 
                        "url": res['url']
                    })
                
                # Generate embeddings and store
                if web_chunks:
                    try:
                        web_emb = LLMHelper.generate_embeddings(web_chunks, provider=self.provider, api_key=self.api_key)
                        self.vector_store.add_documents(web_chunks, web_emb, web_metadata)
                        yield self._format_sse("thought", "Saved Tier 2 search results to local Vector DB for future semantic caching.", 2, iteration)
                    except Exception as e:
                        yield self._format_sse("error", f"Failed to cache web results: {str(e)}", 2, iteration)
            else:
                yield self._format_sse("observation", "Tavily Web Search returned no results.", 2, iteration)

            if self._check_if_query_answered(query, accumulated_context):
                early_stopped = True
                stopping_stage = 2
                yield self._format_sse("thought", "Query fully answered at Stage 2 (Tavily Web Search). Stopping search loop.", 2, iteration)
                
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
                                    
                            if clean_name in query.lower() and len(clean_name) > 2:
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

        yield self._format_sse("thought", "Math engine execution complete. Compiling final report...", 0, iteration)

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

Analyze the following computed scores and raw data.
Your goal is to write a highly impressive, sophisticated, and institutional-grade financial report. Use elegant, professional Wall Street terminology and speak with absolute authority. Do not use boring, robotic, or generic phrasing.

ENGINE OUTPUT:
Final Score: {engine_result.get('final_score', 50):.1f}/100
Recommendation: {engine_result.get('recommendation', 'HOLD')}

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
        
        yield self._format_sse("report", report, 0, iteration)

        status_str = "EARLY_STOPPED" if early_stopped else "SUCCESS"
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
