import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { Link } from "react-router-dom";
import { AxiosError } from "axios";
import { Sidebar } from "../components/Sidebar.tsx";
import { MessageBubble } from "../components/MessageBubble.tsx";
import type { ConversationSummary, Message, UsageStatus } from "../types.ts";
import {
  createConversation,
  deleteConversation,
  getConversation,
  getUsage,
  listConversations,
  renameConversation,
  sendMessage,
} from "../api/conversations.ts";

const MODES: { value: string; label: string }[] = [
  { value: "research", label: "Research" },
  { value: "case_analysis", label: "Case Analysis" },
  { value: "drafting", label: "Drafting" },
  { value: "deep_research", label: "Deep Research" },
  { value: "plain_language", label: "Plain Language" },
  { value: "swahili", label: "Kiswahili" },
];

const EXAMPLES = [
  "What does Article 27 of the Constitution say about equality?",
  "Explain the rights of an accused person under Kenyan law.",
  "What is the process for impeaching a governor in Kenya?",
  "Summarize the Employment Act 2007 provisions on termination.",
];

export function ChatPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("research");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limitReached, setLimitReached] = useState(false);
  const [usage, setUsage] = useState<UsageStatus | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshList = useCallback(async () => {
    setConversations(await listConversations());
  }, []);

  const refreshUsage = useCallback(async () => {
    try {
      setUsage(await getUsage());
    } catch {
      /* non-critical */
    }
  }, []);

  useEffect(() => {
    refreshList();
    refreshUsage();
  }, [refreshList, refreshUsage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function openConversation(id: string) {
    setActiveId(id);
    setError(null);
    const convo = await getConversation(id);
    setMessages(convo.messages);
  }

  function newChat() {
    setActiveId(null);
    setMessages([]);
    setError(null);
  }

  async function handleRename(id: string, title: string) {
    await renameConversation(id, title);
    refreshList();
  }

  async function handleDelete(id: string) {
    await deleteConversation(id);
    if (id === activeId) newChat();
    refreshList();
  }

  async function submitQuery(query: string) {
    if (!query || sending) return;
    setError(null);
    setSending(true);
    setInput("");

    // Optimistically show the user's message.
    const optimistic: Message = {
      id: `tmp-${Date.now()}`,
      conversationId: activeId ?? "",
      role: "user",
      content: query,
      mode,
      sources: null,
      model: null,
      tokensUsed: null,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);

    try {
      // Ensure a conversation exists.
      let convoId = activeId;
      if (!convoId) {
        const convo = await createConversation();
        convoId = convo.id;
        setActiveId(convoId);
      }

      const { userMessage, assistantMessage, usage: usageAfter } =
        await sendMessage(convoId, query, mode);

      // Replace optimistic user message with the persisted pair.
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimistic.id),
        userMessage,
        assistantMessage,
      ]);
      setUsage(usageAfter);
      setLimitReached(usageAfter.exceeded);
      refreshList();
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
      setInput(query);
      if (err instanceof AxiosError && err.response?.status === 429) {
        setLimitReached(true);
        setError(
          err.response?.data?.error ??
            "You've reached your daily request limit. Upgrade your plan to continue.",
        );
        refreshUsage();
      } else {
        setError(
          "Something went wrong reaching the legal AI. Is the RAG service running?",
        );
      }
      console.error(err);
    } finally {
      setSending(false);
    }
  }

  function handleSend(e: FormEvent) {
    e.preventDefault();
    submitQuery(input.trim());
  }

  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={openConversation}
        onNew={newChat}
        onRename={handleRename}
        onDelete={handleDelete}
      />

      <main className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="flex items-center justify-between border-b border-brand-100 bg-white px-6 py-3">
          <div>
            <h1 className="font-serif text-lg font-bold text-brand-800">
              Legal Research Chat
            </h1>
            <p className="text-xs text-slate-500">
              Citation-backed answers from Kenya's legal framework
            </p>
          </div>
          <div className="flex items-center gap-3">
            {usage && (
              <span
                className={`hidden items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium sm:inline-flex ${
                  usage.exceeded
                    ? "bg-flag-red/10 text-flag-red"
                    : "bg-brand-50 text-brand-700"
                }`}
                title={`${usage.plan} plan · resets at UTC midnight`}
              >
                <span className="font-semibold uppercase tracking-wide">
                  {usage.plan}
                </span>
                {usage.limit == null
                  ? "· Unlimited"
                  : `· ${usage.remaining}/${usage.limit} left today`}
              </span>
            )}
            <label className="flex items-center gap-2 text-xs text-slate-500">
              Mode
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="rounded-lg border border-brand-200 bg-brand-50/50 px-2.5 py-1.5 text-sm font-medium text-brand-700 outline-none focus:border-brand-500"
              >
                {MODES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.length === 0 && !sending && (
              <div className="mx-auto mt-6 max-w-2xl text-center">
                <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-brand-700 to-brand-500 text-3xl shadow-card">
                  ⚖️
                </div>
                <h2 className="mt-5 font-serif text-2xl font-bold text-brand-800">
                  Welcome to Kenya Legal AI
                </h2>
                <p className="mt-2 text-sm text-slate-600">
                  Ask about the Constitution, Acts of Parliament, court
                  judgments, or any aspect of Kenya's legal framework.
                </p>
                <div className="mt-7 grid gap-3 text-left sm:grid-cols-2">
                  {EXAMPLES.map((q) => (
                    <button
                      key={q}
                      onClick={() => submitQuery(q)}
                      className="rounded-xl border border-brand-100 bg-white px-4 py-3 text-sm text-slate-700 transition hover:border-brand-300 hover:text-brand-700 hover:shadow-soft"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}

            {sending && (
              <div className="flex justify-start gap-3">
                <div className="mt-1 hidden h-8 w-8 flex-none place-items-center rounded-full bg-gradient-to-br from-brand-700 to-brand-500 text-sm sm:grid">
                  ⚖️
                </div>
                <div className="flex items-center gap-2 rounded-2xl border border-brand-100 bg-white px-4 py-3 text-sm text-slate-400">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-brand-400 [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-brand-400 [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-brand-400" />
                  <span className="ml-1">Researching…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {limitReached && (
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gold-500/30 bg-gold-500/10 px-6 py-3">
            <p className="text-sm text-brand-800">
              ⚠️ You've used all
              {usage?.limit != null ? ` ${usage.limit}` : ""} of today's requests
              on the <strong>{usage?.plan ?? "Free"}</strong> plan.
            </p>
            <Link to="/pricing" className="btn-gold px-4 py-1.5 text-xs">
              Upgrade plan →
            </Link>
          </div>
        )}

        {error && !limitReached && (
          <div className="border-t border-flag-red/20 bg-flag-red/5 px-6 py-2 text-sm text-flag-red">
            {error}
          </div>
        )}

        {/* Composer */}
        <form
          onSubmit={handleSend}
          className="border-t border-brand-100 bg-white px-4 py-4 sm:px-6"
        >
          <div className="mx-auto max-w-3xl">
            <div className="flex items-end gap-2 rounded-2xl border border-brand-200 bg-white p-2 shadow-soft focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/20">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submitQuery(input.trim());
                  }
                }}
                rows={1}
                placeholder={
                  limitReached
                    ? "Daily limit reached — upgrade to keep researching"
                    : "Ask a legal question…"
                }
                maxLength={2000}
                disabled={limitReached}
                className="max-h-40 flex-1 resize-none bg-transparent px-3 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={sending || !input.trim() || limitReached}
                className="grid h-10 w-10 flex-none place-items-center rounded-xl bg-gradient-to-br from-brand-700 to-brand-500 text-white transition hover:opacity-90 disabled:opacity-40"
                aria-label="Send message"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M22 2L11 13" />
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                </svg>
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-slate-400">
              AI-generated content — not legal advice. Always verify against the
              cited sources.
            </p>
          </div>
        </form>
      </main>
    </div>
  );
}
