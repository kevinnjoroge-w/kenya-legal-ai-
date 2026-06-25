import { Link } from "react-router-dom";
import { PageHeader } from "../components/PageHeader.tsx";
import { Disclaimer } from "../components/Disclaimer.tsx";
import { FEATURES, MODES } from "../content.ts";

export function FeaturesPage() {
  return (
    <>
      <PageHeader
        eyebrow="⚖️ Capabilities"
        title="Features built for legal research"
        subtitle="Everything Kenya Legal AI does to help you find, understand, and cite the law — fast."
      />

      <section className="mx-auto max-w-7xl px-5 py-16 sm:px-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
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

      <section className="bg-brand-50/60 py-16">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <h2 className="text-center font-serif text-3xl font-bold text-brand-800">
            Research modes
          </h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {MODES.map((m) => (
              <div key={m.title} className="card">
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
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
        <Disclaimer />
        <div className="mt-10 text-center">
          <Link to="/signup" className="btn-primary px-7 py-3 text-base">
            Try it free →
          </Link>
        </div>
      </section>
    </>
  );
}
