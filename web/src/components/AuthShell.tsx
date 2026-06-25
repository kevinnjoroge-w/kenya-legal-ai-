import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { STATS } from "../content.ts";

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-brand-800 via-brand-700 to-brand-500 lg:flex">
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, #fff 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <Link to="/" className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-white/15 text-2xl">
              ⚖️
            </div>
            <span className="font-serif text-xl font-bold">Kenya Legal AI</span>
          </Link>

          <div>
            <h2 className="font-serif text-4xl font-bold leading-tight">
              Research Kenyan law,
              <br />
              <span className="text-gold-400">grounded in citations.</span>
            </h2>
            <p className="mt-4 max-w-md text-brand-50/85">
              The Constitution, Acts of Parliament, and 100,000+ court judgments
              — answered in seconds, with every source linked.
            </p>
            <div className="mt-10 grid max-w-md grid-cols-3 gap-4">
              {STATS.map((s) => (
                <div key={s.label}>
                  <div className="font-serif text-2xl font-bold text-gold-400">
                    {s.value}
                  </div>
                  <div className="text-xs text-brand-50/75">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          <p className="text-xs text-brand-100/70">
            A legal research tool — not a substitute for professional advice.
          </p>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center lg:hidden">
            <div className="text-4xl">⚖️</div>
          </div>
          <h1 className="font-serif text-2xl font-bold text-brand-800">
            {title}
          </h1>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
          <div className="mt-7">{children}</div>
        </div>
      </div>
    </div>
  );
}
