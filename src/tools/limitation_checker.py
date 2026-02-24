"""
Kenya Legal AI — Limitation Periods Checker
=============================================
Provides structured data on limitation periods under Kenyan law.

Primary authority: Limitation of Actions Act (Cap. 22), supplemented
by special statutes that override the general Act for specific causes
of action.

Usage:
    from src.tools.limitation_checker import check_limitation, LIMITATION_PERIODS
    result = check_limitation("defamation")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LimitationPeriod:
    """A single cause of action and its limitation details."""
    cause_of_action: str
    period: str                           # Friendly string, e.g. "3 years"
    period_months: int                    # Numeric months for sorting/calculation
    statute: str                          # Primary statutory authority
    section: str                          # Specific section / rule
    notes: str = ""                       # Exceptions, starting point, special rules
    special_categories: list[str] = field(default_factory=list)  # tags for matching
    keywords: list[str] = field(default_factory=list)


# ─── Limitation Periods Database ──────────────────────────────────────────────
# Ordered by period_months ascending for logical display.

LIMITATION_PERIODS: list[LimitationPeriod] = [

    # ── 30 days ───────────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Election Petitions (Presidential)",
        period="7 days",
        period_months=0,
        statute="Elections Act, No. 24 of 2011",
        section="s. 75(1)",
        notes=(
            "7 days from the date the results are declared. "
            "Filed in the Supreme Court under Article 163(3)(a) CoK."
        ),
        keywords=["election", "presidential", "petition", "results"],
    ),
    LimitationPeriod(
        cause_of_action="Election Petitions (Parliamentary & County Governor)",
        period="28 days",
        period_months=1,
        statute="Elections Act, No. 24 of 2011",
        section="s. 76",
        notes="28 days from the date the results are published in the Gazette.",
        keywords=["election", "parliamentary", "governor", "petition"],
    ),
    LimitationPeriod(
        cause_of_action="Election Petitions (County Assembly Ward)",
        period="28 days",
        period_months=1,
        statute="Elections Act, No. 24 of 2011",
        section="s. 75(2)",
        notes="Filed in the Magistrate Court within 28 days.",
        keywords=["election", "ward", "county assembly", "petition"],
    ),

    # ── 12 months ─────────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Defamation (Libel & Slander)",
        period="12 months",
        period_months=12,
        statute="Defamation Act (Cap. 36)",
        section="s. 4",
        notes=(
            "Runs from the date of publication or utterance. "
            "Significantly shorter than the general contract period."
        ),
        keywords=["defamation", "libel", "slander", "reputation", "publication"],
    ),
    LimitationPeriod(
        cause_of_action="Actions against the Government / Public Bodies",
        period="12 months (written notice) + 3 years (suit)",
        period_months=12,
        statute="Government Proceedings Act (Cap. 40)",
        section="s. 28 & 29",
        notes=(
            "Written notice of intention to sue must be given within 12 months. "
            "The actual suit must still be filed within the relevant general period "
            "(3 years for tort or contract). "
            "Note: Constitutional petitions under Article 22 are not time-barred."
        ),
        keywords=["government", "state", "public body", "county government", "authority"],
    ),

    # ── 2 years ───────────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Fatal Accidents / Dependants' Claims",
        period="3 years",
        period_months=36,
        statute="Fatal Accidents Act (Cap. 32); Law Reform Act (Cap. 26)",
        section="s. 4 (Law Reform Act)",
        notes=(
            "3 years from the death of the deceased or from the date of knowledge "
            "of the dependant. Brought by the personal representative."
        ),
        keywords=["death", "fatal accident", "dependant", "deceased", "estate"],
    ),

    # ── 3 years ───────────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Personal Injury (Tort)",
        period="3 years",
        period_months=36,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 4(2)",
        notes=(
            "Runs from the date the cause of action accrued, or the earliest date "
            "on which the claimant had knowledge of the injury, the identity of "
            "the defendant, and that the injury was attributable to the defendant's act."
        ),
        keywords=["injury", "personal injury", "negligence", "accident", "bodily harm"],
    ),
    LimitationPeriod(
        cause_of_action="Employment Disputes (Unfair Termination, Wages, etc.)",
        period="3 years",
        period_months=36,
        statute="Employment Act, No. 11 of 2007",
        section="s. 90",
        notes=(
            "3 years from the date the cause of action arose. Filed in the "
            "Employment and Labour Relations Court (ELRC). "
            "Trade dispute conciliation under the Labour Relations Act may "
            "impose shorter notice periods before litigation."
        ),
        keywords=["employment", "termination", "wages", "salary", "dismissal",
                  "redundancy", "elrc", "labour", "unfair"],
    ),
    LimitationPeriod(
        cause_of_action="Negligence (General Tort)",
        period="3 years",
        period_months=36,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 4(2)",
        notes="Runs from accrual of cause of action.",
        keywords=["negligence", "duty of care", "tort", "damage"],
    ),

    # ── 6 years ───────────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Simple Contract (Written or Oral)",
        period="6 years",
        period_months=72,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 4(1)(a)",
        notes=(
            "Runs from the date the breach of contract occurred, "
            "not from when the claimant discovers the breach."
        ),
        keywords=["contract", "agreement", "breach", "payment", "debt",
                  "service", "supply", "non-performance"],
    ),
    LimitationPeriod(
        cause_of_action="Recovery of a Debt",
        period="6 years",
        period_months=72,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 4(1)(a)",
        notes=(
            "6 years from when the debt became payable. "
            "Part payment or written acknowledgment restarts the clock."
        ),
        keywords=["debt", "loan", "money", "repayment", "recover", "creditor"],
    ),
    LimitationPeriod(
        cause_of_action="Fraud / Concealment",
        period="6 years (from discovery)",
        period_months=72,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 26",
        notes=(
            "Where the action is based on the fraud of the defendant, "
            "or any fact relevant to the plaintiff's right has been "
            "deliberately concealed, the period runs from the date "
            "the plaintiff discovered the fraud or concealment."
        ),
        keywords=["fraud", "deceit", "misrepresentation", "concealment", "forgery"],
    ),

    # ── 12 years ──────────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Land / Recovery of Land",
        period="12 years",
        period_months=144,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 7",
        notes=(
            "12 years from the date the adverse possession commenced, or "
            "from the date the right of action first accrued to any person "
            "through whom the claimant claims. Special rules apply to "
            "registered land under the Land Registration Act No. 3 of 2012."
        ),
        keywords=["land", "property", "adverse possession", "trespass", "eviction",
                  "title", "registration"],
    ),
    LimitationPeriod(
        cause_of_action="Mortgage (Recovery of Mortgage Money)",
        period="12 years",
        period_months=144,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 19",
        notes="12 years from the date on which the right to receive the money accrued.",
        keywords=["mortgage", "charge", "security", "bank", "loan secured"],
    ),
    LimitationPeriod(
        cause_of_action="Specialty Contract (Contract Under Seal / Deed)",
        period="12 years",
        period_months=144,
        statute="Limitation of Actions Act (Cap. 22)",
        section="s. 4(3)",
        notes="Applies to contracts executed as deeds rather than simple contracts.",
        keywords=["deed", "specialty contract", "contract under seal", "executed deed"],
    ),

    # ── No limitation ─────────────────────────────────────────────────────────
    LimitationPeriod(
        cause_of_action="Constitutional Petition (Enforcement of Fundamental Rights)",
        period="No fixed limitation period",
        period_months=9999,
        statute="Constitution of Kenya 2010",
        section="Article 22",
        notes=(
            "Article 22(3) directs the Chief Justice to make rules allowing "
            "petitions to be filed 'without undue regard to procedural technicalities'. "
            "However, courts may decline to grant relief where there has been "
            "unreasonable delay causing prejudice (doctrine of laches applies)."
        ),
        keywords=["constitutional petition", "article 22", "fundamental rights",
                  "bill of rights", "enforcement"],
    ),
    LimitationPeriod(
        cause_of_action="Judicial Review (Order 53 Applications)",
        period="3 months (promptly)",
        period_months=3,
        statute="Law Reform Act (Cap. 26); Civil Procedure Rules 2010",
        section="Order 53, r. 3(2) CPR; s. 8 Law Reform Act",
        notes=(
            "Must be brought 'promptly' and in any event within 3 months "
            "of the decision or action complained of, unless the court "
            "extends time for good reason. "
            "Some statutory bodies have shorter notice periods."
        ),
        keywords=["judicial review", "certiorari", "mandamus", "prohibition",
                  "order 53", "quash", "declaration"],
    ),
]


# ─── Lookup Function ──────────────────────────────────────────────────────────

def check_limitation(cause_of_action: str) -> dict:
    """
    Look up the limitation period(s) for a given cause of action.

    Performs keyword matching against the database entry and returns
    all matches ranked by relevance.

    Args:
        cause_of_action: Free-text description of the legal claim.

    Returns:
        Dict with 'matches' (list of results), 'query', and 'disclaimer'.
    """
    query_lower = cause_of_action.lower()
    scored: list[tuple[int, LimitationPeriod]] = []

    for entry in LIMITATION_PERIODS:
        score = 0
        # Keyword matches
        for kw in entry.keywords:
            if kw in query_lower:
                score += 2
        # Name match
        if any(word in query_lower for word in entry.cause_of_action.lower().split()):
            score += 1

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    return {
        "query": cause_of_action,
        "matches": [
            {
                "cause_of_action": e.cause_of_action,
                "period": e.period,
                "statute": e.statute,
                "section": e.section,
                "notes": e.notes,
                "relevance_score": score,
            }
            for score, e in top
        ],
        "total_found": len(scored),
        "disclaimer": (
            "Limitation periods are subject to exceptions (minority, disability, "
            "fraud, concealment). This tool provides general guidance only — "
            "always verify the applicable period with a qualified Kenyan advocate "
            "and check for any special statute governing your specific claim."
        ),
    }
