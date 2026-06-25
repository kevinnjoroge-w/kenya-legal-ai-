import { Link } from "react-router-dom";
import { PageHeader } from "../components/PageHeader.tsx";
import { PRICING } from "../content.ts";

const FAQ = [
  {
    q: "Is there really a free plan?",
    a: "Yes. The Free plan is free forever and includes 20 research queries a month — enough to get a feel for grounded legal research.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Absolutely. Paid plans are month-to-month and you can cancel from your account at any time, no questions asked.",
  },
  {
    q: "Is this a substitute for a lawyer?",
    a: "No. Kenya Legal AI is a research tool. It speeds up your work but does not replace advice from a qualified Kenyan advocate.",
  },
];

export function PricingPage() {
  return (
    <>
      <PageHeader
        eyebrow="Pricing"
        title="Simple, transparent pricing"
        subtitle="Start free. Upgrade when your practice needs more. No hidden fees."
      />

      <section className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PRICING.map((tier) => (
            <div
              key={tier.name}
              className={`relative flex flex-col rounded-2xl border p-7 ${
                tier.highlighted
                  ? "border-brand-500 bg-white shadow-card ring-2 ring-brand-500/30"
                  : "border-brand-100 bg-white shadow-soft"
              }`}
            >
              {tier.highlighted && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-gold-400 to-gold-500 px-4 py-1 text-xs font-bold text-brand-900">
                  Most popular
                </span>
              )}
              <h3 className="font-serif text-xl font-bold text-brand-800">
                {tier.name}
              </h3>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="font-serif text-4xl font-extrabold text-brand-700">
                  {tier.price}
                </span>
                {tier.period && (
                  <span className="text-sm text-slate-500">{tier.period}</span>
                )}
              </div>
              <p className="mt-3 text-sm text-slate-600">{tier.blurb}</p>

              <ul className="mt-6 flex-1 space-y-3">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-slate-700">
                    <span className="mt-0.5 text-brand-600">✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              {tier.name === "Custom" ? (
                <a
                  href="mailto:sales@kenyalegal.ai?subject=Custom%20plan%20enquiry"
                  className="btn-ghost mt-7 w-full"
                >
                  {tier.cta}
                </a>
              ) : (
                <Link
                  to="/signup"
                  className={`mt-7 w-full ${
                    tier.highlighted ? "btn-primary" : "btn-ghost"
                  }`}
                >
                  {tier.cta}
                </Link>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="bg-brand-50/60 py-16">
        <div className="mx-auto max-w-3xl px-5 sm:px-8">
          <h2 className="text-center font-serif text-3xl font-bold text-brand-800">
            Frequently asked questions
          </h2>
          <div className="mt-10 space-y-4">
            {FAQ.map((item) => (
              <div key={item.q} className="card">
                <h3 className="font-serif text-lg font-bold text-brand-800">
                  {item.q}
                </h3>
                <p className="mt-2 text-sm text-slate-600">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
