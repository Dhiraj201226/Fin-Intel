import os
from dotenv import load_dotenv

# Load local .env if available
load_dotenv()

# App directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
CACHE_DIR = os.path.join(DATA_DIR, "sec_cache")

# Create directories if they do not exist
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Default Model configurations (fallbacks if user does not supply keys in headers)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# SQLite DB Path
DB_PATH = os.path.join(DATA_DIR, "episodic_memory.db")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "chroma_vectors")

# Search constraints
SEC_USER_AGENT = "ARA-1 VJTI Project ddshirse_b24@ce.vjti.ac.in"
MAX_STEPS = 8
TEMPERATURE = 0.3
