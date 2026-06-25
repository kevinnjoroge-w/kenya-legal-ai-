import axios from "axios";
import { env } from "../env.js";

/**
 * Thin client for the Python FastAPI RAG service (port 8000).
 * This service is consumed read-only — never modified.
 * Contract mirrors src/api/main.py.
 */
const rag = axios.create({
  baseURL: env.RAG_BASE_URL,
  timeout: 120_000, // legal generation can be slow
});

export interface RagSource {
  title: string;
  section: string;
  citation: string;
  court: string;
  date: string;
  relevance_score: number;
}

export interface RagChatResult {
  response: string;
  sources: RagSource[];
  mode: string;
  model: string;
  rag_used: boolean;
  tokens_used: number | Record<string, unknown> | null;
  follow_up_questions: string[];
  disclaimer: string;
  disclaimer_level: string;
  grounding_notice: string | null;
}

export interface RagChatParams {
  query: string;
  mode?: string;
  documentType?: string | null;
  court?: string | null;
  history?: { role: string; content: string }[];
}

export async function ragChat(params: RagChatParams): Promise<RagChatResult> {
  const { data } = await rag.post<RagChatResult>("/api/v1/chat", {
    query: params.query,
    mode: params.mode ?? "research",
    document_type: params.documentType ?? null,
    court: params.court ?? null,
    history: params.history ?? [],
  });
  return data;
}

export async function ragHealth(): Promise<unknown> {
  const { data } = await rag.get("/api/v1/health");
  return data;
}
