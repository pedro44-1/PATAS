import type { AxiosResponse } from "axios";

export const PAGE_SIZE = 25;
export const OPTIONS_LIMIT = 200;

export interface PageParams {
  skip?: number;
  limit?: number;
  q?: string;
}

export function totalCount(response: AxiosResponse<unknown[]>): number {
  const header = Number(response.headers["x-total-count"]);
  return Number.isFinite(header) ? header : response.data.length;
}
