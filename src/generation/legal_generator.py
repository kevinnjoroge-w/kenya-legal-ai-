"""
Kenya Legal AI — Context-Aware Legal Reasoning Engine
=======================================================
Transformed from a template-filling system to a reasoning engine that constructs
valid legal arguments naturally. Features:
  - RAG mode   : retrieves context from Qdrant, then reasons through it
  - Direct mode: uses expert legal knowledge as fallback
  - User context profiling: adapts response to user type, knowledge, urgency
  - Argument-based quality validation (not structure-based)
  - Lazy RAG init with per-request retry
  - Modes: research | case_analysis | drafting | deep_research
           petition_drafting | judicial_review | devolution
           cross_reference | plain_language | swahili
"""

import logging
from typing import Optional

from openai import OpenAI

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# ─── System Prompts ───────────────────────────────────────────────────────────

# Used in direct (no-RAG) mode
SYSTEM_PROMPT = """\
You are a senior Kenyan advocate with 20 years of experience across constitutional law, 
commercial litigation, and public interest cases. You've argued before the Supreme Court 
and you've also sat with a client who has never set foot in a courtroom.

You don't give the same answer to every question. When someone asks something simple, 
you answer simply. When something is genuinely complex or unsettled in Kenyan law, 
you say so — you don't pretend there's a clean answer when there isn't one.

You have opinions. If the Court of Appeal got something wrong, you'll say it got it wrong 
and explain why. If Parliament drafted a provision badly, you'll point that out.

You speak like a person, not a legal textbook. You don't start every response with 
"Certainly!" or "Great question!". You don't use bullet points when a paragraph 
works better. You don't pad answers with unnecessary headers.

When you cite a case, you cite it because it actually matters to the answer — not 
to look thorough. When you don't know something or the law is silent on it, you say so 
directly rather than hedging for three paragraphs.

If someone is clearly a law student, you explain. If someone is clearly a practitioner, 
you skip the basics. Read the room.

Before answering, outline your reasoning step-by-step to ensure depth:
1. Identify the core legal issue and relevant provisions.
2. Trace the precedent chain from foundational cases to recent applications.
3. Analyze conflicts, weaknesses, or unsettled areas in the law.
4. Provide multi-angle insights: black-letter law, judicial trends, practical implications, and critiques.
5. Offer strategic or practical advice for real-world application.

Always include at least one critical opinion (e.g., "This provision is poorly drafted because...") and one practical tip (e.g., "In practice, clients often face this challenge...").

Example of a deep response:
- For a simple question like "What is Article 50?": Brief summary.
- For complex: "Article 50 guarantees fair trial rights, but the Supreme Court in *XYZ v ABC* [2020] narrowed it unduly. In practice, this means prosecutors must disclose evidence promptly, or risk acquittal. Critically, the provision lacks clarity on digital evidence, leading to inconsistent applications."

Aim for responses that feel like expert memos: insightful, opinionated, and actionable.\
"""

# Used in RAG mode
RAG_SYSTEM_PROMPT = SYSTEM_PROMPT + """

INTEGRATION RULE: You will be provided with retrieved legal sources. You must 
prioritize and cite these sources ([Source N]) whenever applicable. However, 
you are a senior advocate — you already know the Constitution and major Acts. 
If the retrieved sources do not cover a necessary point (e.g., a specific Article 
of the Constitution), DO NOT apologize or state that the sources are missing. 
Seamlessly integrate your own expert knowledge of Kenyan law to provide a complete 
analysis.

Synthesize sources into a coherent narrative: Don't list "Source 1 says X, Source 2 says Y." 
Instead, weave them into your analysis (e.g., "As established in *Mitu-Bell v Kenya Airports* 
and reinforced in *XYZ Ltd v ABC*, the principle is...").

For depth, always include:
- Precedent chain: How cases build on or distinguish each other.
- Critical analysis: Point out any weak reasoning or outdated precedents.
- Practical insights: Real-world implications, common pitfalls, or strategic advice.
- Comparative notes: If relevant, compare with East African or Commonwealth law.

Example: If sources show conflicting High Court decisions, say: "The High Court is split—*Case A* favors X, but *Case B* correctly prioritizes Y because the precedent chain from *Foundational Case* supports it. In practice, this uncertainty leads to forum-shopping."

Ensure responses are 20-30% longer than basic answers, focusing on insight over brevity.\
"""

STYLE_BY_MODE = {
    "research": """
        Answer like a colleague explaining over coffee — direct, confident,
        with nuances called out naturally. Build an argument, don't list points.
        Distinguish settled law from contested areas. Show your reasoning
        (because... therefore... this means...). Synthesize sources naturally —
        never say 'Source N says'. End with the ONE practical thing they must understand.
    """,
    "research_deep": """
        Provide scholarly depth without being verbose:
        - The foundational principles (explained clearly, not just quoted)
        - The precedent chain: how courts evolved their interpretation
        - Where courts disagree and WHY the disagreement exists
        - Your assessment of which line of reasoning is stronger and why
        - Comparative perspective (East Africa / Commonwealth) if relevant
        - The practical implication for someone actually dealing with this
        Aim for the depth of a High Court judgment. Precision over padding.
    """,
    "case_analysis": """
        Analyze like you're preparing a memo for a senior partner:
        Sharp, opinionated where the law allows, honest about weak reasoning.
        Show your thinking — is the judge's core reasoning sound? How does this
        case fit the broader jurisprudence? What distinguishes it from prior cases?
        Where would you have argued differently? What's the lasting precedential
        significance vs. what's case-specific? Don't fill a template. Build an analysis.
    """,
    "drafting": """
        Draft carefully, but don't hide behind formality. Each clause must have
        a purpose. After drafting, annotate: WHY this clause, WHAT it protects
        against, WHAT the client might want to change. Flag negotiation points
        and customization spots with [CUSTOMISE: reason].
    """,
    "deep_research": """
        Research memo for legal professionals. Build it like educating a colleague:
        - What's the legal principle and why does it matter?
        - How did it evolve (precedent chain)?
        - Where is it unsettled or contested?
        - What do other jurisdictions do differently?
        - What are the practical implications?
        - What reforms are needed (if applicable)?
        Opinionated, specific, grounded in actual cases and provisions.
    """,
    "petition_drafting": """
        Draft a petition that actually persuades — not a template to fill.
        Facts should tell a story of why the constitutional violation matters.
        Legal arguments should show why the law compels a particular outcome.
        Don't be wooden. Flag customization points with [CUSTOMISE: reason].
    """,
    "judicial_review": """
        Analyze whether judicial review is available and appropriate.
        Work through the tests methodically, but explain WHY each test matters
        for THIS case specifically, not in the abstract.
    """,
    "plain_language": """
        Explain like you're talking to a client who has never been to a lawyer.
        Simple words, short sentences. No unexplained legal jargon.
        Start with what's at stake, then walk through what the law says and
        what they can do. Include free legal aid contacts where appropriate.
    """
}

