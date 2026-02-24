"""
Kenya Legal AI — RAG Retrieval Pipeline
=========================================
Combines vector similarity search with keyword matching (hybrid search),
court-hierarchy authority weighting, division-aware routing, and optional
re-ranking for high-precision Kenyan legal document retrieval.

Court authority model (Article 163(7) CoK — SC judgments bind all lower courts):
    Supreme Court        → weight 1.00
    Court of Appeal      → weight 0.85
    High Court (all divs)→ weight 0.70
    Magistrate Courts    → weight 0.40
    Unknown              → weight 0.50
"""

import logging
import re
from typing import Optional

from src.config.settings import get_settings
from src.embedding.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


# ─── Court Authority Hierarchy ────────────────────────────────────────────────
# Reflects the binding authority of each court under Article 163(7) CoK 2010.
# All scores are in [0, 1]; a higher score means the document carries more
# precedential authority and should surface above lower-court results.

COURT_HIERARCHY_SCORES: dict[str, float] = {
    # Apex court — Article 163(7): binding on all courts
    "Supreme Court": 1.00,
    "Supreme Court of Kenya": 1.00,

    # Second-highest — binding on High Court and below
    "Court of Appeal": 0.85,
    "Court of Appeal of Kenya": 0.85,

    # High Court divisions (co-equal authority)
    "High Court": 0.70,
    "High Court of Kenya": 0.70,
    "Constitutional Court": 0.70,
    "Constitutional and Human Rights Division": 0.70,
    "Commercial Court": 0.70,
    "Family Court": 0.70,

    # Specialist courts of record (equivalent to HC for their jurisdiction)
    "Employment and Labour Relations Court": 0.70,
    "ELRC": 0.70,
    "Environment and Land Court": 0.70,
    "ELC": 0.70,

    # East African / regional courts — persuasive authority in Kenya
    "East African Court of Justice": 0.65,
    "EACJ": 0.65,
    "African Court on Human and Peoples' Rights": 0.60,

    # Lower courts — persuasive, not binding
    "Magistrate Court": 0.40,
    "Magistrates Court": 0.40,
    "Chief Magistrate Court": 0.42,
    "Senior Resident Magistrate": 0.40,
    "Principal Magistrate": 0.41,

    # Non-judgment documents (statutes, treaties, etc.) — treated as authoritative
    "": 0.55,
}

_DEFAULT_HIERARCHY_SCORE = 0.50   # fallback for unknown court names

# ─── Division-Aware Routing ───────────────────────────────────────────────────
# Maps query keyword clusters → preferred court division.
# Queries that strongly match a cluster get an additional boost for results
# from the corresponding division, surfacing specialist case law first.

TOPIC_DIVISION_MAP: list[tuple[list[str], str]] = [
    # Environment & Land Court
    (
        ["land", "property", "title deed", "tenure", "elc", "nlc", "lease",
         "eviction", "trespass", "adverse possession", "compulsory acquisition",
         "land registration", "community land"],
        "Environment and Land Court",
    ),
    # Employment & Labour Relations Court
    (
        ["employment", "labour", "labor", "elrc", "dismissal", "unfair termination",
         "retrenchment", "redundancy", "collective bargaining", "trade union",
         "salary", "wages", "workplace", "employer", "employee"],
        "Employment and Labour Relations Court",
    ),
    # Constitutional / Human Rights Division
    (
        ["constitutional", "petition", "article", "fundamental rights", "bill of rights",
         "chapter 4", "enforcement", "dignity", "equality", "discrimination",
         "fair trial", "arbitrary", "detention"],
        "High Court",
    ),
    # Family Division
    (
        ["family", "divorce", "matrimonial", "custody", "guardianship",
         "maintenance", "succession", "intestate", "probate", "marriage",
         "domestic violence"],
        "High Court",
    ),
    # EAC / International
    (
        ["eac", "eacj", "east african community", "treaty", "african union", "au",
         "international law", "ratified", "human rights commission"],
        "East African Court of Justice",
    ),
]

_DIVISION_BOOST = 0.12   # score added when result matches inferred division


