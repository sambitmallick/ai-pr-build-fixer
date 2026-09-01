import { Task } from "./types";
import { order, remainingMinutes } from "./task";
import { add, format, usd } from "./money";

export interface Report {
  headline: string;
  totalCostCents: number;
}

// A flat rate we bill per estimated minute of work.
const RATE_PER_MIN = usd(50);

export function buildReport(tasks: Task[]): Report {
  const top = order(tasks).find((t) => !t.done);
  const mins = remainingMinutes(tasks);
  const cost = add(RATE_PER_MIN, usd(mins));
  const headline = `Top: ${top?.title ?? "none"} — ${format(cost)}`;
  return { headline, totalCostCents: cost.cents };
}
