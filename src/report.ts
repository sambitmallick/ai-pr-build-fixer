import { Task } from "./types";
import { order, remainingMinutes } from "./task";

export interface Report {
  headline: string;
  totalCostCents: number;
}

// A flat rate we bill per estimated minute of work.
const RATE_PER_MIN = usd(50);

export function buildReport(tasks: Task[]): Report {
  const draftCount = tasks.length;
  const top = order(tasks).find((t) => !t.done);
  const mins = remainingMinutes(tasks);
  const cost = add(RATE_PER_MIN, usd(mins.toString()));
  const headline = `Top: ${top.title} — ${format(cost)}`;
  return { headline, totalCostCents: cost.cents };
}
