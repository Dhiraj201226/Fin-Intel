from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import re
from typing import Optional
import fitz  # PyMuPDF
import datetime

from sse_starlette.sse import EventSourceResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.agent import ReActAgent
from app.memory_store import EpisodicMemory, ChromaVectorStore
from app.llm_helper import LLMHelper
from app.auth import APIKeyAuthMiddleware
from fastapi.staticfiles import StaticFiles

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ARA-1 Autonomous Financial Research Agent Backend")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(APIKeyAuthMiddleware)

# Enable CORS for React Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static charts directory
charts_dir = os.path.join(os.path.dirname(__file__), "..", "temp_charts")
os.makedirs(charts_dir, exist_ok=True)
app.mount("/api/charts", StaticFiles(directory=charts_dir), name="charts")

class ResearchRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    session_id: Optional[str] = None

class SecFetchRequest(BaseModel):
    ticker: str

@app.get("/")
def read_root():
    return {"status": "online", "agent": "ARA-1", "version": "1.0.0"}

@app.post("/api/research")
@limiter.limit("10/minute")
async def execute_research(
    request: Request,
    req: ResearchRequest,
    x_llm_provider: Optional[str] = Header("gemini"),
    x_llm_api_key: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_session_id: Optional[str] = Header(None),
    x_llm_max_steps: Optional[str] = Header("12"),
    x_llm_temperature: Optional[str] = Header("0.3")
):
    """Orchestrates ReAct agent loop for research queries and streams SSE."""
    if not req.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        max_steps = int(x_llm_max_steps)
        temp = float(x_llm_temperature)
    except:
        max_steps = 12
        temp = 0.3

    agent = ReActAgent(
        provider=x_llm_provider,
        api_key=x_llm_api_key,
        max_steps=max_steps,
        temperature=temp,
        session_id=x_session_id or req.session_id or "GLOBAL"
    )
    
    logs = []
    report = ""
    for event in agent.run(req.query, req.ticker):
        # event is dict like {"data": '{"type": "...", "content": "..."}'}
        try:
            event_data = json.loads(event["data"])
            if event_data["type"] == "report":
                report = event_data["content"]
            elif event_data["type"] != "done":
                logs.append({
                    "type": event_data["type"],
                    "text": event_data["content"]
                })
        except:
            pass

    return {"logs": logs, "report": report}

