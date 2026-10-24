import { CLINIC_TIME_ZONE, parseApiDate } from "@/lib/date";

const LOCALE = "pt-AO";

const kwanza = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: "AOA",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatKz(value: number | string | null | undefined): string {
  const amount = Number(value ?? 0);
  return kwanza.format(Number.isFinite(amount) ? amount : 0);
}

export function formatClinicDate(value: string | Date, options: Intl.DateTimeFormatOptions = {}): string {
  const date = typeof value === "string" ? parseApiDate(value) : value;
  return date.toLocaleDateString(LOCALE, { timeZone: CLINIC_TIME_ZONE, ...options });
}

export function formatClinicDateTime(value: string | Date, options: Intl.DateTimeFormatOptions = {}): string {
  const date = typeof value === "string" ? parseApiDate(value) : value;
  return date.toLocaleString(LOCALE, {
    timeZone: CLINIC_TIME_ZONE,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  });
}

export function formatDateOnly(value: string | null | undefined, options: Intl.DateTimeFormatOptions = {}): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  if (!year || !month || !day) return "—";
  return new Date(Date.UTC(year, month - 1, day)).toLocaleDateString(LOCALE, { timeZone: "UTC", ...options });
}
