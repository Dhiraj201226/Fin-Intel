# 📈 Fin-Intel: AI-Powered Financial Agent & Stock Advisor

Fin-Intel is a full-stack, intelligent financial agent designed to analyze stock markets, research corporate reports, and assist with financial planning. By combining real-time equity data, dynamic web scraping, semantic vector search, and advanced LLMs, Fin-Intel delivers high-fidelity, context-aware financial intelligence.

---

## ⚡ Core Features

* 💼 **Global Equity Intelligence:** Multi-market equity support (US Stocks & Indian Equities mapped to `.NS` via Yahoo Finance) powered by a robust financial computation engine.
* 🤖 **Flexible LLM & AI Routing:** Use cloud-hosted models (**Google Gemini**, **OpenAI**, **Groq**) or run a **100% private, local AI pipeline** on your own hardware via **Ollama**.
* 🧠 **Retentive Long-Term Memory:** Utilizes **ChromaDB** as a vector store to maintain semantic memory of user interactions, custom financial facts, and document indexes.
* 🔍 **Real-Time Web Integration:** Uses **Tavily Search** to scour the web for up-to-date market sentiments, earnings call updates, and stock trends.
* 📄 **Financial Document Parsing:** Ingest and index PDF reports (annual reports, earnings statements) using high-speed extraction libraries (`PyMuPDF` and `PyPDF2`).
* 🎨 **Premium Glassmorphic UI:** A beautiful, responsive frontend built with React, Vite, and Tailwind CSS. Features dynamic dashboards, report previews, and real-time Server-Sent Events (SSE) conversation streaming.

---

## 🛠️ Technology Stack

### Backend
* **API Framework:** FastAPI (with Pydantic validation)
* **Server:** Uvicorn (ASGI)
* **Databases:** ChromaDB (Vector Search / RAG) & SQLite (Episodic Memory)
* **Data Pipelines:** Pandas & `yfinance` (Yahoo Finance Client)
* **Document Processing:** PyMuPDF (Fitz) & PyPDF2
* **Web Scraping/Search:** Tavily Search SDK
* **AI Clients:** Google Generative AI (Gemini SDK) & OpenAI Client

### Frontend
* **UI Library:** React (v19)
* **Build Tool:** Vite
* **Styling:** Tailwind CSS (configured with PostCSS and Autoprefixer)
* **Icons:** Lucide React

---

## 📂 Project Structure

```text
Fin-Intel/
├── backend/
│   ├── app/
│   │   ├── tools/
│   │   │   ├── financial_engine.py  # Computes financial ratios and indicators
│   │   │   ├── reporting.py         # Formats markdown reports
│   │   │   ├── research.py          # Executes web searches
│   │   │   └── yfinance_client.py   # Extracts yfinance balance sheets/cashflows
│   │   ├── agent.py                 # Multi-tool agent execution loop
│   │   ├── config.py                # App settings and env configurations
│   │   ├── memory_store.py          # SQLite & ChromaDB interface logic
│   │   ├── llm_helper.py            # AI router (Gemini, OpenAI, Ollama, Groq)
│   │   └── main.py                  # FastAPI server endpoints
│   ├── requirements.txt             # Backend Python dependencies
│   └── tests/                       # Unit tests for core calculators
└── frontend/
    ├── src/
    │   ├── components/              # Chat, Dashboard, Memory, Settings UI
    │   ├── App.jsx                  # Main application container
    │   ├── index.css                # Tailwind base styles
    │   └── mockData.js              # Sandbox dashboard fallbacks
    ├── package.json                 # Frontend dependencies
    └── vite.config.js               # Bundler settings
```

---

## 🚀 Local Installation & Setup

### Prerequisites
* **Python 3.10+**
* **Node.js 18+ & npm**
* **Git**

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Dhiraj201226/Fin-Intel.git
cd Fin-Intel
```

---

### Step 2: Configure Backend Environment Variables
Create a `.env` file inside the `backend/` directory:

```bash
# Navigate to backend folder
cd backend
touch .env
```

Add the following keys depending on which AI provider you wish to use:

```env
# Google Gemini (Default)
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI (Optional)
OPENAI_API_KEY=your_openai_api_key_here

# Groq Cloud (Optional)
GROQ_API_KEY=your_groq_api_key_here

# Tavily Search API (For Live Web Intelligence)
TAVILY_API_KEY=your_tavily_search_key_here
```

> [!NOTE]
> **Demo Mode:** If you do not supply any API keys, Fin-Intel will fall back to a local **Demo/Sandbox Mode** that uses simulated data and deterministic hash-based embeddings so you can try out the UI without paying for APIs.

---

### Step 3: Run the Backend Server

1. **Create and Activate a Virtual Environment:**
   ```bash
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend documentation will be live at: `http://localhost:8000/docs`*

---

### Step 4: Run the Frontend Server

1. **Navigate to the frontend folder and install dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```

2. **Start the Vite development server:**
   ```bash
   npm run dev
   ```
   *Open your browser and navigate to the address shown in the terminal (typically `http://localhost:5173`).*

---

## 🦙 Running a Local Private AI Pipeline (Ollama)

To run Fin-Intel without exposing financial data to external APIs, you can use **Ollama** locally.

1. **Download and Install Ollama** from [ollama.com](https://ollama.com).
2. **Pull the required models:**
   Open your terminal/command prompt and run:
   ```bash
   # Pull Llama 3 for text reasoning
   ollama pull llama3

   # Pull Nomic Embed Text for ChromaDB vector embeddings
   ollama pull nomic-embed-text
   ```
3. **Configure Settings:**
   * Keep your Ollama server running locally (by default, it hosts at `http://localhost:11434`).
   * In the **Fin-Intel Settings Drawer** (on the frontend interface), switch your model provider option to **Ollama**.
   * The backend will automatically route text generation and vector embedding queries to your local Ollama models.

---

## 🧪 Running Tests
You can verify the mathematical calculations and ratio calculations in the Financial Engine using `pytest`:
```bash
cd backend
pytest
```
