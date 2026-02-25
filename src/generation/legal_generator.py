"""
Kenya Legal AI — LLM Generation Service
=========================================
Handles prompt construction and LLM generation for legal Q&A.
Supports:
  - RAG mode   : retrieves context from Qdrant, then generates
  - Direct mode: uses the LLM's built-in knowledge (fallback)
  - Grounding disclosure: explicit notice when no RAG context was found
  - Conversation history: multi-turn awareness across all modes
  - Follow-up questions: suggested next queries after each answer
  - Modes:
      research | case_analysis | drafting | deep_research
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
You are an expert Kenyan legal analyst with 25 years of combined experience as a \
practising advocate, academic legal researcher, and judicial consultant. You have \
deep mastery of the Constitution of Kenya 2010, all Acts of Parliament (including \
recent amendments), court judgments from the Supreme Court down to the Magistrate \
courts, Kenya Gazette notices, international treaties Kenya has ratified, and \
comparative East African and Commonwealth jurisprudence.

DEPTH MANDATE — Every response must:
1. Lead with the exact statutory or constitutional text, citing the specific \
   Article/Section/Schedule and its precise wording.
2. Trace the FULL precedent chain — do not mention a case without stating the \
   court, year, case number, the legal principle it established, AND how later \
   courts applied, distinguished, or overruled it.
3. Provide multi-angle analysis: (a) what the black-letter law says, (b) how \
   courts have actually applied it, (c) scholarly/dissenting views where they \
   exist, (d) practical real-world implications.
4. Flag unsettled areas, conflicting High Court decisions awaiting Court of \
   Appeal resolution, and recent legislative amendments that may change the \
   analysis.
5. Where relevant, draw on comparative law (Uganda, Tanzania, South Africa, \
   India) to illuminate the Kenyan position.
6. Use proper legal terminology throughout but ALWAYS follow technical terms \
   with a plain-English explanation in parentheses.
7. Structure complex answers with clear headings: Legal Framework → Judicial \
   Interpretation → Practical Implications → Unsettled Areas → Key Takeaways.

COURT HIERARCHY (always reference in this order of authority):
  Supreme Court of Kenya → Court of Appeal → High Court (Constitutional & \
  Family Divisions) → Employment & Labour Relations Court → Environment & \
  Land Court → Magistrate Courts

CITATION FORMAT: Use [Case Name, Court, Year, Petition/Case No.] for judgments \
and [Cap. X, s. Y] or [Article Z, Constitution 2010] for statutes.

Never truncate an analysis. If a legal area is complex, fully cover it.\
"""

# Used in RAG mode
RAG_SYSTEM_PROMPT = """\
You are an expert Kenyan legal analyst with deep mastery of the Constitution of \
Kenya 2010, Acts of Parliament, court judgments across all levels of the \
judiciary, Kenya Gazette notices, and East African legal frameworks.

GROUNDING RULE: Your analysis must be anchored in the provided source documents. \
Every factual or legal claim you make must cite a [Source N] reference. Do not \
invent citations or case names — if the sources do not cover a point, say so \
explicitly and flag it clearly.

DEPTH MANDATE — Every response must:
1. Quote or closely paraphrase the exact statutory/constitutional text from the \
   sources, citing each [Source N].
2. Trace the precedent chain visible in the sources — for each case cite: court \
   level, year, case number, principle established, and how the principle was \
   applied or distinguished in later decisions also visible in the sources.
3. Provide multi-angle analysis: (a) black-letter law from the sources, \
   (b) judicial application from the sources, (c) any dissenting or scholarly \
   commentary visible in the sources, (d) practical real-world implications.
4. Flag contradictions between sources, unsettled areas, and any indication in \
   the sources that the law has recently changed.
5. Structure complex answers: Legal Framework → Judicial Interpretation → \
   Practical Implications → Unsettled Areas / Gaps in Sources → Key Takeaways.

COURT HIERARCHY: Supreme Court → Court of Appeal → High Court → Specialist \
Courts → Magistrate Courts.

CITATION FORMAT:
  - Statutory: [Source N: Article/Section text]
  - Case law: [Source N: Case Name, Court, Year]

Never truncate. Cover everything visible in the sources.\
"""

