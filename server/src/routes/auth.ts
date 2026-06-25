import { Router } from "express";
import { z } from "zod";
import { prisma } from "../prisma.js";
import { hashPassword, verifyPassword } from "../lib/hash.js";
import {
  signAccessToken,
  generateRefreshToken,
} from "../lib/jwt.js";
import { asyncHandler, HttpError } from "../middleware/errorHandler.js";
import { requireAuth, type AuthedRequest } from "../middleware/auth.js";
import { getUsageStatus } from "../lib/usage.js";

export const authRouter = Router();

const signupSchema = z.object({
  name: z.string().min(1).max(120),
  email: z.string().email(),
  password: z.string().min(8).max(200),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

const refreshSchema = z.object({
  refreshToken: z.string().min(1),
});

function publicUser(user: {
  id: string;
  name: string;
  email: string;
  plan: string;
}) {
  return { id: user.id, name: user.name, email: user.email, plan: user.plan };
}

async function issueTokens(userId: string) {
  const accessToken = signAccessToken(userId);
  const { token, expiresAt } = generateRefreshToken();
  await prisma.refreshToken.create({
    data: { userId, token, expiresAt },
  });
  return { accessToken, refreshToken: token };
}

authRouter.post(
  "/signup",
  asyncHandler(async (req, res) => {
    const { name, email, password } = signupSchema.parse(req.body);

    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) throw new HttpError(409, "Email already registered");

    const user = await prisma.user.create({
      data: { name, email, passwordHash: await hashPassword(password) },
    });

    const tokens = await issueTokens(user.id);
    res.status(201).json({ ...tokens, user: publicUser(user) });
  }),
);

authRouter.post(
  "/login",
  asyncHandler(async (req, res) => {
    const { email, password } = loginSchema.parse(req.body);

    const user = await prisma.user.findUnique({ where: { email } });
    if (!user || !(await verifyPassword(password, user.passwordHash))) {
      throw new HttpError(401, "Invalid credentials");
    }

    const tokens = await issueTokens(user.id);
    res.json({ ...tokens, user: publicUser(user) });
  }),
);

authRouter.post(
  "/refresh",
  asyncHandler(async (req, res) => {
    const { refreshToken } = refreshSchema.parse(req.body);

    const stored = await prisma.refreshToken.findUnique({
      where: { token: refreshToken },
    });
    if (!stored || stored.revoked || stored.expiresAt < new Date()) {
      throw new HttpError(401, "Invalid or expired refresh token");
    }

    res.json({ accessToken: signAccessToken(stored.userId) });
  }),
);

authRouter.post(
  "/logout",
  asyncHandler(async (req, res) => {
    const { refreshToken } = refreshSchema.parse(req.body);
    await prisma.refreshToken.updateMany({
      where: { token: refreshToken },
      data: { revoked: true },
    });
    res.status(204).end();
  }),
);

authRouter.get(
  "/me",
  requireAuth,
  asyncHandler(async (req: AuthedRequest, res) => {
    const user = await prisma.user.findUnique({ where: { id: req.userId } });
    if (!user) throw new HttpError(404, "User not found");
    const usage = await getUsageStatus(user.id, user.plan);
    res.json({ user: publicUser(user), usage });
  }),
);

authRouter.get(
  "/usage",
  requireAuth,
  asyncHandler(async (req: AuthedRequest, res) => {
    const user = await prisma.user.findUnique({
      where: { id: req.userId },
      select: { plan: true },
    });
    if (!user) throw new HttpError(404, "User not found");
    const usage = await getUsageStatus(req.userId!, user.plan);
    res.json({ usage });
  }),
);
