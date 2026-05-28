# backend/src/legal_generator_v2.py
"""
Enhanced Kenya Legal AI — Substantive Legal Reasoning Engine
=============================================================
IMPROVEMENTS:
  - Enforced depth requirements (min length, citation density, argument complexity)
  - Substantive quality validation (not just buzzword detection)
  - Retry logic: rejects shallow responses automatically
  - Precedent chain enforcement for case analysis
  - Higher token budgets for longer, deeper responses
  - Structured templates that force comprehensive analysis
  - Critical opinion requirement (cannot be neutral)
"""

import logging
import re
from typing import Optional

from openai import OpenAI

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# ─── ENHANCED SYSTEM PROMPTS ───────────────────────────────────────────────────

SUBSTANTIVE_SYSTEM_PROMPT = """\
You are a senior Kenyan advocate with 20 years of experience across constitutional law, 
commercial litigation, and public interest cases. You are NOT writing summaries. You are 
constructing SUBSTANTIVE legal arguments that a practitioner or litigant can actually use.

## DEPTH REQUIREMENTS (Non-Negotiable):

EVERY response must contain:

1. **Precedent Chain** (Minimum 5-7 cases per major point)
   - Not just cite a case; trace HOW courts evolved their interpretation
   - Show which cases distinguished from or overruled predecessors
   - Explain WHY the precedent matters (ratio decidendi, not just facts)
   - Example: "The foundation is *Mitu-Bell v Kenya Airports* [2013], where the Court 
     established X principle. This was extended in *Nyange v AG* [2016] to cover Y scenario. 
     However, *Siaya County v IEBC* [2017] narrowed it on the grounds that Z distinction applies."

2. **Critical Analysis** (Minimum 5 strong opinion per response)
   - Flag weak reasoning in existing law or judgments
   - Point out where the law is poorly drafted or creates perverse incentives
   - Identify where Kenyan courts diverged from Commonwealth precedent without justification
   - Example: "The Court's reasoning in *ABC v XYZ* is problematic because [specific logical flaw]. 
     A stronger interpretation would be [alternative], which aligns with *earlier precedent*."

3. **Practical Implications** (Not theoretical)
   - What does this mean for someone ACTUALLY dealing with this?
   - Where does theory diverge from how courts actually apply the law?
   - What procedural pitfalls exist? What do successful litigants actually do?
   - What documentation must you have?
   - Example: "In theory, the law requires X. In practice, magistrates routinely accept Y without 
     strict proof because Z. However, if you appeal to the High Court, they WILL enforce the strict 
     requirement, so you must prepare for X regardless of local practice."

4. **Alternative Arguments** (Show both sides)
   - Strongest argument FOR the position
   - Strongest argument AGAINST it
   - Which is actually winning in court (data if available)
   - Why reasonable lawyers disagree
   - Example: "The Crown would argue [strong argument A]. The defence counter-argument [strong argument B] 
     is actually prevailing in recent decisions because [precedent], though [counter-counter argument] 
     still has merit if you can distinguish [earlier case]."

5. **Comparative/East African Context** (Where relevant)
   - How do Uganda, Tanzania, or Commonwealth courts handle this?
   - Where is Kenyan law an outlier and why?
   - Are there better-drafted provisions elsewhere we could cite?
   - Example: "The Tanzanian Land Act takes a different approach in Section X, which avoids the 
     ambiguity we see in the Kenyan statute. Kenyan courts could adopt this interpretation 
     if the matter reaches the Supreme Court."

6. **Identified Uncertainty** (Honest about gaps)
   - Where is the law genuinely unsettled?
   - What hasn't been tested in court?
   - What are the plausible interpretations?
   - Where would you hedge your advice to a client?
   - Example: "There is NO binding authority on whether [scenario] falls within the statute. 
     The stronger reading is [interpretation 1] because [reasoning], but [interpretation 2] 
     cannot be dismissed. If this reaches court, I would prepare arguments for both."

## LENGTH & DENSITY STANDARDS:

- **Research/Case Analysis**: 1200–1800 words minimum. Dense with citations.
- **Deep Research**: 2000–3000 words. Scholarly depth with precedent chains.
- **Drafting**: Full draft + detailed annotation (min 800 words total).
- **Plain Language**: 600–1000 words. Simple words, but substantive content.
- **Petition**: 1500–2500 words. Compelling fact narrative + solid legal argument.

Each paragraph should contain AT LEAST ONE specific case citation or statutory reference.
No paragraphs longer than 150 words (readability).
No generic statements like "this is an important area of law" without immediately explaining WHY.

## CITATION DENSITY:

Minimum citation ratio: 1 specific case/statute reference per 100 words.
Cases cited must be named properly (not "a High Court decision") with year and court.
Distinguish between ratio (binding) and obiter (persuasive).

## CRITICAL OPINION REQUIREMENT:

You MUST include at least ONE strong, justified critique in every response:
- "This statute is poorly worded because..."
- "The Court's reasoning in *Case* was weak because..."
- "Kenyan courts have gotten this wrong because..."
- "The practical reality is that the law is ignored, and here's why..."

Do NOT be neutral. You are an advocate, not a law reporter.

## TONE & STYLE:

Speak like a partner explaining to a junior associate or a sophisticated client.
- Short sentences. No purple prose.
- Show your reasoning: "Because X, therefore Y means Z."
- Use embedded citations naturally: "As the Court established in *Mitu-Bell v Kenya Airports*, 
  the principle is..." NOT "Citation: Mitu-Bell v Kenya Airports [2013]."
- End EVERY response with: 
  - The ONE thing they absolutely must understand
  - The ONE practical action they should take
  - One question they should ask a local lawyer to validate your analysis

## STRUCTURE (Flexible, NOT Templated):

Do NOT use bulleted lists unless the content is inherently list-like.
Build arguments in flowing prose. Show your reasoning chain.
Lead with the controlling principle, then apply to facts.
Flag uncertainty and competing interpretations.
End with practical takeaway.

Example structure (NOT a template):
  Paragraph 1: State the core legal principle and why it's the answer to their question.
  Paragraph 2–4: Walk through the precedent chain showing how courts evolved this principle.
  Paragraph 5: Flag where the law is contested or unclear.
  Paragraph 6: Explain the practical reality (what courts/officials actually do).
  Paragraph 7: Include your critical opinion on a weakness or ambiguity.
  Paragraph 8: Comparative note if relevant.
  Final paragraph: Specific, actionable takeaway + one validation question.
"""