# ─── Query Templates ──────────────────────────────────────────────────────────

QUERY_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## User's Question:
{query}

## Response Instructions:
- Base your answer ONLY on the provided sources above.
- Cite each source using [Source N] for every legal claim.
- Open with the most directly relevant statutory provision or constitutional \
  article (quote the exact text).
- Trace the full precedent chain visible in the sources.
- Provide a multi-angle analysis: legal text → judicial application → \
  practical effect → unsettled areas.
- Use headings to structure complex answers.
- If the sources are insufficient to fully answer the question, clearly state \
  what is covered and what requires further research.
- End with 1–2 sentences summarising the most critical point for a \
  non-lawyer to understand.

## Answer:"""

DIRECT_QUERY_TEMPLATE = """\
## User's Question:
{query}

## Response Instructions:
- Open by citing the exact Article/Section (and its wording) most central to \
  the question.
- Trace the full precedent chain: for each case state the court, year, case \
  number, the principle it established, and how later courts applied or \
  distinguished it.
- Provide multi-angle analysis: (a) black-letter law, (b) judicial application, \
  (c) practical implications, (d) unsettled or contested areas.
- Use structured headings for anything with more than two sub-points.
- If you are uncertain about a specific detail (e.g. a case number), say so \
  explicitly — do not guess.
- End with a plain-English summary of the most critical point.

## Answer:"""

CASE_ANALYSIS_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Case / Topic to Analyse:
{query}

## Structured Analysis Required:
Write a thorough legal analysis with ALL of the following sections:

### 1. Background & Facts
Key parties, procedural history, and factual matrix — cite [Source N].

### 2. Legal Issues
Enumerate each distinct legal question before the court.

### 3. Applicable Legal Framework
Statutes, constitutional provisions, and prior case law the court relied on \
— cite [Source N] for each.

### 4. Court's Decision (Holding)
The outcome on each issue, with the court's reasoning — cite [Source N].

### 5. Ratio Decidendi
The binding legal principle(s) extracted from the decision.

### 6. Obiter Dicta
Notable observations that are persuasive but not binding.

### 7. Jurisprudential Significance
Impact on Kenyan law: does it settle, reverse, or complicate prior \
jurisprudence? Cite [Source N].

### 8. Critique / Commentary
Any scholarly or judicial criticism; unresolved tensions the decision creates.

### 9. Subsequent Application
How later courts (visible in sources) applied, distinguished, or departed from \
this decision — cite [Source N].

Cite all sources using [Source N] format.

## Analysis:"""

DIRECT_CASE_ANALYSIS_TEMPLATE = """\
## Case / Topic to Analyse:
{query}

## Structured Analysis Required — provide ALL sections:

### 1. Background & Facts
### 2. Legal Issues
### 3. Applicable Legal Framework (cite specific Articles, Acts, and cases)
### 4. Court's Decision & Reasoning
### 5. Ratio Decidendi
### 6. Obiter Dicta (if notable)
### 7. Jurisprudential Significance
### 8. Critique / Unresolved Questions
### 9. Subsequent Application in Kenyan courts (if known)

For every case cited: state the court level, year, case/petition number, and \
the specific principle it established. If you are uncertain about a detail, \
flag it explicitly.

## Analysis:"""

DOCUMENT_DRAFTING_TEMPLATE = """\
## Relevant Legal Sources:
{context}

---

## Drafting Request:
{query}

## Drafting Instructions:
- Follow standard Kenyan legal drafting conventions and applicable statutes \
  — cite [Source N] for each statutory requirement incorporated.
- Include ALL mandatory clauses required by Kenyan law for this document type.
- After each key clause, add a brief annotation (in square brackets) \
  explaining the statutory basis and why the clause is required.
- Flag any clauses that require customisation with [CUSTOMISE: reason].
- Flag any areas where professional legal review is essential before execution.
- End with a checklist of steps required to execute / register / give legal \
  effect to the document under Kenyan law.

## Draft:"""

