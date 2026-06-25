import jwt from "jsonwebtoken";
import crypto from "node:crypto";
import { env } from "../env.js";

export interface AccessTokenPayload {
  sub: string; // user id
}

export function signAccessToken(userId: string): string {
  return jwt.sign({ sub: userId }, env.JWT_SECRET, {
    expiresIn: env.ACCESS_TOKEN_TTL,
  } as jwt.SignOptions);
}

export function verifyAccessToken(token: string): AccessTokenPayload {
  return jwt.verify(token, env.JWT_SECRET) as AccessTokenPayload;
}

/**
 * Refresh tokens are opaque random strings stored (and revocable) in Postgres,
 * not JWTs — so logout/rotation can invalidate them server-side.
 */
export function generateRefreshToken(): { token: string; expiresAt: Date } {
  const token = crypto.randomBytes(48).toString("hex");
  const expiresAt = new Date(
    Date.now() + env.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60 * 1000,
  );
  return { token, expiresAt };
}
