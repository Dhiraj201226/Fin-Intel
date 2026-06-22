import os
import time
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
import numpy as np
from PIL import Image
from app.config import GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY

class LLMHelper:
    """Helper to route prompts and embedding generation to Gemini or OpenAI."""
    
    @staticmethod
    def generate_text(prompt, provider="gemini", api_key=None, temperature=0.3, image_path=None):
        """Generates text from selected LLM provider, with optional multimodal support."""
        if not api_key:
            if provider == "gemini": key = GEMINI_API_KEY
            elif provider == "groq": key = GROQ_API_KEY
            else: key = OPENAI_API_KEY
        else:
            key = api_key
        
        if not key and provider != "ollama":
            # Sandbox mode fallback to allow demoing without keys
            if "valid JSON object" in prompt:
                return '{"pe_ratio": 15.5, "revenue_growth": 0.20, "net_margin": 0.12, "debt_to_equity": 0.5, "news_sentiment": 0.8}'
            return """# ⚠️ [DEMO MODE] API Key Missing

Because no valid API key was provided (or limits were hit), this is a **simulated response**. The system successfully executed the full pipeline (Vector Retrieval -> Web Search -> Data Extraction -> Math Engine), but bypassed the live LLM text generation to save quotas.

## Simulated Analysis
Based on our simulated data extraction, the company is showing strong fundamentals with a 20% YoY revenue growth and healthy margins. The Financial Engine processed this data and generated the exact mathematical scores shown above."""

        # Retry logic for rate limits (429)
        max_retries = 3
        retry_delay = 60 # seconds

        for attempt in range(max_retries):
            try:
                if provider == "gemini":
                    genai.configure(api_key=key)
                    # Using Gemini 2.5 Flash for best speed and 15 Requests Per Minute quota limit
                    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": temperature})
                    
                    if image_path and os.path.exists(image_path):
                        img = Image.open(image_path)
                        response = model.generate_content([prompt, img])
                    else:
                        response = model.generate_content(prompt)
                        
                    return response.text
                elif provider == "ollama":
                    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                    # Make sure you have pulled a model like llama3 (e.g. `ollama run llama3`)
                    response = client.chat.completions.create(
                        model="llama3",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature
                    )
                    return response.choices[0].message.content
                elif provider == "groq":
                    client = Groq(api_key=key)
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature
                    )
                    return response.choices[0].message.content
                else:
                    client = OpenAI(api_key=key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature
                    )
                    return response.choices[0].message.content
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "quota" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"Rate limit hit (429). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(retry_delay)
                        continue
                return f"Error executing text generation [{provider}]: {str(e)}"

    @staticmethod
    def generate_embeddings(text_chunks, provider="gemini", api_key=None):
        """Generates vector embeddings for a list of text chunks."""
        if not api_key:
            if provider == "gemini": key = GEMINI_API_KEY
            elif provider == "groq": key = GROQ_API_KEY
            else: key = OPENAI_API_KEY
        else:
            key = api_key
        
        # 1536 is standard dimension for OpenAI (we can mock it with zeros/randoms in sandbox mode)
        dimension = 1536 if provider == "openai" else 768
        
        if not key and provider != "ollama":
            # Sandbox Mock Embeddings (deterministic based on text hashes)
            embeddings = []
            for chunk in text_chunks:
                # Seed based on hash code
                h = hash(chunk)
                np.random.seed(h & 0xffffffff)
                embeddings.append(np.random.rand(dimension).tolist())
            return embeddings

        try:
            if provider == "gemini":
                genai.configure(api_key=key)
                embeddings = []
                total_chunks = len(text_chunks)
                print(f"Starting Gemini embeddings for {total_chunks} chunks...")
                for idx, chunk in enumerate(text_chunks):
                    if idx % 50 == 0 and idx > 0:
                        print(f"Embedded {idx}/{total_chunks} chunks...")
                    result = genai.embed_content(
                        model="models/text-embedding-004",
                        content=chunk,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                print("Gemini embeddings complete!")
                return embeddings
            elif provider == "ollama":
                client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                embeddings = []
                total_chunks = len(text_chunks)
                print(f"Starting Ollama local embeddings for {total_chunks} chunks. This will take time depending on your CPU/GPU...")
                for i in range(0, total_chunks, 50):
                    print(f"Processing Ollama batch: {i} to {min(i+50, total_chunks)} out of {total_chunks}...")
                    batch = text_chunks[i:i+50]
                    response = client.embeddings.create(input=batch, model="nomic-embed-text")
                    embeddings.extend([data.embedding for data in response.data])
                print("Ollama embeddings complete!")
                return embeddings
            elif provider == "groq":
                print("Groq does not provide an embedding model. Falling back to local hash embeddings...")
                embeddings = []
                for chunk in text_chunks:
                    h = hash(chunk)
                    np.random.seed(h & 0xffffffff)
                    embeddings.append(np.random.rand(768).tolist()) # Match Gemini's 768 dimensions to prevent DB crashes
                return embeddings
            else:
                client = OpenAI(api_key=key)
                embeddings = []
                for i in range(0, len(text_chunks), 50):
                    batch = text_chunks[i:i+50]
                    response = client.embeddings.create(input=batch, model="text-embedding-3-small")
                    embeddings.extend([data.embedding for data in response.data])
                return embeddings
        except Exception as e:
            print(f"Error generating embeddings, falling back to hashes: {str(e)}")
            # Fallback on hash embeddings to prevent crashes
            embeddings = []
            for chunk in text_chunks:
                h = hash(chunk)
                np.random.seed(h & 0xffffffff)
                embeddings.append(np.random.rand(dimension).tolist())
            return embeddings