DIRECT_DRAFTING_TEMPLATE = """\
## Drafting Request:
{query}

## Drafting Instructions:
- Follow standard Kenyan legal drafting conventions.
- Cite the specific Act, Section, or Regulation that governs each clause.
- Include ALL mandatory clauses required by Kenyan law.
- Annotate each key clause with its statutory basis in square brackets.
- Flag customisation points with [CUSTOMISE: reason].
- Flag areas requiring professional review.
- End with an execution/registration checklist.

## Draft:"""

DEEP_RESEARCH_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Research Topic:
{query}

## Scholarly Analysis Required:

Write a comprehensive legal research memorandum with ALL of the following \
sections. Each section should be substantive — aim for the depth of a \
High Court judgment or law review article.

---

### I. Executive Summary (3–5 sentences)
The core legal position, key authority, and most critical practical implication.

### II. Legislative & Constitutional Framework
Full text of the governing Articles / Sections. Trace their history: original \
enactment → amendments → current form. Cite [Source N] for each provision.

### III. Judicial Interpretation & Precedent Chain
A chronological analysis of how courts have interpreted this area of law, \
starting from the earliest authority visible in the sources to the most recent. \
For each judgment: court level, year, case number, facts, holding, and principle \
established. Cite [Source N].

### IV. Conflicting Authorities & Unsettled Areas
Where courts have reached different conclusions, summarise each line of \
authority and explain why the conflict exists. Is there a Supreme Court \
pronouncement that resolves it? If not, what are the competing arguments?

### V. Comparative Perspective
How do Uganda, Tanzania, South Africa, or India (as applicable and visible in \
sources) approach this area? Does the comparative position support or undermine \
the Kenyan approach?

### VI. Practical Implications
For individuals / companies / government: what does this legal position mean in \
practice? Include compliance requirements, time limits, penalties, and available \
remedies.

### VII. Recent Developments
Any statutory amendments, recent judgments, or government policy shifts (visible \
in sources) that affect the analysis.

### VIII. Conclusion & Recommendations
A clear statement of the law as it currently stands, any reform recommendations \
where the law is inadequate, and suggested next steps for a person affected by \
this issue.

---

Cite all sources using [Source N] format throughout.

## Memorandum:"""

DIRECT_DEEP_RESEARCH_TEMPLATE = """\
## Research Topic:
{query}

## Scholarly Analysis Required:

Write a comprehensive legal research memorandum covering:

### I. Executive Summary
### II. Legislative & Constitutional Framework
### III. Judicial Interpretation & Precedent Chain (chronological)
### IV. Conflicting Authorities & Unsettled Areas
### V. Comparative Perspective (East Africa / Commonwealth)
### VI. Practical Implications
### VII. Recent Developments
### VIII. Conclusion & Recommendations

For every case cited: court level, year, case/petition number, facts, holding, \
and principle established. Flag any details you are uncertain about explicitly.

## Memorandum:"""

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
- Questions should cover: (1) a practical application, (2) an exception or \
  edge case, (3) a related but distinct legal area
- Return ONLY the 3 questions, one per line, no numbering, no preamble

