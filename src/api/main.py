"""
Kenya Legal AI — FastAPI Application
======================================
REST API for the Kenya Legal AI system providing endpoints for
legal research chat, case search, document analysis, and system status.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.generation.legal_generator import LegalGenerator
from src.embedding.embedding_service import EmbeddingService
from src.tools.disclaimer_engine import assess_disclaimer
from src.tools.limitation_checker import check_limitation

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Kenya Legal AI",
    description=(
        "AI-powered legal research assistant trained on Kenya's Constitution, "
        "Acts of Parliament, court judgments, and the full legal framework. "
        "Provides citation-backed legal analysis using RAG."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for the legal chat endpoint."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Legal question or research query",
        examples=["What does Article 27 of the Constitution say about equality?"],
    )
    mode: str = Field(
        default="research",
        description=(
            "Response mode: research, case_analysis, drafting, deep_research, "
            "petition_drafting, judicial_review, devolution, cross_reference, "
            "plain_language, swahili"
        ),
        pattern="^(research|case_analysis|drafting|deep_research|petition_drafting|judicial_review|devolution|cross_reference|plain_language|swahili)$",
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Filter by document type: constitution, act, judgment, legal_notice",
    )
    court: Optional[str] = Field(
        default=None,
        description="Filter by court: Supreme Court, Court of Appeal, High Court",
    )
    history: list[dict] = Field(
        default=[],
        description=(
            "Prior conversation turns in [{role, content}] format. "
            "Enables multi-turn follow-up questions and contextual awareness."
        ),
    )


class SourceInfo(BaseModel):
    """Information about a source document."""
    title: str = ""
    section: str = ""
    citation: str = ""
    court: str = ""
    date: str = ""
    relevance_score: float = 0.0


class ChatResponse(BaseModel):
    """Response from the legal chat endpoint."""
    response: str
    sources: list[SourceInfo] = []
    mode: str = "research"
    model: str = ""
    rag_used: bool = False
    tokens_used: Optional[dict] = None
    follow_up_questions: list[str] = Field(
        default=[],
        description="Suggested follow-up questions to deepen the research",
    )
    disclaimer: str = ""
    disclaimer_level: str = "research"
    grounding_notice: Optional[str] = None


class SearchRequest(BaseModel):
    """Request body for the document search endpoint."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Search query for legal documents",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of results to return",
    )
    document_type: Optional[str] = None
    court: Optional[str] = None


class SearchResult(BaseModel):
    """A single search result."""
    text: str
    document_title: str = ""
    document_type: str = ""
    section: str = ""
    court: str = ""
    date: str = ""
    citation: str = ""
    score: float = 0.0


class SearchResponse(BaseModel):
    """Response from the search endpoint."""
    results: list[SearchResult]
    total: int
    query: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    app_name: str
    version: str
    vector_db: Optional[dict] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", response_model=dict)
async def root():
    """API root with welcome message."""
    return {
        "message": "Kenya Legal AI API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /api/v1/chat",
            "search": "POST /api/v1/search",
            "health": "GET /api/v1/health",
        },
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon — prevents 404 in browser console."""
    favicon_path = FRONTEND_DIR / "favicon.ico" if FRONTEND_DIR.exists() else None
    if favicon_path and favicon_path.exists():
        return FileResponse(favicon_path)
    from starlette.responses import Response
    return Response(status_code=204)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Check API and vector database health."""
    try:
        embedding_service = EmbeddingService()
        vector_info = embedding_service.get_collection_info()
    except Exception as e:
        vector_info = {"error": str(e)}

    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version="0.1.0",
        vector_db=vector_info,
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def legal_chat(request: ChatRequest):
    """
    Ask a legal question and get a citation-backed response.

    The AI retrieves relevant legal documents (constitution, acts, judgments)
    and generates a comprehensive answer with source citations.
    Falls back to direct LLM mode if vector DB is not available.
    """
    # Check if API key is configured for the selected provider
    if settings.llm_provider == "groq":
        api_key = (settings.groq_api_key or "").strip()
        key_missing = not api_key or api_key.startswith("your-")
        key_name = "GROQ_API_KEY"
        get_key_url = "Get a free key at https://console.groq.com/keys"
    elif settings.llm_provider == "google":
        api_key = (settings.google_api_key or "").strip()
        key_missing = not api_key or api_key.startswith("your-")
        key_name = "GOOGLE_API_KEY"
        get_key_url = "Get a free key at https://aistudio.google.com/apikey"
    else:
        api_key = (settings.openai_api_key or "").strip()
        key_missing = not api_key or api_key.startswith("sk-your")
        key_name = "OPENAI_API_KEY"
        get_key_url = "Get a key at https://platform.openai.com/api-keys"

    if key_missing:
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"{key_name} not configured",
                "message": (
                    f"Please add your API key to the .env file:\n"
                    f"{key_name}=your-key-here\n\n"
                    f"{get_key_url}\n"
                    f"Then restart the server."
                ),
            },
        )

    try:
        # Assess query for disclaimer level
        discl_level, discl_text = assess_disclaimer(request.query)

        generator = LegalGenerator()
        result = generator.generate(
            query=request.query,
            mode=request.mode,
            document_type=request.document_type,
            court=request.court,
            history=request.history,
        )

        response_text = result["response"]
        rag_used = result.get("rag_used", False)
        
        # Add grounding notice if RAG fallback occurred
        grounding_notice = None
        if not rag_used and request.mode != "swahili":
            grounding_notice = (
                "⚠️ Grounding notice: No relevant documents found in the database. "
                "This response is based on general knowledge and may not reflect "
                "the current Kenyan statutory or judicial position."
            )

        return ChatResponse(
            response=response_text,
            sources=[SourceInfo(**s) for s in result.get("sources", [])],
            mode=result.get("mode", "research"),
            model=result.get("model", ""),
            rag_used=rag_used,
            tokens_used=result.get("tokens_used"),
            follow_up_questions=result.get("follow_up_questions", []),
            disclaimer=discl_text,
            disclaimer_level=discl_level,
            grounding_notice=grounding_notice,
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "generation_failed",
                "message": str(e),
            },
        )


@app.post("/api/v1/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search the legal knowledge base for relevant documents.

    Returns matching document chunks with relevance scores and metadata.
    """
    try:
        embedding_service = EmbeddingService()
        results = embedding_service.search(
            query=request.query,
            top_k=request.top_k,
            document_type=request.document_type,
            court=request.court,
        )

        return SearchResponse(
            results=[SearchResult(**r) for r in results],
            total=len(results),
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching.",
        )


@app.get("/api/v1/constitution")
async def search_constitution(
    q: str = Query(
        ...,
        min_length=3,
        description="Search query for the Constitution of Kenya",
    ),
    top_k: int = Query(default=5, ge=1, le=20),
):
    """
    Search specifically within the Constitution of Kenya 2010.

    Convenience endpoint that filters results to constitutional provisions only.
    """
    try:
        embedding_service = EmbeddingService()
        results = embedding_service.search(
            query=q,
            top_k=top_k,
            document_type="constitution",
        )
        return {
            "query": q,
            "results": results,
            "total": len(results),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tools/limitation")
async def get_limitation_period(
    cause: str = Query(..., min_length=2, description="Cause of action / legal claim type")
):
    """
    Look up Kenyan limitation periods for a specific cause of action.
    """
    try:
        return check_limitation(cause)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Frontend Static Files ────────────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    @app.get("/app")
    async def serve_frontend():
        """Serve the frontend application."""
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/app/{path:path}")
    async def serve_frontend_files(path: str):
        """Serve frontend static files."""
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")


# ─── Logging Setup ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
