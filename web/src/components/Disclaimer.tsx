import { DISCLAIMER } from "../content.ts";

export function Disclaimer() {
  return (
    <div className="rounded-2xl border-l-4 border-gold-500 bg-gold-500/10 p-6">
      <h3 className="font-serif text-lg font-bold text-brand-800">
        ⚠️ Important Disclaimer
      </h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-700">{DISCLAIMER}</p>
    </div>
  );
}