Questions:"""


# ─── Petition Drafting Templates ─────────────────────────────────────────────

PETITION_DRAFTING_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Petition Request:
{query}

## Draft a Constitutional Petition with all of the following sections:

### Preamble
IN THE HIGH COURT OF KENYA
AT [STATION]
CONSTITUTIONAL PETITION NO. ___ OF ____

IN THE MATTER OF THE CONSTITUTION OF KENYA 2010
AND IN THE MATTER OF [brief subject matter]

BETWEEN:
[PETITIONER NAME] — PETITIONER
AND
[RESPONDENT NAME] — RESPONDENT

---

### Part 1: Locus Standi (Article 22 CoK)
State the petitioner's standing to bring the petition under Article 22(1)–(2). \
Is this an individual, a public interest petitioner, or a group? Cite [Source N] \
where relevant.

### Part 2: Constitutional Provisions Alleged to be Violated
List each Article breached, quoting its text, and explain the nature of the breach.

### Part 3: Factual Background
Set out the material facts chronologically. Number each paragraph.

### Part 4: Legal Arguments
For each constitutional breach: (a) state the provision, (b) cite supporting \
case law [Source N], (c) explain how the facts constitute a breach.

### Part 5: Reliefs Sought (Article 23 CoK)
List specific reliefs: declarations, orders of mandamus/certiorari/prohibition, \
conservatory orders, damages, costs. Tie each relief to Article 23(3)(a)–(f).

### Part 6: Certificate of Urgency (if applicable)
State grounds for urgency; cite the threshold test from *Gatirau Peter Munya v \
Dickson Mwenda Kithinji* [2014] KECA.

---
Flag customisation points with [CUSTOMISE: reason]. Cite all sources using [Source N].

## Draft:"""

DIRECT_PETITION_DRAFTING_TEMPLATE = """\
## Petition Request:
{query}

## Draft a full Constitutional Petition (Article 22/258 CoK) including:
### Preamble (Court, Parties, Matter)
### Part 1: Locus Standi — Article 22(1)/(2)
### Part 2: Constitutional Provisions Alleged Violated (quote each Article)
### Part 3: Factual Background (numbered paragraphs)
### Part 4: Legal Arguments (provision + case law + application to facts)
### Part 5: Reliefs Sought under Article 23(3)(a)–(f)
### Part 6: Certificate of Urgency (if applicable)

Annotate each section with the statutory/constitutional basis. Flag \
customisation points with [CUSTOMISE: reason].

## Draft:"""

# ─── Judicial Review Templates ────────────────────────────────────────────────

JUDICIAL_REVIEW_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Judicial Review Request:
{query}

## Structured Judicial Review Analysis (Order 53 CPR; s. 8 Law Reform Act Cap. 26):

### 1. Preliminary: Is Judicial Review Available?
Does this matter involve a public law decision by a public body? Cite [Source N].

### 2. Time Limitation
Has the application been brought promptly and within 3 months? State the date \
of the impugned decision and calculate the timeline.

### 3. Ground 1 — Illegality
Did the decision-maker act outside their statutory powers (ultra vires)? \
Cite the empowering statute [Source N] and Kenyan case law on illegality.

### 4. Ground 2 — Irrationality (Wednesbury Unreasonableness)
Was the decision so unreasonable that no reasonable authority could have made it? \
Apply the test from *Council of Civil Service Unions v Minister for Civil Service* [1985] \
as received in Kenyan courts [Source N].

### 5. Ground 3 — Procedural Impropriety
Were the rules of natural justice breached? (a) Audi alteram partem — was the \
applicant heard? (b) Nemo judex in causa sua — was there apparent bias? \
Cite [Source N] for each sub-ground.

### 6. Legitimate Expectations
Were any substantive or procedural legitimate expectations defeated? [Source N]

### 7. Remedies Available
**Certiorari** (quash the decision) / **Mandamus** (compel performance) / \
**Prohibition** (prevent future breach) / **Declaration** / **Injunction**. \
State which remedy is appropriate and why.

### 8. Conservatory / Stay Order
Grounds for interlocutory relief pending the main application.

Cite all sources using [Source N].

## Analysis:"""

DIRECT_JUDICIAL_REVIEW_TEMPLATE = """\
## Judicial Review Request:
{query}

## Structured Analysis — Order 53 CPR / s.8 Law Reform Act (Cap. 26):

### 1. Availability of Judicial Review
### 2. Time Limitation (promptly & within 3 months)
### 3. Ground 1: Illegality (ultra vires — cite empowering statute)
### 4. Ground 2: Irrationality (Wednesbury test — cite Kenyan authority)
### 5. Ground 3: Procedural Impropriety (natural justice — audi alteram partem & nemo judex)
### 6. Legitimate Expectations
### 7. Remedies (certiorari / mandamus / prohibition / declaration)
### 8. Conservatory Relief

For every case cited state: court level, year, case number, and the specific \
principle applied.

## Analysis:"""