class RetrievalPipeline:
    """
    Hybrid retrieval pipeline for legal documents.

    Pipeline:
    1. Vector similarity search (semantic understanding)
    2. Keyword boosting (exact Kenyan legal term matching)
    3. Court hierarchy authority weighting
    4. Division-aware routing boost
    5. Sort by composite score → take top rerank_k
    """

    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()

    # ── Public API ─────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_type: Optional[str] = None,
        court: Optional[str] = None,
    ) -> list[dict]:
        """
        Retrieve relevant document chunks for a legal query.

        If no explicit `court` filter is given, the pipeline will auto-detect
        the most relevant court division from the query text and apply a
        division-aware ranking boost (not a hard filter — broad retrieval is
        preserved while specialist results surface higher).
        """
        top_k = top_k or self.settings.retrieval_top_k

        # Step 1: Vector similarity search
        results = self.embedding_service.search(
            query=query,
            top_k=top_k,
            document_type=document_type,
            court=court,
        )
        if not results:
            return []

        # Step 2: Keyword boost (exact legal term matching)
        results = self._apply_keyword_boost(query, results)

        # Step 3: Court hierarchy authority weighting
        results = self._apply_hierarchy_boost(results)

        # Step 4: Division-aware routing boost
        inferred_division = self._infer_division(query)
        if inferred_division and not court:
            results = self._apply_division_boost(results, inferred_division)

        # Step 5: Sort by final composite score
        results.sort(
            key=lambda x: x.get("adjusted_score", x["score"]),
            reverse=True,
        )

        # Step 6: Take rerank_top_k
        results = results[:self.settings.rerank_top_k]

        logger.info(
            f"Retrieved {len(results)} chunks for query: '{query[:60]}'"
            + (f" | division boost: {inferred_division}" if inferred_division else "")
        )
        return results

    def retrieve_for_context(
        self,
        query: str,
        max_context_length: int = 12000,
        **kwargs,
    ) -> str:
        """
        Retrieve and format document chunks as context for the LLM.

        Returns a formatted string where each chunk is preceded by a
        [Source N: ...] header containing court, citation, and date info.
        """
        results = self.retrieve(query, **kwargs)

        context_parts = []
        total_length = 0

        for i, result in enumerate(results, 1):
            source_info = []
            if result.get("document_title"):
                source_info.append(result["document_title"])
            if result.get("section"):
                source_info.append(result["section"])
            if result.get("citation"):
                source_info.append(result["citation"])
            if result.get("court"):
                source_info.append(result["court"])
            if result.get("date"):
                source_info.append(result["date"])

            # Surface hierarchy weight in the context header so the LLM can
            # calibrate its reliance on each source's precedential value.
            authority = result.get("hierarchy_weight", 0)
            authority_label = self._authority_label(authority)

            source_label = " | ".join(source_info) if source_info else "Unknown Source"

            chunk = (
                f"[Source {i}: {source_label} | Authority: {authority_label}]\n"
                f"{result['text']}\n"
            )

            if total_length + len(chunk) > max_context_length:
                break

            context_parts.append(chunk)
            total_length += len(chunk)

        return "\n---\n".join(context_parts)

    # ── Internal: Keyword Boost ────────────────────────────────────────────────

    def _apply_keyword_boost(
        self, query: str, results: list[dict], boost_factor: float = 0.10
    ) -> list[dict]:
        """Boost scores for results containing exact legal keyword matches."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        legal_keywords = [
            term for term in query_terms
            if any(
                marker in term
                for marker in [
                    "article", "section", "act", "cap", "court", "appeal",
                    "petition", "constitution", "schedule", "regulation",
                    "gazette", "treaty", "judgment", "v.", "vs",
                ]
            )
        ]

        for result in results:
            text_lower = result["text"].lower()
            boost = 0.0

            for keyword in legal_keywords:
                if keyword in text_lower:
                    boost += boost_factor

            # Extra boost for exact phrase presence
            if len(query_lower) > 15 and query_lower in text_lower:
                boost += boost_factor * 2

            result["adjusted_score"] = result["score"] + boost
            result["keyword_boost"] = boost

        return results

    # ── Internal: Hierarchy Boost ──────────────────────────────────────────────

    def _apply_hierarchy_boost(self, results: list[dict]) -> list[dict]:
        """
        Weight each result's score by its court's authority level.

        Formula: adjusted_score = current_adjusted_score * hierarchy_weight
        This means a Supreme Court judgment (weight 1.0) retains its full
        score, while a Magistrate Court decision (weight 0.4) is discounted.
        The effect is significant but not absolute — a very relevant magistrate
        judgment can still outrank a barely-relevant Supreme Court one.
        """
        for result in results:
            court = (result.get("court") or "").strip()

            # Exact match first, then prefix/substring match
            weight = _DEFAULT_HIERARCHY_SCORE
            if court in COURT_HIERARCHY_SCORES:
                weight = COURT_HIERARCHY_SCORES[court]
            else:
                for known_court, w in COURT_HIERARCHY_SCORES.items():
                    if known_court and (
                        known_court.lower() in court.lower()
                        or court.lower() in known_court.lower()
                    ):
                        weight = w
                        break

            current = result.get("adjusted_score", result["score"])
            result["adjusted_score"] = current * weight
            result["hierarchy_weight"] = weight

        return results

    # ── Internal: Division Routing ─────────────────────────────────────────────

    def _infer_division(self, query: str) -> Optional[str]:
        """
        Infer the most relevant court division from the query text.

        Returns the division name, or None if no strong match is found.
        """
        query_lower = query.lower()
        best_division = None
        best_count = 0

        for keywords, division in TOPIC_DIVISION_MAP:
            count = sum(1 for kw in keywords if kw in query_lower)
            if count > best_count:
                best_count = count
                best_division = division

        # Require at least 1 keyword match to avoid spurious routing
        return best_division if best_count >= 1 else None

    def _apply_division_boost(
        self, results: list[dict], division: str
    ) -> list[dict]:
        """Add a fixed boost to results from the inferred court division."""
        for result in results:
            court = (result.get("court") or "").strip()
            if division.lower() in court.lower() or court.lower() in division.lower():
                result["adjusted_score"] = (
                    result.get("adjusted_score", result["score"]) + _DIVISION_BOOST
                )
                result["division_boost"] = _DIVISION_BOOST
        return results

    # ── Internal: Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _authority_label(weight: float) -> str:
        """Convert a hierarchy weight into a human-readable authority label."""
        if weight >= 1.0:
            return "Supreme Court (binding)"
        elif weight >= 0.85:
            return "Court of Appeal (binding on HC)"
        elif weight >= 0.70:
            return "High Court / Specialist Court"
        elif weight >= 0.60:
            return "Regional Court (persuasive)"
        elif weight >= 0.40:
            return "Magistrate Court (persuasive)"
        else:
            return "Unknown"
