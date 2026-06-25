/**
 * Canonical plan definitions — the single source of truth for billing tiers
 * and quota enforcement. Keep `web/src/content.ts` (PRICING) in sync for the
 * marketing/pricing UI.
 */
export interface PlanConfig {
  id: string;
  name: string;
  /** Monthly price in KES. null = custom / talk-to-sales. */
  priceKes: number | null;
  /** Requests allowed per calendar day (UTC). null = unlimited. */
  dailyRequestLimit: number | null;
  blurb: string;
  features: string[];
  highlighted?: boolean;
}

export const PLANS: Record<string, PlanConfig> = {
  Free: {
    id: "Free",
    name: "Free",
    priceKes: 0,
    dailyRequestLimit: 20,
    blurb: "Get started with grounded legal research at no cost.",
    features: [
      "20 requests per day",
      "Research mode",
      "Constitution & Acts search",
      "Citation-backed answers",
    ],
  },
  Student: {
    id: "Student",
    name: "Student",
    priceKes: 139,
    dailyRequestLimit: 100,
    blurb: "For law students and the perpetually curious.",
    features: [
      "100 requests per day",
      "All research modes",
      "Plain-language & Kiswahili",
      "Saved conversations & history",
      "Email support",
    ],
  },
  Individual: {
    id: "Individual",
    name: "Individual",
    priceKes: 359,
    dailyRequestLimit: null,
    blurb: "For practising advocates and busy professionals.",
    features: [
      "Unlimited requests",
      "Case Analysis & Drafting modes",
      "Deep Research mode",
      "Priority responses",
      "Priority support",
    ],
    highlighted: true,
  },
  Custom: {
    id: "Custom",
    name: "Custom",
    priceKes: null,
    dailyRequestLimit: null,
    blurb: "For firms and chambers that need scale and control.",
    features: [
      "Everything in Individual",
      "Team workspaces & seats",
      "SSO & audit logs",
      "Dedicated onboarding",
      "SLA & account manager",
    ],
  },
};

export const DEFAULT_PLAN = "Free";

/** Resolve a stored plan name to its config, falling back to Free. */
export function planFor(name: string | null | undefined): PlanConfig {
  return (name && PLANS[name]) || PLANS[DEFAULT_PLAN];
}
