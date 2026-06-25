import { Link } from "react-router-dom";

export function Brand({ light = false }: { light?: boolean }) {
  return (
    <Link to="/" className="flex items-center gap-3">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-700 to-brand-500 text-xl shadow-sm">
        ⚖️
      </div>
      <div className="flex flex-col leading-none">
        <span
          className={`font-serif text-lg font-bold ${
            light ? "text-white" : "text-brand-800"
          }`}
        >
          Kenya Legal AI
        </span>
        <span
          className={`text-[11px] font-medium ${
            light ? "text-brand-100" : "text-brand-500"
          }`}
        >
          Powered by AI
        </span>
      </div>
    </Link>
  );
}
