import { Task, Priority } from "./types";

const WEIGHT: Record<Priority, number> = { low: 1, normal: 2, high: 4 };

/** Sort tasks by priority (high first), then by shortest estimate. */
export function order(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    const byPriority = WEIGHT[b.priority] - WEIGHT[a.priority];
    return byPriority !== 0 ? byPriority : a.estimateMinutes - b.estimateMinutes;
  });
}

/** Total estimated minutes for the not-yet-done tasks. */
export function remainingMinutes(tasks: Task[]): number {
  return tasks.filter((t) => !t.done).reduce((sum, t) => sum + t.estimateMinutes, 0);
}

export function markDone(task: Task): Task {
  return { ...task, done: true };
}
