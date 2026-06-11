from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import PyPDF2
from typing import Optional

from sse_starlette.sse import EventSourceResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.agent import ReActAgent
from app.memory_store import EpisodicMemory, ChromaVectorStore
from app.llm_helper import LLMHelper
from app.config import DOCUMENTS_DIR
from app.auth import APIKeyAuthMiddleware

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

class ResearchRequest(BaseModel):
    query: str
    ticker: Optional[str] = None

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
        temperature=temp
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



@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_llm_provider: Optional[str] = Header("gemini"),
    x_llm_api_key: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Handles PDF or TXT ingestion. Extracts text, chunks, embeds, and indexes to Vector DB."""
    try:
        content = ""
        filename = file.filename
        
        # Read files based on type
        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(file.file)
            first_page_text = pdf_reader.pages[0].extract_text() or ""
            content += first_page_text
            
            # SEC Authenticity Check
            first_page_upper = first_page_text.upper()
            if not any(kw in first_page_upper for kw in [
                "UNITED STATES SECURITIES AND EXCHANGE COMMISSION",
                "FORM 10-K",
                "FORM 10-Q",
                "FORM 8-K"
            ]):
                raise HTTPException(status_code=400, detail="Document rejected: Authenticity check failed. Not a valid SEC filing.")

            for page in pdf_reader.pages[1:]:
                content += page.extract_text() or ""
                
        elif filename.endswith(".txt"):
            content_bytes = await file.read()
            content = content_bytes.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are accepted")
            
        if not content.strip():
            raise HTTPException(status_code=400, detail="File is empty or could not be read")
            
        import re
        chunks = []
        metadata = []
        
        # Simple heuristic to split by SEC Items
        items = [
            ("Business Overview", r"(?i)(?:ITEM 1\.|ITEM 1 - BUSINESS)"),
            ("Risk Factors", r"(?i)(?:ITEM 1A\.|ITEM 1A - RISK FACTORS)"),
            ("MD&A", r"(?i)(?:ITEM 7\.|ITEM 7 - MANAGEMENT\'S)"),
            ("Financial Statements", r"(?i)(?:ITEM 8\.|ITEM 8 - FINANCIAL)"),
            ("Footnotes", r"(?i)(?:NOTES TO CONSOLIDATED FINANCIAL STATEMENTS)")
        ]
        
        last_idx = 0
        current_section = "General"
        
        # Find all item matches to chunk
        matches = []
        for sec_name, pattern in items:
            for match in re.finditer(pattern, content):
                matches.append((match.start(), sec_name))
                
        matches.sort(key=lambda x: x[0])
        
        if not matches:
            # Fallback to sliding window if no headers found
            chunk_size = 1000
            start = 0
            while start < len(content):
                chunks.append(content[start:start+chunk_size])
                metadata.append({"ticker": "CUSTOM", "year": "2024", "filing": "SEC Document", "section": "General", "source_name": filename})
                start += chunk_size - 150
        else:
            for i, (idx, sec_name) in enumerate(matches):
                next_idx = matches[i+1][0] if i + 1 < len(matches) else len(content)
                section_text = content[idx:next_idx].strip()
                if len(section_text) > 100:
                    # Break massive sections into smaller 2000 char chunks to avoid token limits
                    sub_chunks = [section_text[j:j+2000] for j in range(0, len(section_text), 1800)]
                    for sub in sub_chunks:
                        chunks.append(sub)
                        metadata.append({"ticker": "CUSTOM", "year": "2024", "filing": "SEC Document", "section": sec_name, "source_name": filename})
        
        v_store = ChromaVectorStore()
        embeddings = LLMHelper.generate_embeddings(
            chunks[:30], # Limit to 30 chunks to save API quotas during testing
            provider=x_llm_provider, 
            api_key=x_llm_api_key
        )
        
        v_store.add_documents(chunks[:30], embeddings, metadata[:30])
        
        # Save original file
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        with open(file_path, "wb") as f:
            file.file.seek(0)
            f.write(file.file.read())
            
        return {
            "success": True,
            "filename": filename,
            "chunks": len(chunks),
            "size": f"{len(content)/1024:.1f} KB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload processing failed: {str(e)}")