# ─── Devolution & County Law Templates ───────────────────────────────────────

DEVOLUTION_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Devolution / County Law Question:
{query}

## Devolution Analysis Framework (Chapter 11 CoK; Fourth Schedule):

### 1. Legal Framework
Applicable constitutional provisions: Articles 6, 174–200, Fourth Schedule. \
Quote the relevant text from [Source N].

### 2. Fourth Schedule Classification
Is the function in question listed in Part 1 (national) or Part 2 (county) of \
the Fourth Schedule? If it spans both, identify the point of intersection. \
Cite [Source N].

### 3. Concurrent / Overlapping Functions
Where both levels have competence, apply the supremacy rule under Article 191: \
(a) conflict with national legislation acting within its mandate → national law \
prevails; (b) national legislation that unnecessarily limits county authority → \
may be unconstitutional. Cite relevant Intergovernmental Relations Act provisions \
[Source N].

### 4. Relevant Institutional Framework
- Intergovernmental Relations Act, No. 2 of 2012
- County Governments Act, No. 17 of 2012
- Public Finance Management Act (county fund provisions)
- Relevant sector legislation (health, land, education, etc.) [Source N]

### 5. Judicial Treatment
How have courts resolved similar national–county competence disputes? \
Cite [Source N] for each case.

### 6. Practical Resolution
What practical steps are available to resolve the dispute or assert the \
county's rights?

## Analysis:"""

DIRECT_DEVOLUTION_TEMPLATE = """\
## Devolution / County Law Question:
{query}

## Devolution Analysis Framework:

### 1. Legal Framework (Chapter 11, Arts 174–200, Fourth Schedule CoK)
### 2. Fourth Schedule Classification (Part 1 national / Part 2 county)
### 3. Concurrent Functions & Article 191 Supremacy Rule
### 4. Relevant Statutes (County Governments Act, IGA 2012, PFM Act, sector laws)
### 5. Judicial Treatment of National–County Competence Disputes
### 6. Practical Resolution Pathway

For cases cited state court level, year, case number, and the devolution \
principle established.

## Analysis:"""

# ─── Statute Cross-Reference Templates ───────────────────────────────────────

CROSS_REFERENCE_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Statutory Cross-Reference Request:
{query}

## Statutory Relationship Map:

### 1. Parent Act(s)
Identify the primary/parent statute(s) governing this area. Quote the long title \
and the relevant sections that authorise subsidiary legislation or cross-reference \
other Acts [Source N].

### 2. Subsidiary Legislation
List all Legal Notices, Regulations, Rules, and Orders made under the parent Act(s) \
that are relevant to the query. For each: LN number, year, subject matter [Source N].

### 3. Related Acts (Must Be Read Together)
Identify complementary Acts that must be considered alongside the parent Act. \
For each, explain: (a) the relationship (it amends / supplements / provides \
definitions for / conflicts with the parent Act), and (b) which specific sections \
interact [Source N].

### 4. Conflict Resolution Rules
Where Acts contradict each other, apply: (a) later Act prevails (leges posteriores \
priores contrarias abrogant), (b) specific Act prevails over general Act, or \
(c) Article 259(1)(b) purposive interpretation. Cite Kenyan case law on statutory \
conflict [Source N].

### 5. Definitions & Interpretation
Flag key terms that are defined differently across the related statutes — \
this is a common source of legal disputes.

### 6. Practical Reading Guide
Step-by-step guidance on how to navigate the statutory web for this specific matter.

Cite all sources using [Source N].

## Cross-Reference Map:"""

