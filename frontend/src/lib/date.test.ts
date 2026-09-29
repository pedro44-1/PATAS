import { describe, expect, it } from "vitest";
import { clinicDateInput, clinicDateTimeInput, clinicInputToUtc, parseApiDate } from "./date";

describe("clinic dates", () => {
  it("formats calendar dates in Africa/Luanda", () => {
    expect(clinicDateInput(new Date("2026-01-01T23:30:00Z"))).toBe("2026-01-02");
  });

  it("treats timezone-less API instants as stored UTC", () => {
    expect(parseApiDate("2026-09-28T08:30:00").toISOString()).toBe(
      "2026-09-28T08:30:00.000Z",
    );
  });

  it("round-trips Luanda form values at the UTC boundary", () => {
    expect(clinicDateTimeInput(new Date("2026-09-28T08:30:00Z"))).toBe("2026-09-28T09:30");
    expect(clinicInputToUtc("2026-09-28T09:30")).toBe("2026-09-28T08:30:00.000Z");
  });
});
