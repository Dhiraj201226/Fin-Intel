# 📈 Fin-Intel: AI-Powered Financial Agent & Stock Advisor

Fin-Intel is a full-stack, intelligent financial agent designed to analyze stock markets, research corporate reports, and assist with financial planning. By combining real-time equity data, custom algorithmic scoring, semantic vector search, and advanced LLMs, Fin-Intel delivers high-fidelity, context-aware financial intelligence.

---

## ⚡ Core Features

* 💼 **Global Equity Intelligence:** Multi-market equity support (US Stocks & Indian Equities mapped to `.NS` via Yahoo Finance) powered by a robust financial computation engine.
* 📊 **Weighted Algorithmic Scoring:** Computes Growth Probability, Profitability, and Financial Health scores directly from raw fundamental data to calculate a final Confidence Score.
* 🤖 **Flexible LLM & AI Routing:** Use cloud-hosted models (**Google Gemini**, **OpenAI**, **Groq**) or run a **100% private, local AI pipeline** on your own hardware via **Ollama**.
* 🧠 **Retentive Long-Term Memory:** Utilizes **ChromaDB** as a vector store to maintain semantic memory of user interactions, custom financial facts, and document indexes.
* 📄 **Financial Document Parsing:** Ingest and index PDF reports (annual reports, earnings statements) using high-speed extraction libraries (`PyMuPDF` and `PyPDF2`).
* 🎨 **Premium Glassmorphic UI:** A beautiful, responsive frontend built with React, Vite, and Tailwind CSS. Features dynamic dashboards, report previews, and real-time Server-Sent Events (SSE) conversation streaming.

## 🧠 Dual-Intent ReAct Architecture

Fin-Intel is built on a custom Reasoning and Acting (ReAct) loop that autonomously routes user queries into one of two specialized pipelines:

### 1. Live Market Recommendation Branch
When a user asks about a specific stock (e.g., *"Should I buy AAPL?"*), the agent routes the request to the live market pipeline.
*   **Data Extraction:** Automatically fetches live balance sheets, cash flows, and income statements via the Yahoo Finance API.
*   **Deterministic Math Engine:** Instead of letting the LLM hallucinate an investment thesis, the agent passes the raw data through a strict mathematical engine to calculate precise Growth, Profitability, and Health scores.
*   **Final Output:** Generates a mathematically backed buy/hold/sell recommendation.

### 2. Document Analysis Branch (RAG)
When a user asks a contextual question about a specific document (e.g., *"What is the export revenue in the uploaded report?"*), the agent routes the request to the document analysis pipeline.
*   **Vectorization:** Uploaded PDFs (like 200-page Annual Reports) are parsed via `PyMuPDF`, broken into semantic chunks (with special handling for complex financial tables), and embedded into a local **ChromaDB** vector store.
*   **Targeted Retrieval:** The agent performs a similarity search to hunt down the exact paragraphs and tables required to answer the query.
*   **Final Output:** The LLM synthesizes the retrieved chunks into a conversational, highly accurate summary, completely eliminating manual document hunting.

---

## 📊 Financial Scoring & Decision Model

Fin-Intel uses a weighted, deterministic model to compute a final **Confidence Score** (ranging from **0 to 100**) using fundamental data from balance sheets, income statements, and cash flows.

### Core Categories & Base Weights
The engine divides evaluation into three primary financial vectors:
1. **Growth Score (35% Weight):** Focuses on Year-over-Year (YoY) metric expansions.
2. **Profitability Score (35% Weight):** Evaluates profit margins and capital yields.
3. **Health Score (30% Weight):** Analyzes leverage, solvency, and liquidity levels.

> [!NOTE]
> **Dynamic Weight Normalization:** If specific financial statements are missing or metrics are unavailable for a particular equity, the final score dynamically normalizes by dividing by the sum of the weights of the valid, computed categories.

---

### Sub-Category Formulas & Metrics

#### 1. Growth Score (35% of Final Score)
Derived from three YoY growth trends calculated from the latest 3 years of financial data:
* **Revenue Growth (50% Sub-weight):** Normalized on a scale of `[-5%, 30%]`.
* **Gross Profit Growth (30% Sub-weight):** Normalized on a scale of `[-5%, 30%]`.
* **Operating Income Growth (20% Sub-weight):** Normalized on a scale of `[-5%, 30%]`.

#### 2. Profitability Score (35% of Final Score)
Evaluates margins and investment returns:
* **Gross Profit Margin (15% Sub-weight):** Scaled linearly up to a `55%` margin target.
* **Operating Margin (35% Sub-weight):** Scaled linearly up to a `15%` margin target.
* **Net Margin (25% Sub-weight):** Scaled linearly up to a `10%` margin target.
* **Return on Equity / ROE (25% Sub-weight):** Scaled linearly up to a `12%` target.

#### 3. Health Score (30% of Final Score)
Assesses solvency and asset backing quality:
* **Debt-to-Equity (30% Sub-weight):** Reverses scale. `30` points if ratio is $\le 0.5$; scales down to `0` points if ratio is $\ge 1.5$.
* **Current Ratio (30% Sub-weight):** Scaled linearly up to a `1.5` liquidity ratio target.
* **Interest Coverage (25% Sub-weight):** Scaled linearly up to a `5.0` coverage ratio target.
* **Asset Coverage (15% Sub-weight):** Scaled linearly up to a `2.0` coverage target.

---

### 🎯 Confidence Score & Recommendation Ranges
The final calculated **Confidence Score** (weighted average of the three main categories) determines the stock's overall rating:

| Score Range | Recommendation | Description |
| :--- | :--- | :--- |
| **85.0 to 100.0** | `STRONG BUY` | Outstanding fundamentals, high growth, and minimal financial leverage risk. |
| **70.0 to 84.9** | `BUY` | Solid performance across categories with comfortable financial stability. |
| **55.0 to 69.9** | `HOLD` | Mixed performance; some healthy growth offset by debt or weak margins. |
| **40.0 to 54.9** | `WEAK HOLD` | Declining indicators or elevated levels of credit/liquidity risk. |
| **0.0 to 39.9** | `SELL` | Severe financial stress, negative growth rates, or extreme leverage. |

---

## 🛠️ Technology Stack

### Backend
* **API Framework:** FastAPI (with Pydantic validation)
* **Server:** Uvicorn (ASGI)
* **Databases:** ChromaDB (Vector Search / RAG) & SQLite (Episodic Memory)
* **Data Pipelines:** Pandas & `yfinance` (Yahoo Finance Client)
* **Document Processing:** PyMuPDF (Fitz) & PyPDF2
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
│   │   │   ├── research.py          # Performs local text searches
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