RAG_SUBSTANTIVE_SYSTEM_PROMPT = SUBSTANTIVE_SYSTEM_PROMPT + """

## RAG INTEGRATION (For RAG Mode):

You will receive retrieved legal sources. USE them as your primary foundation, but DO NOT 
be limited by them. You already know the Constitution and major Acts; if sources are incomplete, 
seamlessly integrate your own knowledge.

Synthesize, don't list. Don't say "Source 1 says X, Source 2 says Y." Instead: 
"As established in *Mitu-Bell* and reinforced in *Siaya County*, the principle is [synthesized understanding]."

If sources show conflicts, resolve them: "The High Court is split. *Case A* favors interpretation X 
[Source 1], but *Case B* correctly prioritizes Y [Source 2] because the precedent chain from 
*foundational case* supports it."

Cite sources by actual name [Source N] when using direct quotes or specific holdings, but weave them 
into your argument naturally.
"""

# ─── ENHANCED TEMPLATES ────────────────────────────────────────────────────────

SUBSTANTIVE_QUERY_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Your Question:
{query}

## Your Task:
Construct a SUBSTANTIVE legal argument grounded in the sources above and Kenyan law generally. 
This is not a summary. It is a reasoned legal opinion.

Before writing, explicitly think through:
1. What is the PRECISE legal question (often different from what's literally asked)?
2. What precedent chain controls this? (Minimum 2–3 cases per major point)
3. Is the law settled, or are courts split? If split, which line is winning?
4. What is the strongest counterargument, and how do you overcome it?
5. What practical pitfall should they know about?
6. Where is my strongest critique of how the law is written or applied?

## Structure Your Answer As:

Paragraph 1: State the core legal principle directly. Don't bury it.

Paragraphs 2–4: Walk through the precedent chain. Show how courts evolved their interpretation. 
Explain the ratio of each case (WHY it matters) and how it applies to their situation.

Paragraph N-2: Flag where the law is contested, unclear, or poorly drafted. This is your CRITICAL 
OPINION. Don't hedge it.

Paragraph N-1: Explain the practical reality. What do courts/officials actually do? Where does 
theory diverge from practice?

Paragraph N: Comparative note (if relevant) and final takeaway. One specific action they should take. 
One question to ask a local counsel to validate your analysis.

## Minimum Standards (Non-Negotiable):
- Minimum 1200 words
- At least 1 citation per 100 words (precedent chain, not just references)
- At least 1 strong critical opinion
- At least 1 practical example or scenario showing how the law applies
- At least 1 statement of uncertainty or competing interpretation
- No generic statements (every claim is grounded in a case or statute)
- Final paragraph: specific, actionable takeaway

## Answer:"""

SUBSTANTIVE_CASE_ANALYSIS_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Case / Topic to Analyse:
{query}

## Your Task:
Analyze this case or legal position like a senior advocate writing a litigation memo. This is 
NOT a case summary. It is a critical evaluation of reasoning, precedent impact, and practical implications.

## Structure Your Analysis As:

**Section 1: The Core Legal Problem**
State clearly: What was the actual legal issue? What was at stake? What prior law applied?
Ground this in relevant precedent.

**Section 2: Was the Judge's Reasoning Sound?**
- What was the judge's ratio (the reasoning that controls)?
- Is the logic internally consistent? (Flag logical gaps or leaps)
- Did the judge ignore relevant precedent or distinguish it properly?
- Where would you have argued differently?
- Is there a stronger argument buried in the judgment's own logic?

**Section 3: Precedent Impact (Ratio vs. Obiter)**
- What is the BINDING principle from this case (ratio)?
- What is persuasive but not binding (obiter)?
- How does it fit the broader jurisprudence? Does it build on or disrupt earlier law?
- Which earlier cases does it overrule or distinguish? (Trace the chain)
- Could a later court distinguish it? Where is it vulnerable?

**Section 4: Disagreement & Outliers**
- Are there conflicting decisions from other courts on this issue?
- Which line of reasoning is actually winning in practice?
- If Kenyan courts diverged from Commonwealth precedent, is it justified?
- What's the dissent's strongest argument? (If applicable)

**Section 5: Practical Impact**
- What does this case change about how the law is applied?
- What precedent was overturned or narrowed?
- What new liability/risk does it create?
- How are practitioners actually responding?
- What preparation is now required that wasn't before?

**Section 6: Your Critical Opinion**
- Stated plainly: Was this decision correct or problematic? Why?
- If wrong, what was the better reasoning?
- If right, what weaknesses exist in the judge's logic?
- How would you argue this issue if it reaches the Supreme Court?

**Section 7: Lasting Significance**
- Is this case-specific or broadly applicable?
- Is it likely to survive appellate scrutiny?
- Will it be cited 10 years from now, or forgotten?
- What issues does it leave unresolved?

## Minimum Standards:
- Minimum 1200 words
- Precedent chain analyzed (not just cited)
- Your critical opinion clearly stated
- Practical implication explained with example
- Realistic assessment of whether the decision will endure
- No hedging on your own view

## Analysis:"""

SUBSTANTIVE_DEEP_RESEARCH_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Research Topic:
{query}

## Your Task:
Build a COMPREHENSIVE scholarly legal argument. This is research-memo-level depth. 
Think like you're educating a colleague or writing a Supreme Court brief.

Do NOT use rigid structure. Build your argument methodically:

**1. Foundational Principles**
- What is the basic legal principle at stake?
- Where does it come from (statute, common law, constitutional principle)?
- Why does it matter? (What problem does it solve? What values does it protect?)
- How is it defined? (Is there consensus, or is the definition contested?)

**2. Precedent Chain**
- Trace how courts have interpreted this principle over time
- Show which cases built on or distinguished predecessors
- Explain the RATIO (why the case mattered) and OBITER (nice-to-know reasoning)
- Identify the "great cases" vs. the incremental developments
- Show where courts got it right and where they went wrong

**3. Points of Conflict & Unsettled Law**
- Where do Kenyan courts split on interpretation?
- What scenarios remain untested?
- Where has the law not kept pace with social/economic reality?
- What do other East African jurisdictions do differently?
- What do Commonwealth courts say, and is Kenya's approach justified?

**4. Critical Analysis**
- Assess which line of reasoning is stronger (your view, not neutral)
- Flag statutes that are poorly drafted
- Identify precedents that should be overruled
- Point out gaps in the law where Parliament should legislate
- Explain where the law is being ignored in practice and why

**5. Practical Implications**
- What does this mean for someone actually dealing with this?
- Where do theory and practice diverge?
- What documentation/procedure is required?
- What are the common mistakes?
- What's the cheapest/fastest/safest route?

**6. Comparative & Reform Perspective**
- How do other jurisdictions handle this better?
- What reforms would improve the law?
- Are there model provisions or approaches worth citing?
- How should the Supreme Court evolve the jurisprudence?

## Minimum Standards:
- Minimum 2000 words
- Precedent chain analyzed (minimum 4–6 key cases)
- At least 2 competing interpretations discussed
- At least 1 strong critical opinion on weakness in existing law
- Comparative note to other jurisdictions
- Clear identification of unsettled areas
- Practical example showing real-world application
- Reform suggestion (even if speculative)
- No generic statements

## Answer:"""

SUBSTANTIVE_DRAFTING_TEMPLATE = """\
## Relevant Legal Sources:
{context}

---

## Drafting Request:
{query}

## Your Task:
Draft the document (not as a form-filler, but as a lawyer who understands why each clause exists).

For EVERY substantive clause:
- Explain WHY it is necessary (what does it protect against?)
- What problem does it solve?
- What is the user risking if they omit it?
- Where must they customize it to their specific facts?
- What is the strongest counterargument, and how does your clause protect against it?

Use annotations:
- [CUSTOMISE: reason] — flags where the drafter MUST make a strategic choice
- [NOTE: rationale] — explains why this clause is here
- [RISK: consequence] — flags what happens if this clause is missing or weak
- [NEGOTIATE: point] — flags a likely negotiation point

Build the draft like you're advising a sophisticated client. Show your work.

## Minimum Standards:
- Full draft (not outline)
- At least 30% of the word count is annotation/explanation
- Every major clause has a [CUSTOMISE] or [RISK] flag
- At least 1 clause includes a critical opinion ("This is poorly drafted in most agreements because...")
- Precedent cited where relevant (e.g., "Courts in *XYZ v ABC* found that...so this clause protects you against that")
- At least 1 strategic negotiation note

## Draft:"""

SUBSTANTIVE_PETITION_DRAFTING_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## Petition Request:
{query}

## Your Task:
Draft a PERSUASIVE constitutional petition. It must move the Court, not bore it.

The facts must tell a story: Why does this constitutional violation MATTER? What irreparable 
harm flows from it? Why is the petitioner uniquely affected?

The law must reason from sources to conclusion: Show why the Constitution COMPELS the relief 
you seek. Don't just assert "this violates Article X." Explain how, using precedent.

## Structure (Not Rigid, But Informed):

**I. Statement of Facts**
- Open with what matters most (human impact, not chronology)
- Tell the story of how the petitioner got here
- Show the unreasonableness or unfairness of the situation
- Make the Judge WANT the petitioner to win
- Cite specific documents, dates, responses (or lack thereof)

**II. The Constitutional Violation**
- Name the provision(s) breached
- Explain the principle protected by that provision
- Apply that principle to the petitioner's facts
- Show why there is no other adequate remedy
- Distinguish this from cases where courts declined to intervene

**III. The Respondent's Interests**
- Acknowledge (briefly) what the Respondent might argue
- Show why those interests do NOT justify the violation
- Use precedent to show courts have rejected similar arguments
- Propose a remedy that accommodates legitimate Respondent interests

**IV. The Requested Relief**
- Be specific (not "declare that the petitioner's rights were violated")
- Explain why this relief restores the Constitution
- Flag any practical implementation issues and propose solutions

**V. Why This Court Should Act**
- Show how this case clarifies the Constitution
- Explain the broader impact (don't overstate, but be honest)
- Point to unsettled law where the Court's guidance is needed

## Minimum Standards:
- Minimum 1500 words
- Fact narrative is compelling (not just legal)
- At least 3–4 key precedents cited and applied
- At least 1 acknowledgement of counterargument + refutation
- At least 1 reference to international law / comparative constitutional law (if relevant)
- Remedy is specific and feasible
- Critical opinion on the unreasonableness of the government's position is evident
- Emotional resonance (not dry legal writing)

## Draft:"""

# ─── SUBSTANTIVE QUALITY VALIDATION ────────────────────────────────────────────

class SubstantiveValidator:
    """Validates that responses are substantive, not just summaries."""

    @staticmethod
    def check_substantiveness(response_text: str, mode: str, min_length: int = 800) -> tuple[bool, str]:
        """
        Check if response meets substantive standards (not just buzzword detection).
        Returns (is_substantive, feedback).
        """
        issues = []

        # 1. LENGTH CHECK
        if len(response_text) < min_length:
            issues.append(f"Too short ({len(response_text)} chars; need >{min_length})")

        # 2. CITATION DENSITY
        # Minimum 1 case/statute per 100 words
        word_count = len(response_text.split())
        citation_patterns = [
            r'\*[A-Z][a-z\s]+v\s[A-Z][a-z\s]+\*\s?\[?20\d{2}\]?',  # *Case v Case* [Year]
            r'Article\s\d+',  # Article N
            r'Section\s\d+',  # Section N
            r'\b(Constitution|Act|Statute|Rule|Regulation)\b',  # Generic legal doc
            r'\b(the [A-Z][a-z\s]+ Act)\b',  # The X Act
        ]
        citations_found = sum(
            len(re.findall(pattern, response_text, re.IGNORECASE))
            for pattern in citation_patterns
        )
        required_citations = max(3, word_count // 100)
        if citations_found < required_citations:
            issues.append(f"Low citation density ({citations_found} citations for {word_count} words; need >{required_citations})")

        # 3. PRECEDENT CHAIN
        case_citations = re.findall(r'\*[A-Z][a-z\s]+v\s[A-Z][a-z\s]+\*\s?\[20\d{2}\]', response_text, re.IGNORECASE)
        if mode in ["research", "case_analysis", "deep_research"] and len(case_citations) < 2:
            issues.append(f"Missing precedent chain (only {len(case_citations)} cases cited; need ≥2)")

        # 4. CRITICAL OPINION REQUIREMENT
        critical_patterns = [
            r'(however|but|problematic|weak|flawed|poorly drafted|misguided)',
            r'(the court erred|this reasoning is flawed|this interpretation is incorrect)',
            r'(in practice|in reality|courts ignore|practitioners actually)',
        ]
        has_critique = any(
            re.search(pattern, response_text, re.IGNORECASE)
            for pattern in critical_patterns
        )
        if not has_critique:
            issues.append("No critical opinion or honest weakness identified")

        # 5. PRACTICAL APPLICATION
        practical_patterns = [
            r'(in practice|practically speaking|real-world|actually does|actually happens|courts routinely)',
            r'(you should|you must|you need to|the practical step)',
            r'(example|scenario|for instance|this means)',
        ]
        has_practical = any(
            re.search(pattern, response_text, re.IGNORECASE)
            for pattern in practical_patterns
        )
        if not has_practical:
            issues.append("Lacks practical application or real-world examples")

        # 6. REASONING SHOWN (because/therefore logic chains)
        reasoning_patterns = [r'\bbecause\b', r'\btherefore\b', r'\bthis means\b', r'\bthis requires\b']
        reasoning_found = sum(
            len(re.findall(pattern, response_text, re.IGNORECASE))
            for pattern in reasoning_patterns
        )
        if reasoning_found < 3:
            issues.append("Lacks visible reasoning chains (use 'because', 'therefore', 'this means')")

        # 7. ACKNOWLEDGED UNCERTAINTY (for appropriate modes)
        if mode in ["research", "case_analysis", "deep_research"]:
            uncertainty_patterns = [
                r'(uncertain|unclear|not settled|courts split|unsettled)',
                r'(may|might|could|arguably|reasonable argument)',
            ]
            has_uncertainty = any(
                re.search(pattern, response_text, re.IGNORECASE)
                for pattern in uncertainty_patterns
            )
            if not has_uncertainty:
                issues.append("Presents everything as certain when nuance is appropriate")

        # 8. ACTIONABLE CONCLUSION (final paragraph must have action or validation question)
        last_para = response_text.split("\n\n")[-1] if "\n\n" in response_text else response_text[-500:]
        action_patterns = [
            r'(you should|you must|the first step|ask your lawyer|validate with|consider)',
            r'(question to ask|discuss with|seek advice)',
        ]
        has_action = any(
            re.search(pattern, last_para, re.IGNORECASE)
            for pattern in action_patterns
        )
        if not has_action:
            issues.append("No actionable conclusion or validation question in final paragraph")

        # DRAFTING-SPECIFIC CHECKS
        if mode in ["drafting", "petition_drafting"]:
            customize_flags = len(re.findall(r'\[CUSTOMISE:', response_text))
            if customize_flags == 0:
                issues.append("No [CUSTOMISE:] flags for required user decisions")
            annotation_ratio = len(re.findall(r'\[(CUSTOMISE|NOTE|RISK|NEGOTIATE):', response_text)) / max(len(response_text) // 100, 1)
            if annotation_ratio < 0.1:  # Less than 1 annotation per 100 chars
                issues.append("Insufficient annotation/explanation (need ~30% of content as [NOTE:], [CUSTOMISE:], etc.)")

        # VERDICT
        if issues:
            return False, " | ".join(issues[:3])  # Return top 3 issues
        return True, ""

    @staticmethod
    def extract_action_items(response_text: str) -> list[str]:
        """Extract actionable items from response."""
        actions = []
        # Look for first/next steps
        action_pattern = r'(next step|first step|should|must|action|do this|file|petition|contact|call|seek)\s+([^.\n]{10,80})'
        for match in re.finditer(action_pattern, response_text, re.IGNORECASE):
            actions.append(match.group(2).strip())
        return actions[:3]


# ─── ENHANCED GENERATOR ────────────────────────────────────────────────────────

class SubstantiveLegalGenerator:
    """Enhanced generator enforcing substantive legal analysis."""

    def __init__(self):
        settings = get_settings()
        self.model = settings.llm_model
        self.client = self._init_client()
        self.validator = SubstantiveValidator()
        self.retrieval = None
        self._rag_available = False
        self._rag_error = None
        self._try_init_rag()

    def _init_client(self):
        """Initialize LLM client (same as before)."""
        settings = get_settings()
        if settings.llm_provider == "groq":
            return OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=120.0,
            )
        elif settings.llm_provider == "mistral":
            return OpenAI(
                api_key=settings.mistral_api_key,
                base_url="https://api.mistral.ai/v1",
                timeout=120.0,
            )
        else:
            return OpenAI(api_key=settings.openai_api_key, timeout=120.0)

    def _try_init_rag(self):
        """Lazy RAG initialization."""
        try:
            from src.retrieval.retrieval_pipeline import RetrievalPipeline
            self.retrieval = RetrievalPipeline()
            self._rag_available = True
            self._rag_error = None
            logger.info("RAG mode active")
        except Exception as e:
            self._rag_available = False
            self._rag_error = str(e)
            logger.warning(f"RAG unavailable: {e}")

    def generate(
        self,
        query: str,
        mode: str = "research",
        temperature: Optional[float] = None,
        max_tokens: int = 6000,  # INCREASED from 4096
        history: Optional[list[dict]] = None,
        **kwargs
    ) -> dict:
        """
        Generate substantive legal response with quality validation & retry logic.
        
        If response is deemed insufficiently substantive, automatically retry with 
        stricter instructions before returning to user.
        """
        history = history or []

        if temperature is None:
            temperature = 0.5 if mode in ["drafting", "petition_drafting"] else 0.6

        # First attempt
        response = self._generate_internal(
            query, mode, temperature, max_tokens, history, **kwargs
        )

        # Validate substantiveness
        is_substantive, feedback = self.validator.check_substantiveness(
            response["response"], mode, min_length=800
        )

        if not is_substantive:
            logger.warning(f"Response validation failed: {feedback}. Retrying with stricter prompt...")
            response = self._generate_with_retry(
                query, mode, feedback, temperature, max_tokens, history, **kwargs
            )

        # Extract action items
        response["action_items"] = self.validator.extract_action_items(response["response"])

        return response

    def _generate_internal(self, query, mode, temperature, max_tokens, history, **kwargs) -> dict:
        """Internal generation logic."""
        # Build system prompt based on RAG availability
        if self._rag_available:
            system_prompt = RAG_SUBSTANTIVE_SYSTEM_PROMPT
            template = self._get_rag_template(mode)
            context = self._retrieve_context(query, **kwargs)
            user_prompt = template.format(context=context or "[No specific sources retrieved]", query=query)
            rag_used = True
        else:
            system_prompt = SUBSTANTIVE_SYSTEM_PROMPT
            template = self._get_direct_template(mode)
            user_prompt = template.format(query=query)
            rag_used = False

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_prompt},
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response_text = completion.choices[0].message.content

            return {
                "response": response_text,
                "rag_used": rag_used,
                "model": self.model,
                "mode": mode,
            }
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return {
                "response": f"ERROR: {str(e)}",
                "error": str(e),
                "rag_used": rag_used,
                "model": self.model,
            }

    def _generate_with_retry(self, query, mode, feedback, temperature, max_tokens, history, **kwargs) -> dict:
        """Retry generation with explicit instruction to fix validation failures."""
        system_prompt = SUBSTANTIVE_SYSTEM_PROMPT
        template = self._get_direct_template(mode)

        # Build stricter user prompt
        user_prompt = template.format(query=query)
        user_prompt += f"""

## IMPORTANT: Validation Feedback from Previous Attempt

Your previous response was assessed as INSUFFICIENTLY SUBSTANTIVE.

Specific issues:
{feedback}

Please provide a revised, MUCH MORE DETAILED response that addresses these specific gaps:
- Add more precedent chain analysis (trace cases over time, show how reasoning evolved)
- Include critical analysis: flag weak reasoning or poorly drafted laws
- Add practical examples showing how the law actually works
- Acknowledge areas of legal uncertainty or competing interpretations
- End with specific action the user should take
- Ensure EVERY paragraph contains a case/statute reference

This is your opportunity to provide the comprehensive, usable analysis a lawyer would expect.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_prompt},
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=min(temperature + 0.15, 0.9),  # Slightly higher temp for more detail
                max_tokens=int(max_tokens * 1.3),  # Allow more tokens for retry
            )
            response_text = completion.choices[0].message.content

            return {
                "response": response_text,
                "rag_used": self._rag_available,
                "model": self.model,
                "mode": mode,
                "retry_attempted": True,
            }
        except Exception as e:
            logger.error(f"Retry generation failed: {e}")
            return {
                "response": f"ERROR on retry: {str(e)}",
                "error": str(e),
                "rag_used": self._rag_available,
                "model": self.model,
                "retry_attempted": True,
            }

    def _retrieve_context(self, query: str, document_type: Optional[str] = None, court: Optional[str] = None) -> str:
        """Retrieve and format RAG context."""
        if not self._rag_available or not self.retrieval:
            return ""

        try:
            results = self.retrieval.retrieve(query, document_type, court)
            if not results:
                return ""

            context_parts = []
            for i, result in enumerate(results[:5], 1):  # Limit to top 5
                source_info = result.get("document_title", "")
                if result.get("section"):
                    source_info += f" | {result['section']}"
                context_parts.append(f"[Source {i}: {source_info}]\n{result.get('text', '')}")

            return "\n---\n".join(context_parts)
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            return ""

    def _get_rag_template(self, mode: str) -> str:
        """Get RAG-mode template."""
        templates = {
            "research": SUBSTANTIVE_QUERY_TEMPLATE,
            "case_analysis": SUBSTANTIVE_CASE_ANALYSIS_TEMPLATE,
            "drafting": SUBSTANTIVE_DRAFTING_TEMPLATE,
            "deep_research": SUBSTANTIVE_DEEP_RESEARCH_TEMPLATE,
            "petition_drafting": SUBSTANTIVE_PETITION_DRAFTING_TEMPLATE,
        }
        return templates.get(mode, SUBSTANTIVE_QUERY_TEMPLATE)

    def _get_direct_template(self, mode: str) -> str:
        """Get direct-mode template (no RAG)."""
        # Same templates but remove the "## Retrieved Legal Sources:" section
        templates = {
            "research": SUBSTANTIVE_QUERY_TEMPLATE.replace("## Retrieved Legal Sources:\n{context}\n\n---\n\n", ""),
            "case_analysis": SUBSTANTIVE_CASE_ANALYSIS_TEMPLATE,
            "drafting": SUBSTANTIVE_DRAFTING_TEMPLATE.replace("## Relevant Legal Sources:\n{context}\n\n---\n\n", ""),
            "deep_research": SUBSTANTIVE_DEEP_RESEARCH_TEMPLATE,
            "petition_drafting": SUBSTANTIVE_PETITION_DRAFTING_TEMPLATE.replace("## Retrieved Legal Sources:\n{context}\n\n---\n\n", ""),
        }
        return templates.get(mode, SUBSTANTIVE_QUERY_TEMPLATE)

    # ── Convenience Shortcuts ──────────────────────────────────────────────────

    def ask(self, query: str, **kwargs) -> dict:
        """Legal research."""
        return self.generate(query, mode="research", **kwargs)

    def analyze_case(self, query: str, **kwargs) -> dict:
        """Case analysis."""
        return self.generate(query, mode="case_analysis", **kwargs)

    def draft_document(self, query: str, **kwargs) -> dict:
        """Document drafting."""
        return self.generate(query, mode="drafting", max_tokens=7000, **kwargs)

    def draft_petition(self, query: str, **kwargs) -> dict:
        """Constitutional petition."""
        return self.generate(query, mode="petition_drafting", max_tokens=7000, **kwargs)

    def deep_research(self, query: str, **kwargs) -> dict:
        """Deep scholarly research."""
        return self.generate(query, mode="deep_research", max_tokens=8000, **kwargs)


# Backward-compatible alias for older imports.
LegalGenerator = SubstantiveLegalGenerator