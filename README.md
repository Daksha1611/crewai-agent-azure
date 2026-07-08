# AAFA — AI Agent Financial Analyst

AAFA is a multi-agent financial analysis system built with **CrewAI**, **FastAPI**, **Streamlit**, and **Azure**. Two specialized AI agents — a Quantitative Analyst and an Investment Strategist — research a stock ticker together, analyze hard financial metrics, factor in current news and market sentiment, and produce a structured Buy/Sell/Hold investment report.

## How It Works

Given a stock ticker (e.g. `TSLA`), the system runs two agents in sequence:

1. **Senior Quantitative Analyst** — pulls P/E ratio, EPS, Beta, Market Cap, and 52-week range via `yfinance`, and compares the stock's 1-year performance against another ticker (e.g. the S&P 500 via `SPY`). Flags numerical red flags such as negative EPS or extreme valuations.
2. **Chief Investment Strategist** — receives the Quant's findings as context, searches recent news and market sentiment using Firecrawl, and synthesizes both into a final Buy/Sell/Hold recommendation with reasoning.

The final report is generated in Markdown, uploaded to **Azure Blob Storage**, and logged to **Azure PostgreSQL** — all triggered through a single FastAPI endpoint, with a Streamlit UI on top for interactive use.

```
Streamlit UI  ──▶  POST /api/v1/analyze  { "ticker": "TSLA" }
                            │
                            ▼
              ┌──────────────────────┐        ┌───────────────────────────┐
              │ Quantitative Analyst │──────▶ │  Investment Strategist      │
              │ (yfinance tools)     │ context │  (Firecrawl news search)   │
              └──────────────────────┘        └───────────────────────────┘
                                                       │
                                                       ▼
                                        Markdown report → Azure Blob Storage
                                                       │
                                                       ▼
                                             Record saved → Azure PostgreSQL
                                                       │
                                                       ▼
                                             JSON response → Streamlit UI
```

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | [CrewAI](https://www.crewai.com/) (`Process.sequential`) |
| LLM Provider | OpenRouter (via LiteLLM) |
| API Framework | FastAPI |
| Frontend | Streamlit |
| Financial Data | yfinance |
| Web Search / Scraping | Firecrawl |
| Config & Validation | Pydantic / pydantic-settings |
| Cloud Storage | Azure Blob Storage |
| Database | Azure PostgreSQL (via SQLAlchemy) |
| Observability | LangSmith tracing (optional) |
| Package Management | uv |

## Project Structure

```
crewai-agent-azure/
├── src/
│   ├── agents/
│   │   ├── agents.py        # Agent definitions (Quant + Strategist)
│   │   ├── crew.py          # Crew assembly and async execution
│   │   ├── tasks.py         # Task definitions (prompt engineering layer)
│   │   └── tools/
│   │       ├── financial.py # FundamentalAnalysisTool, CompareStocksTool
│   │       └── scraper.py   # SentimentSearchTool (Firecrawl)
│   ├── api/
│   │   ├── main.py          # FastAPI app entrypoint
│   │   ├── routes.py        # /analyze endpoint (Controller)
│   │   └── models.py        # Request/response schemas
│   └── shared/
│       ├── config.py        # Centralized settings (env-based)
│       ├── storage.py       # Azure Blob Storage service
│       └── database.py      # Azure PostgreSQL service (SQLAlchemy)
├── frontend/
│   └── app.py                # Streamlit UI
├── main.py                   # Standalone CLI runner (no API/frontend needed)
├── debug_run.py               # Quick script for debugging the crew directly
├── pyproject.toml
└── Dockerfile
```

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependency management
- An [OpenRouter](https://openrouter.ai) API key
- A [Firecrawl](https://firecrawl.dev) API key
- Azure Blob Storage and Azure PostgreSQL instances (required for cloud persistence)

### Installation

```bash
git clone https://github.com/Daksha1611/crewai-agent-azure.git
cd crewai-agent-azure
uv sync
```

### Configuration

Create a `.env` file in the project root:

```env
# LLM Provider (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL_NAME=openrouter/google/gemini-2.5-flash

# Tools
FIRECRAWL_API_KEY=your_firecrawl_key_here

# Azure
AZURE_BLOB_CONNECTION_STRING=your_blob_connection_string
AZURE_POSTGRES_CONNECTION_STRING=postgresql://user:password@host:5432/dbname?sslmode=require

# Observability (optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
```

### Running the Full App (API + UI)

You'll need two terminals running at once:

**Terminal 1 — start the backend API:**
```bash
uv run uvicorn src.api.main:app --reload
```
Runs at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

**Terminal 2 — start the Streamlit frontend:**
```bash
uv run streamlit run frontend/app.py
```
Opens at `http://localhost:8501`. Enter a ticker (e.g. `NVDA`) and click **Run Full Analysis**.

### Running via CLI (no API/frontend needed)

For a quick standalone run that still uploads to Azure:
```bash
uv run python main.py
```

### Example API Request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA"}'
```

### Example Response

```json
{
  "status": "success",
  "ticker": "TSLA",
  "report_content": "## Investment Report: TSLA\n\n**Verdict: HOLD**\n...",
  "report_url": "https://<storage-account>.blob.core.windows.net/reports/investment_report_TSLA.md",
  "message": "Analysis complete and saved to cloud."
}
```

## Known Issues / Debugging Notes

While migrating LLM providers (OpenAI → Groq → OpenRouter), a few CrewAI/LiteLLM internals surfaced worth documenting:

- **`cache_breakpoint` unsupported by Groq** — CrewAI attaches a prompt-caching marker to messages that isn't recognized by every provider, causing `BadRequestError` on Groq specifically.
- **`'bool' object has no attribute 'get'`** — a CrewAI/LiteLLM internal debug-logging bug triggered when the `cache` parameter is passed as a boolean instead of a dict.
- **CrewAI memory requires an OpenAI-format embedder by default** — even when the main LLM is switched to a different provider, `Agent(memory=True)` still defaults to OpenAI's embedding model unless explicitly reconfigured. Currently disabled (`memory=False`) on both agents and at the `Crew` level.

## Roadmap

- [ ] Configurable agent memory with a non-OpenAI embedder
- [ ] Additional agents (e.g. Risk Analyst, Technical Analyst)
- [ ] Dockerized full-stack deployment (API + Streamlit + Azure)
- [ ] Persist report history view in the Streamlit UI (pulled from Azure PostgreSQL)

