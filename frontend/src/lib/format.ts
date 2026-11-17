const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

/** Paise → "₹1,24,500" (Indian digit grouping). Display only: the server owns all money maths. */
export function formatINR(paise: number): string {
  return inr.format(Math.round(paise / 100));
}

/** Integer with Indian grouping: 124500 → "1,24,500". */
export function formatCount(n: number): string {
  return new Intl.NumberFormat("en-IN").format(n);
}

/** Stat suffix: symbols attach ("+", "%"), words get a space ("21 days"). */
export function withSuffix(value: string, suffix?: string | null): string {
  if (!suffix) return value;
  return /^[\p{L}]/u.test(suffix) ? `${value} ${suffix}` : `${value}${suffix}`;
}
