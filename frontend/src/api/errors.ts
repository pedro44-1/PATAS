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
  return String(t(statusKeys[status] ?? DEFAULT_STATUS_KEYS[status] ?? fallbackKey));
}
