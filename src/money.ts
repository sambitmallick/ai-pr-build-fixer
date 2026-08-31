import { Money } from "./types";

export function usd(cents: number): Money {
  if (!Number.isInteger(cents)) throw new TypeError("cents must be an integer");
  return { cents, currency: "USD" };
}

export function format(money: Money): string {
  const sign = money.cents < 0 ? "-" : "";
  const abs = Math.abs(money.cents);
  return `${sign}$${(abs / 100).toFixed(2)}`;
}

export function add(a: Money, b: Money): Money {
  return { cents: a.cents + b.cents, currency: "USD" };
}