USER_CONTEXT_PROMPT = """
Before answering, read the query and decide:
- Is this person a law student? (asking "what is", "explain", "define")
- Is this a practitioner? (citing provisions, using procedural terms correctly)
- Is this a layperson? (plain language, no legal terminology)

Adjust your explanation depth, vocabulary, and assumed knowledge accordingly. 
Don't explain locus standi to someone who just cited Article 258(2)(b) correctly.
Don't throw Latin at someone asking "can my landlord kick me out without notice?"
"""

NEGATIVE_INSTRUCTIONS = """
Never start a response with: "Certainly", "Great question", "Of course", 
"As an AI", "I'd be happy to", "Absolutely".

Never end with: "I hope this helps!", "Feel free to ask more questions!", 
"Please consult a legal professional for advice specific to your situation" 
(unless the situation genuinely requires it — don't paste it as a footer on everything).

Never use bullet points just to look organized. Use them only when the content 
is genuinely list-like and a paragraph would be harder to read.

Don't summarize what you just said at the end of every response.
"""

CRITICAL_ANALYSIS_PROMPT = """
When analyzing cases or legal positions, you are allowed — and expected — to:
- Point out where a court's reasoning was weak or internally inconsistent
- Note where a dissenting judgment was actually stronger than the majority
- Flag where Kenyan courts have diverged from persuasive Commonwealth precedent 
  without good reason
- Identify where the law as written and the law as applied have drifted apart

This is legal analysis, not legal worship. The law is made by people and 
people get things wrong.
"""


# ─── Query Templates ──────────────────────────────────────────────────────────

QUERY_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Question:
{query}

