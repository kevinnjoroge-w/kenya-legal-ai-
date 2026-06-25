import { Link } from "react-router-dom";
import { FEATURES, MODES, STATS, STEPS } from "../content.ts";

const EXAMPLES = [
  "What does Article 27 of the Constitution say about equality?",
  "Explain the rights of an accused person under Kenyan law.",
  "What is the process for impeaching a governor in Kenya?",
  "Summarize the Employment Act 2007 provisions on termination.",
];

export function LandingPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500" />
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, #fff 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="relative mx-auto max-w-5xl px-5 py-24 text-center sm:px-8 sm:py-32">
          <span className="badge bg-white/10 text-white border-white/25">
            ⚖️ 🇰🇪 Built for Kenyan Law
          </span>
          <h1 className="mt-6 font-serif text-4xl font-extrabold leading-tight text-white sm:text-6xl">
            Your AI-Powered
            <br />
            <span className="text-gold-400">Legal Research</span> Assistant
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-brand-50/90">
            Query the Constitution, Acts of Parliament, and thousands of court
            judgments with instant, citation-backed answers from Kenya's legal
            framework.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
            <Link to="/signup" className="btn-gold px-7 py-3 text-base">
              Start Researching →
            </Link>
            <Link
              to="/features"
              className="btn px-7 py-3 text-base border border-white/30 bg-white/5 text-white hover:bg-white/10"
            >
              Learn More
            </Link>
          </div>

          <div className="mx-auto mt-16 grid max-w-2xl grid-cols-3 gap-4">
            {STATS.map((s) => (
              <div
                key={s.label}
                className="rounded-2xl border border-white/15 bg-white/10 px-3 py-5 backdrop-blur"
              >
                <div className="font-serif text-2xl font-bold text-gold-400 sm:text-3xl">
                  {s.value}
                </div>
                <div className="mt-1 text-xs text-brand-50/80">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Modes */}
      <section className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
        <div className="text-center">
          <h2 className="font-serif text-3xl font-bold text-brand-800 sm:text-4xl">
            Three ways to research
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-slate-600">
            Pick the mode that fits your task — from a quick question to a full
            case breakdown.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {MODES.map((m) => (
            <div key={m.title} className="card transition hover:shadow-card">
              <div className="grid h-12 w-12 place-items-center rounded-xl bg-brand-50 text-2xl">
                {m.icon}
              </div>
              <h3 className="mt-4 font-serif text-xl font-bold text-brand-800">
                {m.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{m.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-brand-50/60 py-20">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <div className="text-center">
            <h2 className="font-serif text-3xl font-bold text-brand-800 sm:text-4xl">
              How it works
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-slate-600">
              Grounded answers in three steps — no legal-search expertise
              required.
            </p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="card">
                <div className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-brand-700 to-brand-500 font-serif text-lg font-bold text-white">
                  {s.n}
                </div>
                <h3 className="mt-4 font-serif text-lg font-bold text-brand-800">
                  {s.title}
                </h3>
                <p className="mt-2 text-sm text-slate-600">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features grid */}
      <section className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
        <div className="text-center">
          <h2 className="font-serif text-3xl font-bold text-brand-800 sm:text-4xl">
            Why Kenya Legal AI
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-slate-600">
            Everything you need to research Kenyan law with confidence.
          </p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="card transition hover:shadow-card">
              <div className="text-3xl">{f.icon}</div>
              <h3 className="mt-3 font-serif text-lg font-bold text-brand-800">
                {f.title}
              </h3>
              <p className="mt-2 text-sm text-slate-600">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Example queries + CTA */}
      <section className="bg-brand-50/60 py-20">
        <div className="mx-auto max-w-4xl px-5 text-center sm:px-8">
          <h2 className="font-serif text-3xl font-bold text-brand-800 sm:text-4xl">
            Try asking…
          </h2>
          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            {EXAMPLES.map((q) => (
              <Link
                key={q}
                to="/signup"
                className="rounded-xl border border-brand-100 bg-white px-5 py-4 text-left text-sm font-medium text-slate-700 transition hover:border-brand-300 hover:text-brand-700 hover:shadow-soft"
              >
                {q}
              </Link>
            ))}
          </div>
          <div className="mt-12 rounded-3xl bg-gradient-to-br from-brand-700 to-brand-500 px-6 py-12 text-white shadow-card">
            <h3 className="font-serif text-2xl font-bold sm:text-3xl">
              Start researching Kenyan law today
            </h3>
            <p className="mx-auto mt-2 max-w-xl text-brand-50/90">
              Create a free account and get citation-backed answers in seconds.
            </p>
            <Link
              to="/signup"
              className="btn-gold mt-6 px-7 py-3 text-base"
            >
              Get Started Free →
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
