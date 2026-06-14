import hashlib
import sqlite3
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import DB_PATH

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exempt paths
        if request.url.path in ["/", "/api/health", "/docs", "/openapi.json"] or request.url.path.startswith("/api/charts/"):
            return await call_next(request)

        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(status_code=401, content={"detail": "Missing X-API-Key header"})

        # Hash the key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Check against SQLite
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Ensure table exists
            c.execute('''CREATE TABLE IF NOT EXISTS api_keys
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, key_hash TEXT UNIQUE, active INTEGER DEFAULT 1)''')
            
            # Dev auto-provision: insert a default test_key hash if DB is empty
            c.execute("SELECT COUNT(*) FROM api_keys")
            if c.fetchone()[0] == 0:
                dev_hash = hashlib.sha256(b'test_key').hexdigest()
                c.execute("INSERT INTO api_keys (key_hash) VALUES (?)", (dev_hash,))
                conn.commit()

            c.execute("SELECT active FROM api_keys WHERE key_hash=?", (key_hash,))
            row = c.fetchone()
            conn.close()

            if not row or row[0] == 0:
                return JSONResponse(status_code=401, content={"detail": "Invalid or revoked API Key"})

        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"Auth DB error: {str(e)}"})

        return await call_next(request)
