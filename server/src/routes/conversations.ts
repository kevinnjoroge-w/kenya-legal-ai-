import { Router } from "express";
import { z } from "zod";
import type { Prisma } from "@prisma/client";
import { prisma } from "../prisma.js";
import { requireAuth, type AuthedRequest } from "../middleware/auth.js";
import { asyncHandler, HttpError } from "../middleware/errorHandler.js";
import { ragChat } from "../lib/ragClient.js";
import { getUsageStatus } from "../lib/usage.js";

export const conversationsRouter = Router();

// All conversation routes require auth.
conversationsRouter.use(requireAuth);

const RAG_MODES = [
  "research",
  "case_analysis",
  "drafting",
  "deep_research",
  "petition_drafting",
  "judicial_review",
  "devolution",
  "cross_reference",
  "plain_language",
  "swahili",
] as const;

const messageSchema = z.object({
  query: z.string().min(3).max(2000),
  mode: z.enum(RAG_MODES).default("research"),
  documentType: z.string().optional(),
  court: z.string().optional(),
});

const renameSchema = z.object({ title: z.string().min(1).max(200) });

/** Ensure the conversation exists and belongs to the caller. */
async function ownedConversation(userId: string, id: string) {
  const convo = await prisma.conversation.findFirst({
    where: { id, userId },
  });
  if (!convo) throw new HttpError(404, "Conversation not found");
  return convo;
}

function titleFromQuery(query: string): string {
  const trimmed = query.trim().replace(/\s+/g, " ");
  return trimmed.length > 60 ? `${trimmed.slice(0, 57)}…` : trimmed;
}

// ─── List ──────────────────────────────────────────────────────────────────
conversationsRouter.get(
  "/",
  asyncHandler(async (req: AuthedRequest, res) => {
    const conversations = await prisma.conversation.findMany({
      where: { userId: req.userId },
      orderBy: { updatedAt: "desc" },
      select: { id: true, title: true, updatedAt: true, createdAt: true },
    });
    res.json({ conversations });
  }),
);

// ─── Create ────────────────────────────────────────────────────────────────
conversationsRouter.post(
  "/",
  asyncHandler(async (req: AuthedRequest, res) => {
    const convo = await prisma.conversation.create({
      data: { userId: req.userId! },
    });
    res.status(201).json({ conversation: convo });
  }),
);

// ─── Get one (with messages) ────────────────────────────────────────────────
conversationsRouter.get(
  "/:id",
  asyncHandler(async (req: AuthedRequest, res) => {
    await ownedConversation(req.userId!, req.params.id);
    const convo = await prisma.conversation.findUnique({
      where: { id: req.params.id },
      include: { messages: { orderBy: { createdAt: "asc" } } },
    });
    res.json({ conversation: convo });
  }),
);

// ─── Rename ─────────────────────────────────────────────────────────────────
conversationsRouter.patch(
  "/:id",
  asyncHandler(async (req: AuthedRequest, res) => {
    await ownedConversation(req.userId!, req.params.id);
    const { title } = renameSchema.parse(req.body);
    const convo = await prisma.conversation.update({
      where: { id: req.params.id },
      data: { title },
    });
    res.json({ conversation: convo });
  }),
);

// ─── Delete ─────────────────────────────────────────────────────────────────
conversationsRouter.delete(
  "/:id",
  asyncHandler(async (req: AuthedRequest, res) => {
    await ownedConversation(req.userId!, req.params.id);
    await prisma.conversation.delete({ where: { id: req.params.id } });
    res.status(204).end();
  }),
);

// ─── Send a message → RAG → persist ─────────────────────────────────────────
conversationsRouter.post(
  "/:id/messages",
  asyncHandler(async (req: AuthedRequest, res) => {
    const userId = req.userId!;
    await ownedConversation(userId, req.params.id);
    const { query, mode, documentType, court } = messageSchema.parse(req.body);

    // Enforce the caller's plan daily request quota before doing any work.
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { plan: true },
    });
    const usage = await getUsageStatus(userId, user?.plan);
    if (usage.exceeded) {
      throw new HttpError(
        429,
        `You've reached your ${usage.plan} plan limit of ${usage.limit} requests for today. Upgrade your plan or try again after the daily reset.`,
      );
    }

    // Build history from prior turns in this conversation.
    const prior = await prisma.message.findMany({
      where: { conversationId: req.params.id },
      orderBy: { createdAt: "asc" },
      select: { role: true, content: true },
    });
    const history = prior.map((m) => ({ role: m.role, content: m.content }));

    // Persist the user's message first.
    const userMessage = await prisma.message.create({
      data: { conversationId: req.params.id, role: "user", content: query, mode },
    });

    // Call the Python RAG service.
    const result = await ragChat({ query, mode, documentType, court, history });

    const tokens =
      typeof result.tokens_used === "number" ? result.tokens_used : null;

    // Persist the assistant reply.
    const assistantMessage = await prisma.message.create({
      data: {
        conversationId: req.params.id,
        role: "assistant",
        content: result.response,
        mode: result.mode,
        model: result.model,
        sources: result.sources as unknown as Prisma.InputJsonValue,
        tokensUsed: tokens,
      },
    });

    // Record usage + bump conversation; auto-title on first turn.
    await prisma.usageEvent.create({
      data: { userId, kind: "chat", tokens: tokens ?? 0 },
    });
    const usageAfter = await getUsageStatus(userId, user?.plan);
    await prisma.conversation.update({
      where: { id: req.params.id },
      data: {
        updatedAt: new Date(),
        ...(history.length === 0 ? { title: titleFromQuery(query) } : {}),
      },
    });

    res.status(201).json({
      userMessage,
      assistantMessage,
      meta: {
        rag_used: result.rag_used,
        follow_up_questions: result.follow_up_questions,
        disclaimer: result.disclaimer,
        disclaimer_level: result.disclaimer_level,
        grounding_notice: result.grounding_notice,
      },
      usage: usageAfter,
    });
  }),
);
