export interface User {
  id: string;
  name: string;
  email: string;
  plan: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface Source {
  title: string;
  section: string;
  citation: string;
  court: string;
  date: string;
  relevance_score: number;
}

export interface Message {
  id: string;
  conversationId: string;
  role: "user" | "assistant";
  content: string;
  mode: string | null;
  sources: Source[] | null;
  model: string | null;
  tokensUsed: number | null;
  createdAt: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: Message[];
}

export interface UsageStatus {
  plan: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  exceeded: boolean;
  resetsAt: string;
}

export interface SendMessageMeta {
  rag_used: boolean;
  follow_up_questions: string[];
  disclaimer: string;
  disclaimer_level: string;
  grounding_notice: string | null;
}
