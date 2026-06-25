/** Shared marketing content so pages stay consistent. */

export const STATS = [
  { value: "264", label: "Constitutional Articles" },
  { value: "700+", label: "Acts of Parliament" },
  { value: "100K+", label: "Court Judgments" },
];

export const FEATURES = [
  {
    icon: "🏛️",
    title: "Comprehensive Legal Database",
    body: "The Constitution of Kenya 2010, 700+ Acts of Parliament, 100,000+ court judgments from every court, and Kenya Gazette legal notices — all in one place.",
  },
  {
    icon: "🤖",
    title: "RAG-Powered AI",
    body: "Retrieval-Augmented Generation grounds every response in real legal documents. No hallucinations — only verified sources, every time.",
  },
  {
    icon: "📖",
    title: "Citation-Backed Answers",
    body: "Every legal claim is tied to a specific case citation, constitutional article, or statutory provision with a direct source reference.",
  },
  {
    icon: "🔒",
    title: "Ethical by Design",
    body: "Built with legal ethics in mind: mandatory disclaimers, court-hierarchy awareness, and a clear line between settled and debated law.",
  },
  {
    icon: "⚡",
    title: "Multiple Research Modes",
    body: "Research for general Q&A, Case Analysis for deep dives into judgments, and Drafting to generate legal document templates.",
  },
  {
    icon: "🇰🇪",
    title: "Built for Kenya",
    body: "Purpose-built for the Kenyan legal system — local courts, legal terminology, and the unique character of Kenyan jurisprudence.",
  },
];

export const MODES = [
  {
    icon: "🔍",
    title: "Research",
    body: "Ask any question about Kenyan law and get a clear, citation-backed answer in seconds.",
  },
  {
    icon: "📑",
    title: "Case Analysis",
    body: "Dive deep into a specific judgment — holdings, reasoning, and how it sits in the court hierarchy.",
  },
  {
    icon: "✍️",
    title: "Drafting",
    body: "Generate first-draft legal document templates grounded in the relevant statutes.",
  },
];

export const STEPS = [
  {
    n: "1",
    title: "Ask your question",
    body: "Type a legal question in plain English or Kiswahili — no special syntax required.",
  },
  {
    n: "2",
    title: "We retrieve the law",
    body: "The engine searches the Constitution, Acts, and case law for the most relevant passages.",
  },
  {
    n: "3",
    title: "Get a cited answer",
    body: "Receive a grounded answer with every source linked so you can verify and go deeper.",
  },
];

export interface PricingTier {
  name: string;
  price: string;
  period: string;
  blurb: string;
  features: string[];
  cta: string;
  highlighted?: boolean;
}

/**
 * Mirrors the canonical plan definitions in `server/src/lib/plans.ts`.
 * Keep the two in sync — the server enforces the daily request limits.
 */
export const PRICING: PricingTier[] = [
  {
    name: "Free",
    price: "KES 0",
    period: "",
    blurb: "Get started with grounded legal research at no cost.",
    features: [
      "20 requests per day",
      "Research mode",
      "Constitution & Acts search",
      "Citation-backed answers",
    ],
    cta: "Start for free",
  },
  {
    name: "Student",
    price: "KES 139",
    period: "/ month",
    blurb: "For law students and the perpetually curious.",
    features: [
      "100 requests per day",
      "All research modes",
      "Plain-language & Kiswahili",
      "Saved conversations & history",
      "Email support",
    ],
    cta: "Choose Student",
  },
  {
    name: "Individual",
    price: "KES 359",
    period: "/ month",
    blurb: "For practising advocates and busy professionals.",
    features: [
      "Unlimited requests",
      "Case Analysis & Drafting modes",
      "Deep Research mode",
      "Priority responses",
      "Priority support",
    ],
    cta: "Choose Individual",
    highlighted: true,
  },
  {
    name: "Custom",
    price: "Custom",
    period: "",
    blurb: "For firms and chambers that need scale and control.",
    features: [
      "Everything in Individual",
      "Team workspaces & seats",
      "SSO & audit logs",
      "Dedicated onboarding",
      "SLA & account manager",
    ],
    cta: "Talk to sales",
  },
];

export const DISCLAIMER =
  "Kenya Legal AI is a legal research tool and does not constitute legal advice. Always consult a qualified Kenyan advocate for professional legal guidance. Use this tool as a starting point for research, not a replacement for professional counsel.";
