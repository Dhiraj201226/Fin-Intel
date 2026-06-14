import os
import sqlite3
import json
import chromadb
from datetime import datetime
from app.config import DB_PATH, DATA_DIR

class EpisodicMemory:
    """Manages SQLite Episodic memory for storing research session logs and agent strategies."""
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                query TEXT,
                status TEXT,
                tools_used TEXT,
                failures TEXT,
                recovery TEXT,
                strategy TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_episode(self, episode_id, query, status, tools_used, failures, recovery, strategy):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT OR REPLACE INTO episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (episode_id, timestamp, query, status, json.dumps(tools_used), failures, recovery, strategy)
        )
        conn.commit()
        conn.close()

    def get_episodes(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        episodes = []
        for row in rows:
            ep = dict(row)
            try:
                ep['tools_used'] = json.loads(ep['tools_used'])
            except:
                ep['tools_used'] = []
            episodes.append(ep)
        return episodes

    def delete_episode(self, episode_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM episodes WHERE id=?", (episode_id,))
        conn.commit()
        conn.close()


class ChromaVectorStore:
    """Persistent Vector Database using ChromaDB."""
    def __init__(self):
        self.chroma_path = os.path.join(DATA_DIR, "chroma")
        os.makedirs(self.chroma_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.client.get_or_create_collection(name="documents")

    def add_documents(self, chunks, embeddings, metadata_list):
        """Adds text chunks with embeddings and metadata to the database."""
        timestamp_base = str(datetime.utcnow().timestamp())
        ids = [f"vec_{timestamp_base}_{i}" for i in range(len(chunks))]
        
        # Ensure metadata values are strings, ints, floats, or bools as required by ChromaDB
        clean_metadata = []
        for meta in metadata_list:
            clean_meta = {
                "source_type": str(meta.get("source_type", "unknown")),
                "tier": str(meta.get("tier", "Unknown")),
                "ticker": str(meta.get("ticker", "GENERIC")),
                "source_name": str(meta.get("source_name", "Unknown")),
                "url": str(meta.get("url", "")),
                "timestamp": str(meta.get("timestamp", datetime.utcnow().isoformat()))
            }
            if "query" in meta:
                clean_meta["query"] = str(meta["query"])
            clean_metadata.append(clean_meta)

        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            self.collection.add(
                documents=chunks[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                metadatas=clean_metadata[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )

    def similarity_search(self, query_vector, k=4, filter_ticker=None, custom_where=None):
        """Performs cosine similarity search against stored vectors."""
        if not query_vector:
            return []

        where_clause = custom_where if custom_where else {}
        if filter_ticker:
            where_clause["ticker"] = filter_ticker.upper()
            
        if not where_clause:
            where_clause = None
            
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where_clause
        )
        
        formatted = []
        if results and results.get('documents') and results['documents'][0]:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            for d, m in zip(docs, metas):
                item = {
                    "snippet": d,
                    "ticker": m.get("ticker", "GENERIC"),
                    "tier": m.get("tier", "Unknown"),
                    "source_name": m.get("source_name", "Unknown"),
                    "url": m.get("url", "")
                }
                formatted.append(item)
        return formatted

    def get_all_vectors(self):
        """Formats vectors for display in the dashboard."""
        results = self.collection.get()
        display_docs = []
        if results and results.get('documents'):
            for id_, doc, meta in zip(results['ids'], results['documents'], results['metadatas']):
                display_docs.append({
                    "id": id_,
                    "ticker": meta.get("ticker", "GENERIC"),
                    "tier": meta.get("tier", "Unknown"),
                    "snippet": doc,
                    "vector": "[Embedded by ChromaDB]"
                })
        return display_docs

    def delete_vector(self, vector_id):
        self.collection.delete(ids=[vector_id])
