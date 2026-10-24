import { describe, expect, it } from "vitest";

import { formatClinicDate, formatDateOnly, formatKz } from "./format";

const normalizeSpaces = (value: string) => value.replace(/\s/g, " ");

describe("format helpers", () => {
  it("always renders Kwanza with two decimals", () => {
    expect(normalizeSpaces(formatKz(1234.5))).toBe("1 234,50 Kz");
    expect(normalizeSpaces(formatKz("1234.567"))).toBe("1 234,57 Kz");
    expect(normalizeSpaces(formatKz(null))).toBe("0,00 Kz");
  });

  it("formats date-only values without shifting the day", () => {
    expect(formatDateOnly("2024-03-01")).toBe("01/03/2024");
    expect(formatDateOnly(null)).toBe("—");
  });

  it("reads timezone-less API instants as UTC and shows the Luanda day", () => {
    expect(formatClinicDate("2026-10-24T23:30:00")).toBe("25/10/2026");
  });
});
