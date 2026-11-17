import { describe, expect, it } from "vitest";

import { formatCount, formatINR, withSuffix } from "@/lib/format";

describe("formatINR", () => {
  it("uses Indian digit grouping and no paise", () => {
    expect(formatINR(12_450_000)).toBe("₹1,24,500");
    expect(formatINR(489_900)).toBe("₹4,899");
    expect(formatINR(0)).toBe("₹0");
  });
});

describe("formatCount / withSuffix", () => {
  it("groups counts the Indian way", () => expect(formatCount(1234567)).toBe("12,34,567"));
  it("attaches symbols and spaces words", () => {
    expect(withSuffix("120", "+")).toBe("120+");
    expect(withSuffix("21", "days")).toBe("21 days");
    expect(withSuffix("8", "")).toBe("8");
  });
});
