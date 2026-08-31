export type Priority = "low" | "normal" | "high";

export interface Task {
  id: number;
  title: string;
  priority: Priority;
  estimateMinutes: number;
  done: boolean;
}

export interface Money {
  /** integer amount in cents */
  cents: number;
  currency: "USD";
}
