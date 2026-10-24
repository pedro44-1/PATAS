import axios from "axios";
import type { TFunction } from "i18next";

const DEFAULT_STATUS_KEYS: Record<number, string> = {
  401: "apiErrors.sessionExpired",
  403: "apiErrors.forbidden",
  409: "apiErrors.conflict",
  422: "apiErrors.validation",
};

export function apiErrorMessage(
  error: unknown,
  t: TFunction,
  fallbackKey: string,
  statusKeys: Partial<Record<number, string>> = {},
): string {
  if (!axios.isAxiosError(error)) return String(t(fallbackKey));
  const status = error.response?.status;
  if (!status) return String(t(fallbackKey));
  if (statusKeys[status]) return String(t(statusKeys[status]));
  const detail = serverDetail(error.response?.data);
  if (detail && status !== 401) return detail;
  return String(t(DEFAULT_STATUS_KEYS[status] ?? fallbackKey));
}

const CUSTOM_VALIDATION_PREFIX = "Value error, ";

function serverDetail(data: unknown): string | null {
  if (!data || typeof data !== "object") return null;
  const detail = (data as { detail?: unknown }).detail;
  if (typeof detail === "string") return /\s/.test(detail.trim()) ? detail : null;
  if (!Array.isArray(detail)) return null;
  const message = detail.map((item) => (item as { msg?: unknown })?.msg)
    .find((msg): msg is string => typeof msg === "string" && msg.startsWith(CUSTOM_VALIDATION_PREFIX));
  return message ? message.slice(CUSTOM_VALIDATION_PREFIX.length) : null;
}
