"""
Kenya Legal AI — Disclaimer Engine
=====================================
Detects when a user query crosses from legal research into specific legal advice
and returns an appropriate disclaimer level.

Under the Advocates Act (Cap. 16), only enrolled advocates may give legal advice
for a fee. This engine flags queries that sound like requests for specific advice
rather than general legal research.

Disclaimer levels:
  RESEARCH       — Standard footer disclaimer only (general queries)
  BORDERLINE     — Inline amber notice (query is getting specific)
  SPECIFIC_ADVICE — Prominent red notice + advocate referral text

Usage:
    from src.tools.disclaimer_engine import assess_disclaimer
    level, text = assess_disclaimer("Should I sign this tenancy agreement?")
"""

from __future__ import annotations

import re
from enum import Enum


class DisclaimerLevel(str, Enum):
    RESEARCH = "research"
    BORDERLINE = "borderline"
    SPECIFIC_ADVICE = "specific_advice"


# ─── Pattern Banks ────────────────────────────────────────────────────────────

# Strong signals — very likely requesting specific personal legal advice
_SPECIFIC_ADVICE_PATTERNS: list[str] = [
    r"\bshould i\b",
    r"\bwill i win\b",
    r"\bdo i have a case\b",
    r"\bam i liable\b",
    r"\bam i guilty\b",
    r"\bwhat should i do\b",
    r"\bcan i be arrested\b",
    r"\bcan they (fire|dismiss|sue|arrest|charge) me\b",
    r"\bis my (contract|lease|agreement|will|deed|marriage) valid\b",
    r"\bshould (my client|he|she|they)\b",
    r"\bwill (the court|judge|magistrate) (rule|decide|find)\b",
    r"\bdo i need (a lawyer|an advocate|legal representation)\b",
    r"\bhow much (compensation|damages) will i get\b",
    r"\bwhat are my chances\b",
    r"\bcan i (win|succeed|appeal|sue)\b",
    r"\bis it worth (suing|appealing|filing)\b",
    r"\bshould i plead (guilty|not guilty)\b",
    r"\bwhat (sentence|penalty|fine) will i face\b",
    r"\badvise me on\b",
    r"\bgive me legal advice\b",
]

# Weaker signals — borderline; general but with personal framing
_BORDERLINE_PATTERNS: list[str] = [
    r"\bmy (employer|landlord|tenant|bank|wife|husband|partner|neighbour)\b",
    r"\bi (was|am being|have been) (fired|arrested|evicted|sued|charged)\b",
    r"\bmy (case|matter|dispute|situation|problem)\b",
    r"\bwhat (can|do) i do\b",
    r"\bmy rights\b",
    r"\bi want to (sue|claim|appeal|petition|file)\b",
    r"\bi (signed|entered into|agreed to)\b",
    r"\bthey are (threatening|refusing|demanding)\b",
    r"\bare they allowed to\b",
    r"\bcan my (employer|landlord|bank)\b",
]

# ─── Recommendation Text ──────────────────────────────────────────────────────

_SPECIFIC_ADVICE_TEXT = (
    "⚠️ **Legal Advice Notice**\n\n"
    "Your question appears to be seeking specific legal advice about your "
    "personal situation. Kenya Legal AI is a **research tool only** — "
    "it cannot and does not give legal advice, and any information provided "
    "should **not** be relied on as legal advice.\n\n"
    "Under the **Advocates Act (Cap. 16)**, only a duly enrolled advocate "
    "may give legal advice for a fee. For your specific situation, please "
    "consult a qualified Kenyan advocate. If cost is a barrier:\n"
    "- **Law Society of Kenya (LSK)** pro bono referral: +254 20 3874 481\n"
    "- **Kituo Cha Sheria** (free legal aid): +254 722 314 508\n"
    "- **FIDA Kenya** (women's rights): +254 20 2721784\n"
    "- **NCAJ Legal Aid Fund** — apply through any High Court registry"
)

_BORDERLINE_TEXT = (
    "ℹ️ **Research Context Notice**\n\n"
    "Your question has a personal dimension. The analysis below is based on "
    "general Kenyan law and is provided for **research purposes only**. "
    "It does not constitute legal advice for your specific situation. "
    "For advice on your particular circumstances, consult a qualified "
    "Kenyan advocate."
)

_RESEARCH_TEXT = (
    "This information is for legal research purposes only and does not "
    "constitute legal advice. Consult a qualified Kenyan advocate for "
    "professional legal guidance."
)


# ─── Public API ───────────────────────────────────────────────────────────────

def assess_disclaimer(query: str) -> tuple[DisclaimerLevel, str]:
    """
    Analyse a query and return the appropriate disclaimer level and text.

    Args:
        query: The user's natural-language legal query.

    Returns:
        Tuple of (DisclaimerLevel, disclaimer_text)
    """
    q = query.lower().strip()

    # Check for strong advice-seeking signals first
    for pattern in _SPECIFIC_ADVICE_PATTERNS:
        if re.search(pattern, q):
            return DisclaimerLevel.SPECIFIC_ADVICE, _SPECIFIC_ADVICE_TEXT

    # Check for borderline signals
    for pattern in _BORDERLINE_PATTERNS:
        if re.search(pattern, q):
            return DisclaimerLevel.BORDERLINE, _BORDERLINE_TEXT

    # Default: standard research disclaimer
    return DisclaimerLevel.RESEARCH, _RESEARCH_TEXT
