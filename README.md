# Kenya Legal AI 🇰🇪⚖️

An AI-powered legal research assistant built on Kenya's Constitution of 2010, Acts of Parliament, court judgments across all court levels, Kenya Gazette notices, and Judiciary resources. Built with a RAG (Retrieval-Augmented Generation) architecture for deep, citation-backed legal analysis.

---

## Features

| Feature | Description |
|---|---|
| 🔍 **Research Mode** | Ask any legal question — get a structured, citation-backed answer with precedent chains and multi-angle analysis |
| 📋 **Case Analysis Mode** | 9-section structured analysis: Facts → Issues → Framework → Holding → Ratio Decidendi → Obiter → Significance → Critique → Subsequent Application |
| ✍️ **Drafting Mode** | Generate Kenyan-law-compliant legal document templates with annotated clauses and an execution checklist |
| 🎓 **Deep Research Mode** | 8-section scholarly legal memorandum: Framework → Precedent Chain → Conflicts → Comparative Law → Practical Implications → Recent Developments → Conclusion |
| 📜 **Constitution Explorer** | Navigate and search the Constitution of Kenya 2010 by chapter or free-text query |
| 🔎 **Case Law Search** | Semantic search across the indexed legal knowledge base, filterable by document type and court |
| 💬 **Multi-Turn Conversations** | Conversation memory (up to 10 prior exchanges) allows genuine follow-up questions and contextual deep-dives |
| 💡 **Follow-up Question Chips** | After every answer the agent suggests 3 clickable follow-up questions to guide further research |

---

## Data Sources