DIRECT_CROSS_REFERENCE_TEMPLATE = """\
## Statutory Cross-Reference Request:
{query}

## Statutory Relationship Map:

### 1. Parent Act(s) — long title, relevant authorising sections
### 2. Subsidiary Legislation (LNs, Regulations, Rules, Orders)
### 3. Related Acts (must read together — state relationship & interacting sections)
### 4. Conflict Resolution Rules (leges posteriores, lex specialis, Art. 259 purposive)
### 5. Definitions & Interpretation Conflicts
### 6. Practical Reading Guide

For every statute cited include: Cap. number or year of enactment, and the \
relevant section numbers.

## Cross-Reference Map:"""

# ─── Plain Language / Access to Justice Templates ─────────────────────────────

PLAIN_LANGUAGE_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Question (Plain Language Mode — Article 48 CoK):
{query}

## Plain-Language Legal Explanation:

Write for a self-represented litigant with no legal training. You MUST:
1. **Never use unexplained legal jargon.** If a legal term is unavoidable, \
   immediately explain it in simple English in brackets.
2. Use short sentences and simple words.
3. Structure the answer as a story: "Here is what the law says → Here is what \
   this means for you → Here is what you can do."
4. Use numbered lists and bullet points for steps.
5. Include specific practical steps (which court, what forms, what fees, \
   time limits) drawn from [Source N].
6. End with a section: **When You Should See a Lawyer** — describe situations \
   where professional help is essential and list where to get it for free:
   - Kituo Cha Sheria: 0722 314 508
   - FIDA Kenya: 0720 904 065
   - LSK Pro Bono Programme: 0703 874 481

Cite sources as [Source N] where helpful, but do not let citations interrupt \
readability.

## Plain-Language Explanation:"""

DIRECT_PLAIN_LANGUAGE_TEMPLATE = """\
## Question (Plain Language Mode — Article 48 CoK):
{query}

## Plain-Language Legal Explanation:

Write for a self-represented litigant with no legal training:
- **What the law says** (quote the relevant provision simply)
- **What this means for you** (practical real-world impact)
- **What you can do** (numbered step-by-step guide)
- **Time limits you must know**
- **Costs and fees involved**
- **When you must see a lawyer** (and free legal aid contacts)

Never use unexplained jargon. Short sentences. Simple words.

## Explanation:"""

# ─── Swahili Query Templates ──────────────────────────────────────────────────

SWAHILI_TEMPLATE = """\
## Vyanzo vya Kisheria Vilivyopatikana:
{context}

---

## Swali (Kiswahili):
{query}

## Maelekezo ya Jibu:
Jibu katika Kiswahili sanifu. Ufafanuzi lazima:
1. Taja sheria au Katiba inayohusika ([Chanzo N]) — nunuu maandishi halisi.
2. Eleza jinsi mahakama zimetekeleza sheria hiyo.
3. Toa maelezo ya vitendo (hatua za kufuata, muda wa kisheria, gharama).
4. Tumia lugha rahisi inayoeleweka kwa mtu ambaye si mwanasheria.
5. Mwishowe: **Unapaswa Kuona Mwanasheria Wakati** — na nambari za msaada wa kisheria \
   bila malipo:
   - Kituo Cha Sheria: 0722 314 508
   - FIDA Kenya: 0720 904 065
   - LSK: 0703 874 481

Rejelea vyanzo kwa [Chanzo N].

## Jibu:"""

