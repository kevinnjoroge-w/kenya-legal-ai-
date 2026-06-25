import ReactMarkdown from "react-markdown";
import type { Message } from "../types.ts";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-3`}>
      {!isUser && (
        <div className="mt-1 hidden h-8 w-8 flex-none place-items-center rounded-full bg-gradient-to-br from-brand-700 to-brand-500 text-sm sm:grid">
          ⚖️
        </div>
      )}
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 text-sm shadow-sm ${
          isUser
            ? "bg-gradient-to-br from-brand-700 to-brand-600 text-white"
            : "border border-brand-100 bg-white text-slate-800"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="legal-markdown">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 border-t border-brand-100 pt-2.5">
            <p className="mb-1.5 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-brand-600">
              📚 Sources
            </p>
            <ul className="space-y-1.5">
              {message.sources.map((s, i) => (
                <li
                  key={i}
                  className="rounded-lg bg-brand-50/70 px-2.5 py-1.5 text-xs text-slate-600"
                >
                  <span className="font-medium text-brand-800">
                    {s.citation || s.title}
                  </span>
                  {s.section && ` — ${s.section}`}
                  {s.court && ` · ${s.court}`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