Using the sources above as your primary foundation, construct a coherent legal
argument — not a structured report. Before writing, think through:
1. What is the ACTUAL legal question? (Often different from what's literally asked.)
2. Which facts or provisions shift the outcome?
3. What would a strong opposing argument be, and how do you counter it?
4. Which retrieved sources directly control this? Which are peripheral?
5. What is the ONE insight that changes how they understand this?

Build your answer like a lawyer reasoning through the problem aloud. Distinguish
between settled law and genuinely contested areas. Show your reasoning — because...
therefore... this means... Cite sources by their actual name, not "Source N".
If sources are incomplete, supplement from your own legal knowledge without apology.

End with the practical takeaway: what should this person actually do or know?

After your answer, list 2-3 follow-up questions (as a bullet list) that would
deepen understanding or clarify practical application.

## Answer:"""

DIRECT_QUERY_TEMPLATE = """\
## Question:
{query}

Using your expert legal knowledge, construct a coherent legal argument. 
Identify the controlling provisions or precedents and explain HOW they apply 
to the user's situation. Do not just list points. Show your reasoning: 
state the law, apply it to the facts (even if implied), and conclude.
Highlight any areas of legal uncertainty.

After your answer, suggest 2-3 specific follow-up questions.

## Answer:"""

CASE_ANALYSIS_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Case / Topic to Analyse:
{query}

Using the sources above, analyze this case or legal position like a senior advocate.
Focus your reasoning on:
1. What was the core legal problem?
2. Is the judge's reasoning logically sound? Where are the gaps?
3. How does this decision fit into (or disrupt) the broader jurisprudence?
4. What is the lasting practical impact?

Do not just summarise the facts. Build a critical, opinionated analysis.
Cite specific sources by name.

## Analysis:"""

DIRECT_CASE_ANALYSIS_TEMPLATE = """\
## Case / Topic to Analyse:
{query}

Analyze this case or legal position like a senior advocate.
Focus your reasoning on:
1. What was the core legal problem?
2. Is the judge's reasoning logically sound? Where are the gaps?
3. How does this decision fit into (or disrupt) the broader jurisprudence?
4. What is the lasting practical impact?

Do not just summarise the facts. Build a critical, opinionated analysis.

## Analysis:"""

DOCUMENT_DRAFTING_TEMPLATE = """\
## Relevant Legal Sources:
{context}

---

## Drafting Request:
{query}

Draft the required document, but do not just act as a form-filler.
For every substantive clause, reason through why it is necessary based on the 
provided sources or Kenyan law generally. 
Add annotations (e.g. [NOTE: ...]) explaining the strategic reason for a clause 
or flagging where the user must make a strategic choice.
Flag customization points with [CUSTOMISE: reason].

## Draft:"""

DIRECT_DRAFTING_TEMPLATE = """\
## Drafting Request:
{query}

Draft the required document, but do not just act as a form-filler.
For every substantive clause, reason through why it is necessary under Kenyan law.
Add annotations (e.g. [NOTE: ...]) explaining the strategic reason for a clause 
or flagging where the user must make a strategic choice.
Flag customization points with [CUSTOMISE: reason].

## Draft:"""

DEEP_RESEARCH_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Research Topic:
{query}

Build a comprehensive scholarly legal argument using the sources above.
Do not use rigid structural templates. Instead, reason through the topic 
methodically:
- Explain the foundational principles and why they matter.
- Trace the chain of precedent showing how the law evolved.
- Analyze conflicting authorities and explain why the conflict exists.
- Evaluate the practical implications.

Your argument should flow logically from one point to the next, building 
a complete picture of the law. Cite sources by their actual names.

## Scholarly Analysis:"""

DIRECT_DEEP_RESEARCH_TEMPLATE = """\
## Research Topic:
{query}

Build a comprehensive scholarly legal argument.
Do not use rigid structural templates. Instead, reason through the topic 
methodically:
- Explain the foundational principles and why they matter.
- Trace the chain of precedent showing how the law evolved.
- Analyze conflicting authorities and explain why the conflict exists.
- Evaluate the practical implications.

Your argument should flow logically from one point to the next.

## Scholarly Analysis:"""

# Template for generating follow-up question suggestions
FOLLOWUP_TEMPLATE = """\
A user asked a legal question about Kenyan law and received a comprehensive \
answer. Based on the topic covered, suggest exactly 3 concise follow-up \
questions that would help the user deepen their understanding.

The original question was:
"{query}"

Rules for follow-up questions:
- Each question must be a natural next step from the answer given
- Each question should be 1 sentence, under 15 words
- Questions should cover: (1) a practical application or case example, (2) an exception or edge case, (3) a related legal area or reform
- Return ONLY the 3 questions, one per line, no numbering, no preamble

Questions:"""


# ─── Petition Drafting Templates ─────────────────────────────────────────────

PETITION_DRAFTING_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Petition Request:
{query}

Draft a persuasive constitutional petition. The facts must tell a story of why 
the constitutional violation matters, and the legal arguments must reason 
from the provided sources to show why the law compels a particular outcome. 
Do not be wooden or overly formulaic. Reason through the violation and the relief sought.
Flag customization points with [CUSTOMISE: reason].

## Draft:"""

DIRECT_PETITION_DRAFTING_TEMPLATE = """\
## Petition Request:
{query}

Draft a persuasive constitutional petition. The facts must tell a story of why 
the constitutional violation matters, and the legal arguments must show why 
the law compels a particular outcome. 
Do not be wooden or overly formulaic. Reason through the violation and the relief sought.
Flag customization points with [CUSTOMISE: reason].

## Draft:"""

# ─── Judicial Review Templates ────────────────────────────────────────────────

JUDICIAL_REVIEW_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Judicial Review Request:
{query}

Reason through whether judicial review is available and appropriate for this case.
Methodically apply the tests (illegality, irrationality, procedural impropriety, etc.), 
but explain WHY each test matters for THIS specific situation, rather than just 
stating the abstract rule. Rely on the provided sources to build your argument.

## Analysis:"""

DIRECT_JUDICIAL_REVIEW_TEMPLATE = """\
## Judicial Review Request:
{query}

Reason through whether judicial review is available and appropriate for this case.
Methodically apply the tests (illegality, irrationality, procedural impropriety, etc.), 
but explain WHY each test matters for THIS specific situation, rather than just 
stating the abstract rule.

## Analysis:"""

# ─── Devolution & County Law Templates ───────────────────────────────────────

DEVOLUTION_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Devolution / County Law Question:
{query}

Reason through this devolution conflict using the provided sources. 
Don't just list the Fourth Schedule functions; analyze where the functions 
intersect and apply the supremacy rules to build a coherent argument for 
how the conflict should be resolved.

## Analysis:"""

DIRECT_DEVOLUTION_TEMPLATE = """\
## Devolution / County Law Question:
{query}

Reason through this devolution conflict. 
Don't just list the Fourth Schedule functions; analyze where the functions 
intersect and apply the supremacy rules to build a coherent argument for 
how the conflict should be resolved.

## Analysis:"""

# ─── Statute Cross-Reference Templates ───────────────────────────────────────

CROSS_REFERENCE_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Statutory Cross-Reference Request:
{query}

Analyze how the relevant provisions across different statutes or regulations 
interact based on the sources provided. Reason through the hierarchy or conflict 
between them to provide a synthesized view of the law.

## Analysis:"""

DIRECT_CROSS_REFERENCE_TEMPLATE = """\
## Statutory Cross-Reference Request:
{query}

Analyze how the relevant provisions across different statutes or regulations 
interact. Reason through the hierarchy or conflict between them to provide 
a synthesized view of the law.

## Analysis:"""

# ─── Plain Language / Access to Justice Templates ─────────────────────────────

PLAIN_LANGUAGE_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## User's Situation:
{query}

Explain the law and what they should do next like you are talking to someone 
who has never spoken to a lawyer before. Focus entirely on the practical reality 
and the specific steps they need to take. Do not use legal jargon.

## Explanation:"""

DIRECT_PLAIN_LANGUAGE_TEMPLATE = """\
## User's Situation:
{query}

Explain the law and what they should do next like you are talking to someone 
who has never spoken to a lawyer before. Focus entirely on the practical reality 
and the specific steps they need to take. Do not use legal jargon.

## Explanation:"""

# ─── Swahili Query Templates ──────────────────────────────────────────────────

SWAHILI_TEMPLATE = """\
## Vyanzo vya Kisheria Vilivyopatikana:
{context}

---

## Swahili Query:
{query}

Jibu swali hili kwa Kiswahili sanifu na kinachoeleweka kwa urahisi. 
Tumia vyanzo vilivyoambatanishwa kujenga hoja ya kisheria.
Kama unatumia maneno ya kisheria ya Kiingereza, yawekee maelezo kwa Kiswahili.

## Jibu:"""

DIRECT_SWAHILI_TEMPLATE = """\
## Swahili Query:
{query}

Jibu swali hili kwa Kiswahili sanifu na kinachoeleweka kwa urahisi. 
Jenga hoja ya kisheria kulingana na sheria za Kenya.
Kama unatumia maneno ya kisheria ya Kiingereza, yawekee maelezo kwa Kiswahili.

## Jibu:"""


# ─── Generator ────────────────────────────────────────────────────────────────


class LegalGenerator:
    """LLM-powered legal response generator with RAG context and conversation memory."""

    def __init__(self):
        settings = get_settings()
        self.model = settings.llm_model

        # Set up LLM client based on provider
        if settings.llm_provider == "groq":
            api_key = (settings.groq_api_key or "").strip()
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=120.0,
            )
            logger.info(f"Using Groq ({self.model})")
        elif settings.llm_provider == "mistral":
            api_key = (settings.mistral_api_key or "").strip()
            if not api_key:
                logger.warning("MISTRAL_API_KEY not set, falling back to Groq")
                # Fallback to Groq
                groq_key = (settings.groq_api_key or "").strip()
                if groq_key:
                    self.client = OpenAI(
                        api_key=groq_key,
                        base_url="https://api.groq.com/openai/v1",
                        timeout=120.0,
                    )
                    self.model = "llama-3.3-70b-versatile"  # Use Groq model
                    logger.info(f"Mistral API key missing, using Groq fallback ({self.model})")
                else:
                    raise ValueError("Neither MISTRAL_API_KEY nor GROQ_API_KEY are set")
            else:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.mistral.ai/v1",
                    timeout=120.0,
                )
                logger.info(f"Using Mistral AI ({self.model})")
        elif settings.llm_provider == "google":
            api_key = (settings.google_api_key or "").strip()
            if not api_key:
                logger.error("GOOGLE_API_KEY is missing for Gemini LLM.")
                raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=120.0,
            )
            logger.info(f"Using Google Gemini ({self.model})")
        else:
            api_key = (settings.openai_api_key or "").strip()
            self.client = OpenAI(api_key=api_key, timeout=120.0)
            logger.info(f"Using OpenAI ({self.model})")

        self.retrieval = None
        self._rag_available = False
        self._rag_error = None

        # Attempt eager RAG setup — failures are logged but do NOT crash the
        # server. The flag is re-checked lazily on every request so a transient
        # cold-start network hiccup does not permanently disable retrieval.
        self._try_init_rag()

    def _try_init_rag(self):
        """Attempt to initialise the RAG pipeline. Safe to call multiple times."""
        try:
            from src.retrieval.retrieval_pipeline import RetrievalPipeline
            self.retrieval = RetrievalPipeline()
            info = self.retrieval.embedding_service.get_collection_info()
            if "error" in info:
                self._rag_available = False
                self._rag_error = info["error"]
                logger.warning(f"RAG startup probe failed — vector DB error: {info['error']}")
            else:
                self._rag_available = True
                self._rag_error = None
                logger.info(f"RAG mode active — {info.get('points_count', '?')} vectors in collection")
        except Exception as e:
            self._rag_available = False
            self._rag_error = str(e)
            logger.warning(f"RAG unavailable at startup (will retry per-request): {e}")

    def _build_user_context_profile(self, query: str, prior_context: Optional[str] = None) -> dict:
        """
        Build a profile of who this user is and what they care about.
        This shapes how we construct arguments throughout the response.
        """
        profile: dict = {}

        # Infer user type from query language
        if any(w in query.lower() for w in ["my company", "business", "enterprise", "ltd", "limited"]):
            profile["user_type"] = "business"
        elif any(w in query.lower() for w in ["petition", "plead", "file", "court order", "locus standi", "ultra vires"]):
            profile["user_type"] = "practitioner"
        else:
            profile["user_type"] = "individual"

        # Infer legal knowledge from terminology used
        advanced_terms = ["locus standi", "ultra vires", "mens rea", "pro bono", "certiorari", "mandamus"]
        if sum(1 for t in advanced_terms if t in query.lower()) >= 2:
            profile["legal_knowledge"] = "advanced"
        elif any(t in query.lower() for t in ["article", "section", "act", "statute", "provision"]):
            profile["legal_knowledge"] = "basic"
        else:
            profile["legal_knowledge"] = "none"

        # Infer urgency
        urgent_words = ["urgent", "asap", "immediately", "deadline", "court date", "tomorrow", "today"]
        profile["urgency"] = "high" if any(w in query.lower() for w in urgent_words) else "medium"

        profile["situation_summary"] = query[:200]
        profile["prior_context"] = prior_context or ""

        # Extract constraints
        constraints = []
        if "budget" in query.lower() or "afford" in query.lower() or "cheap" in query.lower():
            constraints.append("cost-sensitive")
        if "time" in query.lower() or profile["urgency"] == "high":
            constraints.append("time-sensitive")
        if "confidential" in query.lower() or "private" in query.lower():
            constraints.append("confidentiality-required")
        profile["key_constraints"] = constraints

        return profile

    def _score_source_for_context(self, source: dict, user_profile: Optional[dict] = None) -> float:
        """
        Dynamically re-weights sources based on the user's profile and current context.
        """
        base_score = source.get("score", 0.0)
        authority = source.get("hierarchy_weight", 0.0)
        
        # Start with standard RAG score and bump by authority
        weight = base_score + (authority * 0.2)
        
        if not user_profile:
            return weight

        # If urgent, prioritize direct statutes over long cases
        if user_profile.get("urgency") == "high":
            if source.get("document_type") in ["constitution", "act"]:
                weight += 0.15
        
        # If practitioner, prioritize Supreme Court and Court of Appeal cases
        if user_profile.get("user_type") == "practitioner":
            if authority >= 0.8:  # SC and CoA
                weight += 0.1
                
        # If plain language, slightly prefer Constitutions and Acts over dense cases
        if user_profile.get("legal_knowledge") == "none":
            if source.get("document_type") in ["constitution", "act", "legal_notice"]:
                weight += 0.1

        return weight

    # ── RAG Templates ──────────────────────────────────────────────────────────

    _RAG_TEMPLATES = {
        "research": QUERY_TEMPLATE,
        "research_deep": QUERY_TEMPLATE,  # Uses same template but with deeper style
        "case_analysis": CASE_ANALYSIS_TEMPLATE,
        "drafting": DOCUMENT_DRAFTING_TEMPLATE,
        "deep_research": DEEP_RESEARCH_TEMPLATE,
        "petition_drafting": PETITION_DRAFTING_TEMPLATE,
        "judicial_review": JUDICIAL_REVIEW_TEMPLATE,
        "devolution": DEVOLUTION_TEMPLATE,
        "cross_reference": CROSS_REFERENCE_TEMPLATE,
        "plain_language": PLAIN_LANGUAGE_TEMPLATE,
        "swahili": SWAHILI_TEMPLATE,
    }

    _DIRECT_TEMPLATES = {
        "research": DIRECT_QUERY_TEMPLATE,
        "research_deep": DIRECT_QUERY_TEMPLATE,
        "case_analysis": DIRECT_CASE_ANALYSIS_TEMPLATE,
        "drafting": DIRECT_DRAFTING_TEMPLATE,
        "deep_research": DIRECT_DEEP_RESEARCH_TEMPLATE,
        "petition_drafting": DIRECT_PETITION_DRAFTING_TEMPLATE,
        "judicial_review": DIRECT_JUDICIAL_REVIEW_TEMPLATE,
        "devolution": DIRECT_DEVOLUTION_TEMPLATE,
        "cross_reference": DIRECT_CROSS_REFERENCE_TEMPLATE,
        "plain_language": DIRECT_PLAIN_LANGUAGE_TEMPLATE,
        "swahili": DIRECT_SWAHILI_TEMPLATE,
    }

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate(
        self,
        query: str,
        mode: str = "research",
        document_type: Optional[str] = None,
        court: Optional[str] = None,
        history: Optional[list[dict]] = None,
        prior_context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ) -> dict:
        """
        Generate a legal response.

        Args:
            query: The user's current question.
            mode: research | case_analysis | drafting | deep_research
            document_type: Optional filter (constitution, act, judgment, legal_notice)
            court: Optional court filter
            history: List of {role, content} dicts representing prior turns.
            prior_context: User's prior statements/context — shapes entire response.
            temperature: LLM temperature (lower = more factual)
            max_tokens: Maximum generation length
        """
        history = history or []

        # Build user context profile first — informs every subsequent step
        user_profile = self._build_user_context_profile(query, prior_context)

        # Conversational greeting bypass (pure greetings only)
        if self._is_greeting(query):
            logger.info(f"Pure greeting detected: '{query}'. Bypassing RAG.")
            return self._generate_greeting_response(query, mode)

        # Determine temperature from mode if not explicitly provided
        if temperature is None:
            settings = get_settings()
            if mode in ("drafting", "petition_drafting"):
                temperature = getattr(settings, "drafting_temperature", 0.2)
            else:
                temperature = getattr(settings, "llm_temperature", 0.4)

        # Lazy RAG init — retry on every request if startup probe failed
        if not self._rag_available:
            self._try_init_rag()

        if self._rag_available:
            return self._generate_rag(
                query, mode, document_type, court,
                history, temperature, max_tokens,
                user_profile=user_profile,
            )
        else:
            logger.warning(f"RAG not available, using direct mode. Last error: {self._rag_error}")
            return self._generate_direct(
                query, mode, history, temperature, max_tokens,
                user_profile=user_profile,
                rag_error=self._rag_error,
            )

    def ask(self, query: str, **kwargs) -> dict:
        """Shortcut for legal research queries."""
        return self.generate(query, mode="research", **kwargs)

    def analyze_case(self, query: str, **kwargs) -> dict:
        """Shortcut for case analysis."""
        return self.generate(query, mode="case_analysis", **kwargs)

    def draft_document(self, query: str, **kwargs) -> dict:
        """Shortcut for document drafting."""
        return self.generate(query, mode="drafting", **kwargs)

    def deep_research(self, query: str, **kwargs) -> dict:
        """Shortcut for deep scholarly research."""
        return self.generate(query, mode="deep_research", **kwargs)

    def _is_greeting(self, query: str) -> bool:
        """
        Detect if this is JUST a greeting (not a greeting + question).
        Only pure greetings bypass RAG/research mode.
        """
        q = query.strip().lower().strip("?!.,-")
        pure_greetings = {
            "hello", "hi", "hey", "jambo", "habari", "mambo", "sasa",
            "good morning", "good afternoon", "good evening",
            "greetings", "yo", "sup", "howdy", "test", "testing",
            "hello there", "hi there"
        }
        if q in pure_greetings:
            return True
        # Do NOT treat "hello, what about X" as a greeting
        if "," in query or any(w in q for w in ["what", "how", "explain", "tell me", "ask", "can", "does", "is ", "are "]):
            return False
        # Short phrase starting with a greeting word (e.g. "hello assistant")
        words = q.split()
        if len(words) <= 2 and words[0] in pure_greetings:
            return True
        return False

    def _generate_greeting_response(self, query: str, mode: str) -> dict:
        """Generate a warm, helpful, non-RAG response for simple greetings."""
        system_prompt = (
            "You are Kenya Legal AI, a friendly, expert, and professional legal assistant "
            "trained on the Kenyan legal framework. Respond to this user greeting warmly and professionally. "
            "Introduce yourself briefly as a specialized legal assistant and mention that you can help with "
            "legal research, case analysis, document drafting, constitutional interpretation, "
            "and Swahili legal translations. Keep the response concise, engaging, and end with a question "
            "asking how you can help them with their legal research today."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            completion, used_model = self._create_chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=150,
            )
            return {
                "response": completion.choices[0].message.content,
                "sources": [],
                "mode": mode,
                "model": used_model,
                "rag_used": False,
                "follow_up_questions": [
                    "What are the requirements for a valid contract in Kenya?",
                    "Can you help me draft a tenant agreement?",
                    "Explain Article 27 of the Constitution of Kenya."
                ]
            }
        except Exception as e:
            logger.error(f"Greeting response failed: {e}")
            # Secure fallback response
            return {
                "response": (
                    "Hello! I am Kenya Legal AI, your specialized legal research assistant. "
                    "I can help you with legal research, case analysis, document drafting, "
                    "and navigating the Kenyan legal system. How can I assist you with your legal questions today?"
                ),
                "sources": [],
                "mode": mode,
                "model": self.model,
                "rag_used": False,
                "follow_up_questions": [
                    "What are the requirements for a valid contract in Kenya?",
                    "Can you help me draft a tenant agreement?",
                    "Explain Article 27 of the Constitution of Kenya."
                ]
            }

    def _truncate_messages_for_tpm(self, messages, max_chars=18000):
        """Truncate messages to fit within tight TPM limits (e.g. 6000 tokens)."""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        if total_chars <= max_chars:
            return messages

        logger.info(f"Payload size ({total_chars} chars) exceeds safety threshold ({max_chars} chars). Truncating...")
        
        # Make a copy of messages
        pruned = [m.copy() for m in messages]
        
        # 1. Prune history (remove all turns between system prompt and user prompt)
        if len(pruned) > 2:
            logger.info("Pruning conversation history to fit TPM limit.")
            pruned = [pruned[0], pruned[-1]]
            total_chars = sum(len(m.get("content", "")) for m in pruned)
            if total_chars <= max_chars:
                return pruned

        # 2. Prune retrieved RAG chunks in the user prompt
        user_content = pruned[-1].get("content", "")
        if "## Retrieved Legal Sources:" in user_content and "## Case / Topic to Analyse:" in user_content:
            parts = user_content.split("## Case / Topic to Analyse:")
            context_part = parts[0]
            query_part = "## Case / Topic to Analyse:" + parts[1]
            
            # Extract chunks from context_part
            context_prefix = "## Retrieved Legal Sources:\n"
            actual_context = context_part.replace("## Retrieved Legal Sources:\n", "").strip()
            chunks = actual_context.split("\n---\n")
            
            # Keep chunks from the beginning until we hit the char limit
            keep_chunks = []
            current_len = len(context_prefix) + len(query_part)
            for chunk in chunks:
                if current_len + len(chunk) + 5 > max_chars:
                    break
                keep_chunks.append(chunk)
                current_len += len(chunk) + 5
                
            if not keep_chunks:
                new_user_content = f"## Retrieved Legal Sources:\n[Context omitted to fit rate limits]\n\n{query_part}"
            else:
                new_context = "\n---\n".join(keep_chunks)
                new_user_content = f"## Retrieved Legal Sources:\n{new_context}\n\n{query_part}"
                
            pruned[-1]["content"] = new_user_content
            logger.info(f"Truncated RAG context chunks to fit TPM limit. New size: {len(new_user_content)} chars.")
            
        return pruned

    def _create_chat_completion(self, messages, temperature, max_tokens):
        """Helper to create a chat completion with automatic rate-limit fallbacks."""
        # Try primary model first
        models_to_try = [self.model]
        
        # If using Groq and the primary is the 70B model, add fallbacks
        # Groq's 70B has tight rate limits on the free tier, but 8B is separated
        if "70b" in self.model or "versatile" in self.model:
            models_to_try.append("llama-3.1-8b-instant")
            
        for i, model in enumerate(models_to_try):
            try:
                active_messages = messages
                if model == "llama-3.1-8b-instant":
                    active_messages = self._truncate_messages_for_tpm(messages)
                    
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=active_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return completion, model
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "rate_limit" in err_str
                if is_rate_limit and i < len(models_to_try) - 1:
                    logger.warning(f"Groq Model {model} hit rate limit (429). Falling back to {models_to_try[i+1]}...")
                    continue
                else:
                    raise e
        raise RuntimeError("All models failed to generate response")

    # ── Internal: RAG Generation ───────────────────────────────────────────────

    def _generate_rag(
        self, query, mode, document_type, court,
        history, temperature, max_tokens,
        user_profile: Optional[dict] = None,
    ) -> dict:
        """Generate a response grounded in retrieved source documents."""
        try:
            raw_results = self.retrieval.retrieve(
                query=query,
                document_type=document_type,
                court=court,
            )
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return self._generate_direct(query, mode, history, temperature, max_tokens,
                                         user_profile=user_profile, rag_error=f"Retrieval failed: {e}")

        if not raw_results:
            logger.info("No RAG context found — falling back to direct mode")
            return self._generate_direct(query, mode, history, temperature, max_tokens,
                                         user_profile=user_profile,
                                         rag_error="No matching documents found in vector database")

        # Sort results by relevance AND authority (not just retrieval order)
        weighted_results = [
            (result, self._score_source_for_context(result, user_profile))
            for result in raw_results
        ]
        weighted_results.sort(key=lambda x: x[1], reverse=True)

        context_parts = []
        total_length = 0
        max_context_length = 14000

        for i, (result, weight) in enumerate(weighted_results, 1):
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

            authority = result.get("hierarchy_weight", 0)
            authority_label = self.retrieval._authority_label(authority)
            source_label = " | ".join(source_info) if source_info else "Unknown Source"

            chunk = (
                f"[Source {i}: {source_label} | Authority: {authority_label} | Relevance: {weight:.2f}]\n"
                f"{result['text']}\n"
            )

            if total_length + len(chunk) > max_context_length:
                logger.info(f"Context limit reached after {i-1} sources")
                break

            context_parts.append(chunk)
            total_length += len(chunk)

        context = "\n---\n".join(context_parts)
        if len(context_parts) < 3:
            context += "\n\n[NOTE: Limited sources retrieved. Response grounded in these sources plus expert legal knowledge.]"

        template = self._RAG_TEMPLATES.get(mode, QUERY_TEMPLATE)
        user_prompt = template.format(context=context, query=query)

        messages = self._build_messages(RAG_SYSTEM_PROMPT, history, user_prompt, mode, user_profile=user_profile)

        try:
            completion, used_model = self._create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = completion.choices[0].message.content

            # Argument-validation quality check for deep modes
            if mode in ["research_deep", "deep_research", "case_analysis"]:
                is_adequate, feedback = self._check_response_quality(response_text, mode)
                if not is_adequate:
                    logger.info(f"Enhancing response quality: {feedback}")
                    response_text = self._enhance_response_quality(
                        response_text, feedback, query, mode, temperature
                    )

            main_response, follow_up_questions = self._parse_follow_ups(response_text)

            sources = [
                {
                    "title": r.get("document_title", ""),
                    "section": r.get("section", ""),
                    "citation": r.get("citation", ""),
                    "court": r.get("court", ""),
                    "date": r.get("date", ""),
                    "relevance_score": r.get("score", 0),
                }
                for r in raw_results
            ]

            return {
                "response": main_response,
                "sources": sources,
                "mode": mode,
                "model": used_model,
                "rag_used": True,
                "follow_up_questions": follow_up_questions,
                "user_profile": {
                    "type": user_profile.get("user_type") if user_profile else None,
                    "legal_knowledge": user_profile.get("legal_knowledge") if user_profile else None,
                    "urgency": user_profile.get("urgency") if user_profile else None,
                },
                "tokens_used": {
                    "prompt": completion.usage.prompt_tokens,
                    "completion": completion.usage.completion_tokens,
                    "total": completion.usage.total_tokens,
                },
            }
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            return self._generate_direct(query, mode, history, temperature, max_tokens,
                                         user_profile=user_profile, rag_error=f"Generation failed: {e}")

    # ── Internal: Direct Generation ────────────────────────────────────────────

    def _generate_direct(self, query, mode, history, temperature, max_tokens,
                         user_profile: Optional[dict] = None, rag_error=None) -> dict:
        """Generate a response using direct LLM knowledge (no RAG)."""
        template = self._DIRECT_TEMPLATES.get(mode, DIRECT_QUERY_TEMPLATE)
        user_prompt = template.format(query=query)

        messages = self._build_messages(SYSTEM_PROMPT, history, user_prompt, mode, user_profile=user_profile)

        try:
            completion, used_model = self._create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = completion.choices[0].message.content

            # Argument-validation quality check for deep modes
            if mode in ["research_deep", "deep_research", "case_analysis"]:
                is_adequate, feedback = self._check_response_quality(response_text, mode)
                if not is_adequate:
                    logger.info(f"Enhancing response quality: {feedback}")
                    response_text = self._enhance_response_quality(
                        response_text, feedback, query, mode, temperature
                    )

            main_response, follow_up_questions = self._parse_follow_ups(response_text)

            return {
                "response": main_response,
                "sources": [],
                "mode": mode,
                "model": used_model,
                "rag_used": False,
                "follow_up_questions": follow_up_questions,
                "rag_error": rag_error,
                "user_profile": {
                    "type": user_profile.get("user_type") if user_profile else None,
                    "legal_knowledge": user_profile.get("legal_knowledge") if user_profile else None,
                    "urgency": user_profile.get("urgency") if user_profile else None,
                },
                "tokens_used": {
                    "prompt": completion.usage.prompt_tokens,
                    "completion": completion.usage.completion_tokens,
                    "total": completion.usage.total_tokens,
                },
            }

        except Exception as e:
            logger.error(f"Direct LLM generation failed: {e}")
            error_str = str(e)

            if "429" in error_str or "quota" in error_str.lower():
                error_msg = (
                    "⚠️ **Rate limit / quota exceeded.** "
                    "Your API key has hit its usage limit. "
                    "Wait a few minutes and try again, or check your billing dashboard."
                )
            elif "401" in error_str or "auth" in error_str.lower():
                error_msg = (
                    "⚠️ **Authentication failed.** "
                    "Your API key appears to be invalid. "
                    "Please check the key in your .env file."
                )
            else:
                error_msg = (
                    "An error occurred while generating the response. "
                    "Please check your API key configuration in .env and try again."
                )

            return {
                "response": error_msg,
                "sources": [],
                "mode": mode,
                "follow_up_questions": [],
                "error": error_str,
            }

    # ── Internal: Helpers ──────────────────────────────────────────────────────

    def _check_response_quality(self, response_text: str, mode: str) -> tuple[bool, str]:
        """
        Check if the response contains VALID LEGAL REASONING, not just structure.
        Returns (is_adequate, feedback).
        """
        issues = []

        # 1. Does it acknowledge complexity where appropriate?
        if mode in ["research_deep", "deep_research", "case_analysis"]:
            complexity_markers = ["however", "but", "tension", "conflict", "unclear",
                                  "courts split", "unsettled", "one interpretation"]
            if not any(m in response_text.lower() for m in complexity_markers):
                issues.append("doesn't acknowledge genuine complexity in the law")

        # 2. Does it distinguish settled law from contested areas?
        settled = ["clearly established", "no doubt", "well-settled", "uncontroversial"]
        contested = ["debated", "disputed", "unclear", "split", "disagreement"]
        has_distinctions = (
            any(m in response_text.lower() for m in settled) or
            any(m in response_text.lower() for m in contested)
        )
        if not has_distinctions and mode in ["research", "deep_research"]:
            issues.append("treats all legal positions equally; doesn't distinguish settled from contested")

        # 3. Does it show reasoning rather than bare conclusions?
        reasoning_markers = ["because", "therefore", "this means", "the significance",
                             "here's why", "what this means"]
        if not any(m in response_text.lower() for m in reasoning_markers):
            issues.append("lacks visible reasoning; feels like conclusions without support")

        # 4. Does it acknowledge uncertainty where nuance is warranted?
        uncertainty = ["uncertain", "not clear", "unclear", "may", "might", "depends on", "could argue"]
        if mode in ["case_analysis", "drafting"] and len(response_text) > 500:
            if not any(m in response_text.lower() for m in uncertainty):
                issues.append("presents everything as certain when nuance is appropriate")

        # 5. Drafting mode must flag customization points
        if mode in ["drafting", "petition_drafting"] and "[CUSTOMISE:" not in response_text:
            issues.append("doesn't flag customization points for the drafter")

        # 6. Plain language mode must avoid legalese
        if mode == "plain_language":
            legalese = ["pursuant to", "heretofore", "notwithstanding", "inter alia",
                        "prima facie", "ceteris paribus"]
            if any(t in response_text for t in legalese):
                issues.append("uses legal jargon in plain language mode")

        if issues:
            return False, " | ".join(issues)
        return True, ""

    def _enhance_response_quality(self, response_text: str, feedback: str, query: str, mode: str, temperature: float) -> str:
        """
        Re-prompt the LLM to improve response quality based on feedback.
        """
        enhancement_prompt = f"""\
The previous response was inadequate: {feedback}

Original query: {query}

Previous response:
{response_text}

Please provide an enhanced version that addresses these shortcomings. Focus on adding:
- Specific legal citations and case references
- Critical analysis and opinionated critiques
- Practical advice for real-world application

Enhanced response:"""

        try:
            messages = [{"role": "user", "content": enhancement_prompt}]
            completion, _ = self._create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=2048,  # Shorter for enhancement
            )
            return completion.choices[0].message.content or response_text
        except Exception as e:
            logger.warning(f"Quality enhancement failed: {e}")
            return response_text

    def _parse_follow_ups(self, response_text: str) -> tuple[str, list[str]]:
        """
        Parse the main response and follow-up questions from the LLM output.
        
        Looks for a 'Follow-up Questions:' section and splits accordingly.
        """
        # Look for various markers
        markers = ["## Follow-up Questions:", "Follow-up Questions:", "follow-up questions:", "Some potential follow-up questions to deepen the research or clarify practical application include:"]
        for marker in markers:
            if marker in response_text:
                parts = response_text.split(marker, 1)
                main_response = parts[0].strip()
                followup_section = parts[1].strip()
                # Parse bullet points
                questions = [
                    q.strip().lstrip("-•* ")
                    for q in followup_section.splitlines()
                    if q.strip() and q.strip().startswith(("-", "•", "*", "1.", "2.", "3."))
                ]
                return main_response, questions[:3]
        
        # Fallback: no follow-ups found
        return response_text.strip(), []

    def _build_messages(
        self,
        system_prompt: str,
        history: list[dict],
        current_user_prompt: str,
        mode: str = "research",
        user_profile: Optional[dict] = None,
    ) -> list[dict]:
        """
        Build the full messages array for the LLM call.
        Injects user context profile to shape reasoning style.
        """
        full_system_prompt = system_prompt
        full_system_prompt += "\n\n" + USER_CONTEXT_PROMPT
        full_system_prompt += "\n\n" + CRITICAL_ANALYSIS_PROMPT

        # Inject user-specific guidance when a profile is available
        if user_profile:
            constraints_str = (
                ", ".join(user_profile["key_constraints"])
                if user_profile["key_constraints"] else "none identified"
            )
            prior = user_profile.get("prior_context", "")[:300] or "none"
            user_guidance = f"""
## ABOUT THIS USER:
- Type: {user_profile['user_type']}
- Legal Knowledge: {user_profile['legal_knowledge']}
- Urgency: {user_profile['urgency']}
- Key Constraints: {constraints_str}
Prior Context: {prior}

## GUIDANCE:
- No legal knowledge → explain simply; replace Latin with plain English.
- Practitioner → skip basics, use technical language.
- Time-sensitive → lead with the CRITICAL ACTION they should take NOW.
- Cost-conscious → flag expensive vs. cheaper alternatives.
Make every sentence relevant to THEIR specific situation."""
            full_system_prompt += user_guidance

        if mode in STYLE_BY_MODE:
            full_system_prompt += "\n\n" + STYLE_BY_MODE[mode]

        full_system_prompt += "\n\n" + NEGATIVE_INSTRUCTIONS

        messages: list[dict] = [{"role": "system", "content": full_system_prompt}]

        for turn in history[-10:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": current_user_prompt})
        return messages

    def _generate_follow_up_questions(self, query: str) -> list[str]:
        """
        Generate 3 suggested follow-up questions after a legal answer.

        Uses a lightweight, fast call with a low token budget.
        """
        try:
            prompt = FOLLOWUP_TEMPLATE.format(query=query)
            completion, _ = self._create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,   # slightly more creative for variety
                max_tokens=120,    # 3 short questions is all we need
            )
            raw = completion.choices[0].message.content or ""
            questions = [
                q.strip().lstrip("0123456789.-) ")
                for q in raw.strip().splitlines()
                if q.strip()
            ]
            return questions[:3]  # always return at most 3
        except Exception as e:
            logger.warning(f"Follow-up question generation failed: {e}")
            return []
