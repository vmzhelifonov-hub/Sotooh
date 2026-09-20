import { describe, expect, it } from "vitest";
import { formatMoney } from "../components/ui/Field";

describe("formatMoney", () => {
  it("formats IQD with thousands separators", () => {
    expect(formatMoney("1387001.90")).toBe("1,387,001.90 د.ع");
  });

  it("handles empty values", () => {
    expect(formatMoney(null)).toBe("—");
    expect(formatMoney("")).toBe("—");
  });

  it("handles non-numeric gracefully", () => {
    expect(formatMoney("abc")).toBe("abc");
  });

  it("formats integer values without decimals", () => {
    expect(formatMoney("1000000")).toBe("1,000,000 د.ع");
  });
});