| Source | What We Ingest | API/Scraping |
|---|---|---|
| **Kenya Law** ([kenyalaw.org](https://new.kenyalaw.org)) | Court judgments (all levels), Kenya Gazette notices (2020–2026) | Web scraping |
| **Laws.Africa API** ([laws.africa](https://api.laws.africa/v3)) | Constitution of Kenya 2010 (priority), Acts of Parliament (Akoma Ntoso XML + HTML) | REST API |
| **Judiciary of Kenya** ([judiciary.go.ke](https://judiciary.go.ke)) | Practice directions, CJ speeches, administrative circulars | Web scraping |
| **AfricanLII** ([africanlii.org](https://africanlii.org/)) | Kenya case law, judgments, legislation (supplementary) | REST API |
| **Kenya Law Reports** ([kenyalawreports.or.ke](https://kenyalawreports.or.ke)) | Official law reports, EARLR, KLR, historical judgments | Web scraping |
| **KRA Tax Laws** ([kra.go.ke](https://kra.go.ke)) | Tax Acts (Income Tax, VAT, Excise), regulations, circulars | Web scraping |
| **Parliament** ([parliament.go.ke](https://parliament.go.ke)) | Bills, Order Papers, Votes & Proceedings, Committee Reports, Hansard, Standing Orders | Web scraping |
| **Law Society of Kenya** ([lsk.or.ke](https://lsk.or.ke)) | Public resources, guidelines, practice directions | Web scraping |
| **EAC** ([eac.int](https://eac.int)) | Regional treaties, protocols, East African legislation | Web scraping |

The **Constitution of Kenya 2010** is ingested first as a dedicated priority step — it is always in the knowledge base before any other source is processed.

---

## Architecture

```
Data Sources (19 sources)
  ├── Kenya Law (judgments, gazettes)
  ├── Laws.Africa API (Constitution, Acts)
  ├── Judiciary Kenya (directives, circulars)
  ├── AfricanLII (supplementary cases)
  ├── Kenya Law Reports (official reports)
  ├── KRA (tax laws, regulations)
  ├── Parliament (hansard, bills, orders, votes)
  ├── Law Society Kenya (public resources)
  └── EAC (regional legislation)
        │
        ▼
  Ingestion Layer (src/ingestion/)
  └── 20 specialized scrapers + 4 new scrapers (AfricanLII, KLR, KRA, Parliament docs)
        │
        ▼
  Processing Layer (src/processing/)
  └── Document parsing · Cleaning · Chunking (1000 chars / 200 overlap)
        │
        ▼
  Embedding Layer (src/embedding/)
  └── Google text-embedding-004 (768 dimensions)
        │
        ▼
  Vector Database
  └── Qdrant — collection: kenya_legal_docs
        │
        ▼
  Retrieval Layer (src/retrieval/)
  └── Hybrid search: vector similarity + keyword boost
      12,000 char context window · Re-ranked top-5 results
        │
        ▼
  Generation Layer (src/generation/)
  └── LegalGenerator — RAG mode (grounded) or Direct LLM (fallback)
      Conversation history threading · Follow-up question generation
      Modes: research | case_analysis | drafting | deep_research
        │
        ▼
  FastAPI Backend (src/api/)
  └── REST API — /api/v1/chat · /api/v1/search · /api/v1/constitution · /api/v1/health
        │
        ▼
  Frontend (frontend/)
  └── Vanilla HTML/CSS/JS — served at /app
```

**LLM providers** (configurable via `.env`): Groq · Google Gemini · OpenAI  
**Default**: Groq `llama-3.3-70b-versatile` (free tier)

---

## Project Structure

```
gpt/
├── src/
│   ├── config/
│   │   └── settings.py          # Pydantic-settings config (reads from .env)
│   ├── ingestion/
│   │   ├── kenya_law_scraper.py # Scrapes kenyalaw.org judgments & Gazette
│   │   ├── laws_africa_client.py# Laws.Africa API client (Constitution priority)
│   │   ├── judiciary_scraper.py # Scrapes judiciary.go.ke practice directions
│   │   ├── africanlii_scraper.py# AfricanLII API client (supplementary cases)
│   │   ├── kenya_law_reports_scraper.py # Kenya Law Reports (official reports)
│   │   ├── kra_tax_laws_scraper.py # KRA tax legislation & circulars
│   │   ├── parliament_additional_scraper.py # Parliament order papers, votes, committees
│   │   ├── hansard_scraper.py   # Parliamentary debates
│   │   ├── bills_scraper.py     # Parliamentary bills
│   │   ├── tribunals_scraper.py # Tribunal decisions (15 tribunals)
│   │   ├── treaties_scraper.py  # International treaties
│   │   ├── eac_ingestor.py      # EAC legislation
│   │   ├── lsk_scraper.py       # Law Society of Kenya documents
│   │   ├── cipit_scraper.py     # CIPIT (IP tribunal) decisions
│   │   ├── elections_scraper.py # Election petitions & results
│   │   └── mass_ingest.py       # Orchestrator: runs all sources in sequence
│   ├── processing/
│   │   └── document_processor.py# Parse, clean, chunk raw documents to JSONL
│   ├── embedding/
│   │   └── embedding_service.py # Embed chunks & index into Qdrant
│   ├── retrieval/
│   │   └── retrieval_pipeline.py# Hybrid retrieval + keyword boost + re-ranking
│   ├── generation/
│   │   └── legal_generator.py   # Prompt templates, RAG & direct modes, history
│   └── api/
│       └── main.py              # FastAPI app — all REST endpoints
├── frontend/
│   ├── index.html               # Single-page UI
│   ├── styles.css               # All styling
│   └── app.js                   # Chat, search, constitution, conversation history
├── data/
│   ├── raw/                     # Scraped HTML/PDF/JSON from sources
│   ├── processed/               # Chunked JSONL (all_documents.jsonl)
│   └── metadata/                # Document index JSONs
├── tests/
├── scripts/
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Clone & set up

```bash
git clone <your-repo-url>
cd gpt
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys. The minimum required key is one LLM provider:

| Variable | Where to get it | Required? |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) — **free** | ✅ Default |
| `GOOGLE_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — free | Optional |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Optional |
| `LAWS_AFRICA_API_KEY` | [developers.laws.africa](https://developers.laws.africa/) | For legislation |

### 3. Start Qdrant (vector database)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Ingest legal data

Run the full ingestion pipeline (Constitution first, then all other sources):

```bash
python -m src.ingestion.mass_ingest
```

Or ingest individual sources:

```bash
# Constitution of Kenya only
python -c "import asyncio; from src.ingestion.laws_africa_client import LawsAfricaClient; asyncio.run(LawsAfricaClient().download_constitution())"

# Kenya Law judgments (2024, 1 page)
python -m src.ingestion.kenya_law_scraper

# Judiciary documents
python -m src.ingestion.judiciary_scraper
```

### 5. Start the API server

```bash
venv/bin/uvicorn src.api.main:app --reload --port 8000
```

The UI is served at **http://localhost:8000/app**  
API docs (Swagger) at **http://localhost:8000/docs**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Legal Q&A with conversation history and follow-up questions |
| `POST` | `/api/v1/search` | Semantic search across the legal knowledge base |
| `GET` | `/api/v1/constitution?q=...` | Constitution-specific search |
| `GET` | `/api/v1/health` | System health — API + Qdrant + document count |

### Chat request example

```json
{
  "query": "What are the rights of an accused person under Kenyan law?",
  "mode": "deep_research",
  "document_type": "constitution",
  "court": null,
  "history": [
    {"role": "user", "content": "Tell me about Article 50."},
    {"role": "assistant", "content": "Article 50 guarantees the right to a fair hearing..."}
  ]
}
```

**Modes:** `research`, `case_analysis`, `drafting`, `deep_research`, `petition_drafting`, `judicial_review`, `devolution`, `cross_reference`, `plain_language`, `swahili`

---

## 🚀 Deployment

### PaaS (Recommended)
- **Backend (FastAPI + Qdrant):** Deploy to **Render** using the provided `render.yaml` Blueprint.
- **Frontend (Static):** Deploy to **Vercel** pointing the root to the `frontend` directory.
- See [paas_deployment_guide.md](file:///home/def/.gemini/antigravity/brain/af50911d-8f2b-4850-9c53-50d97a2e3ae8/paas_deployment_guide.md) for step-by-step instructions.

### Docker
- Run the entire stack locally or on a VPS:
  ```bash
  docker-compose up -d
  ```
- See [deployment_guide.md](file:///home/def/.gemini/antigravity/brain/af50911d-8f2b-4850-9c53-50d97a2e3ae8/deployment_guide.md) for VPS setup.


---

## Switching LLM / Embedding Provider

Edit `.env`:

```bash
# Use Groq (default, free)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_your_key

# Use Google Gemini (free tier)
LLM_PROVIDER=google
LLM_MODEL=gemini-1.5-flash
GOOGLE_API_KEY=AIza_your_key

# Embeddings — Google text-embedding-004 (default)
EMBEDDING_PROVIDER=google
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=768
```

---

## Disclaimer

Kenya Legal AI is a **legal research tool** and does **not constitute legal advice**. Always consult a qualified Kenyan advocate for professional legal guidance. This tool should be used as a starting point for research, not as a substitute for professional legal counsel.

---

## License

Proprietary - All Rights Reserved. This software is private and confidential. Unauthorized copying, distribution, or use is strictly prohibited.
