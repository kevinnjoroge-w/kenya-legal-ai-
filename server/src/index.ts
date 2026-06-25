import express from "express";
import cors from "cors";
import { env } from "./env.js";
import { authRouter } from "./routes/auth.js";
import { conversationsRouter } from "./routes/conversations.js";
import { errorHandler } from "./middleware/errorHandler.js";
import { ragHealth } from "./lib/ragClient.js";
import { PLANS } from "./lib/plans.js";

const app = express();

app.use(cors({ origin: env.CORS_ORIGIN, credentials: true }));
app.use(express.json({ limit: "1mb" }));

// Health: reports the Express app and probes the RAG service.
app.get("/api/health", async (_req, res) => {
  let rag: unknown;
  let ragOk = true;
  try {
    rag = await ragHealth();
  } catch (err) {
    ragOk = false;
    rag = { error: err instanceof Error ? err.message : "unreachable" };
  }
  res.json({ status: "ok", rag_reachable: ragOk, rag });
});

// Public: billing tiers (single source of truth for the pricing UI).
app.get("/api/plans", (_req, res) => {
  res.json({ plans: Object.values(PLANS) });
});

app.use("/api/auth", authRouter);
app.use("/api/conversations", conversationsRouter);

app.use(errorHandler);

app.listen(env.PORT, () => {
  console.log(`🚀 Express API listening on http://localhost:${env.PORT}`);
  console.log(`   RAG service: ${env.RAG_BASE_URL}`);
  console.log(`   CORS origin: ${env.CORS_ORIGIN}`);
});
