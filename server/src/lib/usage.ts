import { prisma } from "../prisma.js";
import { planFor } from "./plans.js";

/** Midnight today, UTC — the rolling reset boundary for daily quotas. */
export function startOfDayUTC(now = new Date()): Date {
  return new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
  );
}

export interface UsageStatus {
  plan: string;
  used: number;
  /** null = unlimited */
  limit: number | null;
  /** null = unlimited */
  remaining: number | null;
  exceeded: boolean;
  resetsAt: string;
}

/** Count today's chat requests for a user and compare against their plan. */
export async function getUsageStatus(
  userId: string,
  planName: string | null | undefined,
): Promise<UsageStatus> {
  const plan = planFor(planName);
  const used = await prisma.usageEvent.count({
    where: { userId, kind: "chat", createdAt: { gte: startOfDayUTC() } },
  });

  const limit = plan.dailyRequestLimit;
  const remaining = limit == null ? null : Math.max(0, limit - used);
  const exceeded = limit != null && used >= limit;

  // Next UTC midnight.
  const reset = startOfDayUTC();
  reset.setUTCDate(reset.getUTCDate() + 1);

  return {
    plan: plan.id,
    used,
    limit,
    remaining,
    exceeded,
    resetsAt: reset.toISOString(),
  };
}
