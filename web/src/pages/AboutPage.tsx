import { PageHeader } from "../components/PageHeader.tsx";
import { Disclaimer } from "../components/Disclaimer.tsx";
import { FEATURES, STATS } from "../content.ts";

export function AboutPage() {
  return (
    <>
      <PageHeader
        eyebrow="About"
        title="About Kenya Legal AI"
        subtitle="Understanding your AI legal research assistant — and the principles behind it."
      />

      <section className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
        <div className="prose prose-slate max-w-none">
          <p className="text-lg leading-relaxed text-slate-700">
            Kenya Legal AI makes the Kenyan legal corpus searchable in plain
            language. Instead of paging through statutes and reporters, you ask a
            question and receive a grounded answer — every claim tied back to the
            Constitution, an Act of Parliament, or a reported judgment.
          </p>
          <p className="mt-4 leading-relaxed text-slate-700">
            Under the hood, a Retrieval-Augmented Generation (RAG) pipeline
            retrieves the most relevant legal passages and asks the model to
            answer <em>only</em> from those sources. That keeps responses
            anchored to real law and surfaces citations you can verify yourself.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-3 gap-4">
          {STATS.map((s) => (
            <div
              key={s.label}
              className="rounded-2xl border border-brand-100 bg-white p-5 text-center shadow-soft"
            >
              <div className="font-serif text-2xl font-bold text-brand-700">
                {s.value}
              </div>
              <div className="mt-1 text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-brand-50/60 py-16">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <h2 className="text-center font-serif text-3xl font-bold text-brand-800">
            What makes it different
          </h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="card">
                <div className="text-3xl">{f.icon}</div>
                <h3 className="mt-3 font-serif text-lg font-bold text-brand-800">
                  {f.title}
                </h3>
                <p className="mt-2 text-sm text-slate-600">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-5 py-16 sm:px-8">
        <Disclaimer />
      </section>
    </>
  );
}
