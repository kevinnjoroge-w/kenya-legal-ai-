import { api } from "./client.ts";
import type {
  ConversationDetail,
  ConversationSummary,
  Message,
  SendMessageMeta,
  UsageStatus,
} from "../types.ts";

export async function getUsage(): Promise<UsageStatus> {
  const { data } = await api.get("/auth/usage");
  return data.usage;
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const { data } = await api.get("/conversations");
  return data.conversations;
}

export async function createConversation(): Promise<ConversationSummary> {
  const { data } = await api.post("/conversations");
  return data.conversation;
}

export async function getConversation(
  id: string,
): Promise<ConversationDetail> {
  const { data } = await api.get(`/conversations/${id}`);
  return data.conversation;
}

export async function renameConversation(
  id: string,
  title: string,
): Promise<ConversationSummary> {
  const { data } = await api.patch(`/conversations/${id}`, { title });
  return data.conversation;
}

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(`/conversations/${id}`);
}

export async function sendMessage(
  conversationId: string,
  query: string,
  mode = "research",
): Promise<{
  userMessage: Message;
  assistantMessage: Message;
  meta: SendMessageMeta;
  usage: UsageStatus;
}> {
  const { data } = await api.post(`/conversations/${conversationId}/messages`, {
    query,
    mode,
  });
  return data;
}
