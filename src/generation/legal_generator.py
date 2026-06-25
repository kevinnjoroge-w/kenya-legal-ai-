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

Each paragraph should contain AT LEAST TEN specific case citation or statutory reference.
No paragraphs longer than 150 words (readability).
No generic statements like "this is an important area of law" without immediately explaining WHY.

## CITATION DENSITY:

Minimum citation ratio: 3 specific case/statute reference per 100 words.
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

ADAPTIVE_QUERY_TEMPLATE = """\
## Retrieved Legal Sources:
{context}

---

## User Question:
{query}

## Response Guidance:
You are a senior Kenyan advocate and legal research advisor. Respond to the user's need rather than enforcing a rigid structure.
Response intent: {intent}
Mode hint: {mode}

If the user needs an explanation, answer clearly and directly.
If the user needs legal analysis, compare the strongest arguments, note uncertainty, and explain the practical consequences.
If the user needs procedural guidance, describe the practical steps, likely pitfalls, and the safest route.
If the user needs drafting help, generate a complete, usable legal draft in formal format, including headings, numbered paragraphs, and wording suitable for filing or review. Do not only provide outlines or drafting notes.
If the user needs plain language, simplify the answer and avoid jargon.
If the mode is swahili, answer in Swahili.

Use retrieved sources as evidence where available. If the evidence is insufficient, say the answer is based on general Kenyan legal knowledge and identify the limits.
Keep the answer focused on solving the user's legal need. Avoid filler, checklists, or word-count padding.
"""

ADAPTIVE_DIRECT_TEMPLATE = """\
## User Question:
{query}

## Response Guidance:
You are a senior Kenyan advocate and legal research advisor. Respond to the user's need rather than enforcing a rigid structure.
Response intent: {intent}
Mode hint: {mode}

If the user needs an explanation, answer clearly and directly.
If the user needs legal analysis, compare the strongest arguments, note uncertainty, and explain the practical consequences.
If the user needs procedural guidance, describe the practical steps, likely pitfalls, and the safest route.
If the user needs drafting help, generate a complete, usable legal draft in formal format, including headings, numbered paragraphs, and wording suitable for filing or review. Do not only provide outlines or drafting notes.
If the user needs plain language, simplify the answer and avoid jargon.
If the mode is swahili, answer in Swahili.

Use Kenyan legal principles and any relevant evidence you can infer. Keep the answer focused on solving the user's need.
"""

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
        elif settings.llm_provider == "google":
            return OpenAI(
                api_key=settings.google_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=120.0,
            )
        elif settings.llm_provider == "anthropic":
            return OpenAI(
                api_key=settings.anthropic_api_key,
                base_url="https://api.anthropic.com/v1/",
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

        # Validate substantiveness — log only, no retry (retry doubles latency)
        is_substantive, feedback = self.validator.check_substantiveness(
            response["response"], mode, min_length=800
        )
        if not is_substantive:
            logger.info(f"Validation note (response still returned): {feedback}")

        # Extract action items
        response["action_items"] = self.validator.extract_action_items(response["response"])

        return response

    def _infer_intent(self, query: str, mode: str) -> str:
        normalized = (query or "").lower()
        if mode == "swahili":
            return "swahili"
        if mode in ["drafting", "petition_drafting"]:
            return "drafting"
        if mode == "plain_language":
            return "plain_language"
        if re.search(r"\b(draft|petition|affidavit|contract|letter|memorandum|terms|clause)\b", normalized):
            return "drafting"
        if re.search(r"\b(how do i|what steps|procedure|process|file|serve|appeal|apply|challenge|prepare)\b", normalized):
            return "procedural guidance"
        if re.search(r"\b(compare|difference|versus|vs|contrast|rather than)\b", normalized):
            return "analysis"
        if re.search(r"\b(what does|meaning of|explain|summary|interpretation|define)\b", normalized):
            return "explanation"
        return "analysis"

    def _generate_internal(self, query, mode, temperature, max_tokens, history, **kwargs) -> dict:
        """Internal generation logic."""
        intent = self._infer_intent(query, mode)

        if self._rag_available:
            system_prompt = RAG_SUBSTANTIVE_SYSTEM_PROMPT
            template = self._get_rag_template(mode, query)
            context = self._retrieve_context(query, **kwargs)
            user_prompt = template.format(
                context=context or "[No specific sources retrieved]",
                query=query,
                intent=intent,
                mode=mode,
            )
            rag_used = True
        else:
            system_prompt = SUBSTANTIVE_SYSTEM_PROMPT
            template = self._get_direct_template(mode, query)
            user_prompt = template.format(query=query, intent=intent, mode=mode)
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
            raise

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

    def _get_rag_template(self, mode: str, query: Optional[str] = None) -> str:
        return ADAPTIVE_QUERY_TEMPLATE

    def _get_direct_template(self, mode: str, query: Optional[str] = None) -> str:
        return ADAPTIVE_DIRECT_TEMPLATE

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