@app.get("/api/episodes")
def get_episodic_memory(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Fetches SQLite episodic runs database."""
    ep_mem = EpisodicMemory()
    return ep_mem.get_episodes(limit=25)

@app.get("/api/vectors")
def get_vector_vault(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Fetches stored vector snippets."""
    v_store = ChromaVectorStore()
    return v_store.get_all_vectors()

@app.delete("/api/memory")
def delete_memory(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Deletes all local databases for a fresh start."""
    import os
    for file in ["data/vector_store.json", "data/episodic_memory.db"]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception as e:
                pass
    return {"status": "success", "message": "Memory deleted successfully."}

@app.delete("/api/memory/episodic/{id}")
def delete_episodic_memory(id: str, x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Deletes a single episodic memory."""
    ep_mem = EpisodicMemory()
    ep_mem.delete_episode(id)
    return {"status": "success"}

@app.delete("/api/memory/vector/{id}")
def delete_vector_memory(id: str, x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Deletes a single vector from ChromaDB."""
    v_store = ChromaVectorStore()
    v_store.delete_vector(id)
    return {"status": "success"}

@app.get("/api/charts_list")
def list_charts(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Returns a list of cached candlestick charts from the last 24 hours."""
    charts = []
    try:
        charts_dir = os.path.join(os.path.dirname(__file__), "..", "temp_charts")
        if os.path.exists(charts_dir):
            import time
            current_time = time.time()
            for filename in os.listdir(charts_dir):
                if filename.endswith(".png"):
                    filepath = os.path.join(charts_dir, filename)
                    # Check if file is less than 24 hours old
                    if (current_time - os.path.getmtime(filepath)) < 86400:
                        charts.append({
                            "filename": filename,
                            "url": f"http://localhost:7860/api/charts/{filename}",
                            "timestamp": os.path.getmtime(filepath)
                        })
            # Sort newest first
            charts.sort(key=lambda x: x["timestamp"], reverse=True)
    except Exception as e:
        pass
    return charts

@app.post("/api/upload")
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    x_llm_provider: Optional[str] = Header("gemini"),
    x_llm_api_key: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header("GLOBAL")
):
    """Parses a PDF, applies semantic chunking, and stores it in the vector DB."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        text = ""
        table_chunks = []
        for page in doc:
            page_text = ""
            try:
                page_text += page.get_text("text", sort=True) + "\n\n"
            except TypeError:
                page_text += page.get_text("text") + "\n\n"
                
            # Attempt native table extraction
            try:
                tables_lines = page.find_tables(strategy="lines")
                tables_text = page.find_tables(strategy="text")
                
                all_extracted = []
                if tables_lines:
                    for t in tables_lines: all_extracted.append(t.extract())
                if tables_text:
                    for t in tables_text: all_extracted.append(t.extract())
                
                if all_extracted:
                    for idx, extracted in enumerate(all_extracted):
                        if extracted and len(extracted) > 0:
                            # Prepend the first 300 characters of the page as a semantic title/context
                            context_header = page_text[:300].replace('\n', ' ').strip()
                            table_chunk = f"TABLE CONTEXT (Page {page.number+1}): {context_header}...\n\n"
                            table_chunk += f"--- STRUCTURED TABLE EXCAVATION (Page {page.number+1}, Extraction {idx+1}) ---\n"
                            for row in extracted:
                                clean_row = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]
                                table_chunk += "| " + " | ".join(clean_row) + " |\n"
                            table_chunk += "--------------------------------------------------\n"
                            # Add to standalone table buffer
                            table_chunks.append(table_chunk)
            except Exception as e:
                print("Table extraction error:", str(e))
            
            text += page_text
        
        # Advanced Chunking (preserving newlines and paragraph structure)
        chunk_size = 1200
        overlap = 250
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:text_len].strip())
                break
                
            # Try to find a clean break (double newline, single newline, or period)
            nearest_break = text.rfind("\n\n", start, end)
            if nearest_break == -1 or nearest_break < start + (chunk_size // 2):
                nearest_break = text.rfind("\n", start, end)
            if nearest_break == -1 or nearest_break < start + (chunk_size // 2):
                nearest_break = text.rfind(". ", start, end)
                
            if nearest_break != -1 and nearest_break > start + (chunk_size // 2):
                end = nearest_break + 1  # Include the break char
                if text[end-1:end+1] == "\n\n": end += 1 # Include second newline if double
                
            chunks.append(text[start:end].strip())
            start = end - overlap
            
        # Append all perfectly intact tables as their own dedicated chunks!
        chunks.extend(table_chunks)
            
        if not chunks:
            raise HTTPException(status_code=400, detail="No readable text found in PDF.")

        # Embed and store
        v_store = ChromaVectorStore()
        
        # We no longer clear previous uploads. Instead, we isolate them via session_id!
        # try:
        #     v_store.collection.delete(where={"source_type": "user_upload"})
        # except Exception:
        #     pass

        embeddings = LLMHelper.generate_embeddings(chunks, provider=x_llm_provider, api_key=x_llm_api_key)
        
        metadata_list = [{
            "source_type": "user_upload",
            "tier": "User Docs",
            "session_id": x_session_id,
            "ticker": "N/A",
            "source_name": file.filename,
            "timestamp": datetime.datetime.utcnow().isoformat()
        } for _ in chunks]
        
        v_store.add_documents(chunks, embeddings, metadata_list)
        
        return {"status": "success", "message": f"Document processed and embedded into {len(chunks)} chunks.", "chunks": len(chunks)}
    except Exception as e:
        error_msg = str(e)
        if "cannot open" in error_msg.lower() or "not a pdf" in error_msg.lower() or "filetype" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file. Please ensure the file is a valid PDF document.")
        elif "dimension" in error_msg.lower() or "expected" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Vector DB Dimension Mismatch: You likely switched LLM providers (e.g., from OpenAI to Gemini) which have different vector sizes. Please go to the Memory Vault and click the Trash icon to reset the database before uploading.")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {error_msg}")