DIRECT_SWAHILI_TEMPLATE = """\
## Swali (Kiswahili):
{query}

## Maelekezo ya Jibu:
Jibu katika Kiswahili sanifu:
1. Sheria inayohusika (taja sehemu au Ibara halisi)
2. Jinsi mahakama zimetekeleza sheria hiyo
3. Hatua za vitendo (nini ufanye, muda gani, wapi uende)
4. Gharama na ada za mahakama
5. Unapaswa Kuona Mwanasheria Wakati

Tumia lugha rahisi. Epuka maneno magumu ya kisheria bila maelezo.

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

        # Try to set up RAG retrieval — fall back to direct mode if unavailable
        try:
            from src.retrieval.retrieval_pipeline import RetrievalPipeline
            self.retrieval = RetrievalPipeline()
            from src.embedding.embedding_service import EmbeddingService
            es = EmbeddingService()
            info = es.get_collection_info()
            if "error" not in info:
                self._rag_available = True
                logger.info("RAG mode active — vector DB connected with documents")
            else:
                logger.info("Direct LLM mode — vector DB has no collection yet")
        except Exception as e:
            logger.info(f"Direct LLM mode — RAG unavailable: {e}")

    # ── RAG Templates ──────────────────────────────────────────────────────────

    _RAG_TEMPLATES = {
        "research": QUERY_TEMPLATE,
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
        temperature: float = 0.1,
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
                     Injected before the current message so the LLM can do
                     multi-turn follow-ups.
            temperature: LLM temperature (lower = more factual)
            max_tokens: Maximum generation length
        """
        history = history or []

        if self._rag_available:
            return self._generate_rag(
                query, mode, document_type, court,
                history, temperature, max_tokens
            )
        else:
            return self._generate_direct(
                query, mode, history, temperature, max_tokens
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

    # ── Internal: RAG Generation ───────────────────────────────────────────────

    def _generate_rag(
        self, query, mode, document_type, court,
        history, temperature, max_tokens
    ) -> dict:
        """Generate a response grounded in retrieved source documents."""
        # Retrieve relevant context
        context = self.retrieval.retrieve_for_context(
            query=query,
            document_type=document_type,
            court=court,
        )

        if not context:
            # No relevant documents found — fall back to direct mode
            logger.info("No RAG context found — falling back to direct mode")
            return self._generate_direct(query, mode, history, temperature, max_tokens)

        template = self._RAG_TEMPLATES.get(mode, QUERY_TEMPLATE)
        user_prompt = template.format(context=context, query=query)

        messages = self._build_messages(RAG_SYSTEM_PROMPT, history, user_prompt)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = completion.choices[0].message.content

            # Extract source metadata for the frontend
            raw_results = self.retrieval.retrieve(
                query=query, document_type=document_type, court=court,
            )
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

            follow_up_questions = self._generate_follow_up_questions(query)

            return {
                "response": response_text,
                "sources": sources,
                "mode": mode,
                "model": self.model,
                "rag_used": True,
                "follow_up_questions": follow_up_questions,
                "tokens_used": {
                    "prompt": completion.usage.prompt_tokens,
                    "completion": completion.usage.completion_tokens,
                    "total": completion.usage.total_tokens,
                },
            }
        except Exception as e:
            logger.error(f"RAG generation failed: {e}")
            return self._generate_direct(query, mode, history, temperature, max_tokens)

    # ── Internal: Direct Generation ────────────────────────────────────────────

    def _generate_direct(self, query, mode, history, temperature, max_tokens) -> dict:
        """Generate a response using direct LLM knowledge (no RAG)."""
        template = self._DIRECT_TEMPLATES.get(mode, DIRECT_QUERY_TEMPLATE)
        user_prompt = template.format(query=query)

        messages = self._build_messages(SYSTEM_PROMPT, history, user_prompt)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = completion.choices[0].message.content
            follow_up_questions = self._generate_follow_up_questions(query)

            return {
                "response": response_text,
                "sources": [],
                "mode": mode,
                "model": self.model,
                "rag_used": False,
                "follow_up_questions": follow_up_questions,
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

    def _build_messages(
        self,
        system_prompt: str,
        history: list[dict],
        current_user_prompt: str,
    ) -> list[dict]:
        """
        Build the full messages array for the LLM call.

        Structure:
          [system] → [history turns…] → [current user turn]

        History items must have keys 'role' ('user' | 'assistant') and 'content'.
        """
        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Inject prior conversation turns (capped to last 10 to control token use)
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
        Returns an empty list on failure so it never breaks the main response.
        """
        try:
            prompt = FOLLOWUP_TEMPLATE.format(query=query)
            completion = self.client.chat.completions.create(
                model=self.model,
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
