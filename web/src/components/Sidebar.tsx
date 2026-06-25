import { useState } from "react";
import { Link } from "react-router-dom";
import type { ConversationSummary } from "../types.ts";
import { useAuth } from "../auth/AuthContext.tsx";

interface SidebarProps {
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onRename,
  onDelete,
}: SidebarProps) {
  const { user, logout } = useAuth();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  function startEdit(c: ConversationSummary) {
    setEditingId(c.id);
    setDraft(c.title);
  }

  function commitEdit(id: string) {
    const title = draft.trim();
    if (title) onRename(id, title);
    setEditingId(null);
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-brand-800/40 bg-brand-900 text-brand-50">
      <div className="flex items-center gap-2 border-b border-white/10 px-4 py-4">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/10 text-lg">
            ⚖️
          </span>
          <span className="font-serif text-base font-bold text-white">
            Kenya Legal AI
          </span>
        </Link>
      </div>

      <div className="p-3">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-white/10 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-white/15"
        >
          <span className="text-lg leading-none">＋</span> New chat
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-2">
        {conversations.length === 0 && (
          <p className="px-2 py-6 text-center text-xs text-brand-200/70">
            No conversations yet
          </p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`group flex items-center gap-1 rounded-lg px-2 py-2 text-sm transition ${
              c.id === activeId
                ? "bg-white/15 text-white"
                : "text-brand-100 hover:bg-white/10"
            }`}
          >
            {editingId === c.id ? (
              <input
                autoFocus
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onBlur={() => commitEdit(c.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitEdit(c.id);
                  if (e.key === "Escape") setEditingId(null);
                }}
                className="w-full rounded border border-white/20 bg-brand-800 px-1.5 py-0.5 text-sm text-white outline-none"
              />
            ) : (
              <>
                <button
                  onClick={() => onSelect(c.id)}
                  className="flex-1 truncate text-left"
                  title={c.title}
                >
                  {c.title}
                </button>
                <button
                  onClick={() => startEdit(c)}
                  className="hidden text-brand-200 hover:text-white group-hover:block"
                  title="Rename"
                >
                  ✎
                </button>
                <button
                  onClick={() => onDelete(c.id)}
                  className="hidden text-brand-200 hover:text-gold-400 group-hover:block"
                  title="Delete"
                >
                  🗑
                </button>
              </>
            )}
          </div>
        ))}
      </nav>

      <div className="border-t border-white/10 p-3">
        <div className="mb-2 flex items-center gap-2 px-1">
          <span className="grid h-8 w-8 place-items-center rounded-full bg-gold-500/20 text-sm font-bold text-gold-300">
            {user?.name?.charAt(0).toUpperCase() ?? "?"}
          </span>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-white">
              {user?.name}
            </div>
            <div className="text-[11px] uppercase tracking-wide text-brand-200/80">
              {user?.plan} plan
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full rounded-lg px-3 py-1.5 text-left text-sm text-brand-100 transition hover:bg-white/10"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
