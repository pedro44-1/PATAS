import type {
  InvoiceCreate,
  InvoiceResponse,
  InvoiceStatus,
  InvoiceUpdate,
  PaymentMethod,
} from "@patas/shared-types";

import api from "./client";
import type { PageParams } from "./pagination";

export type Invoice = InvoiceResponse;
export type { InvoiceCreate, InvoiceStatus, InvoiceUpdate, PaymentMethod };

export const invoicesApi = {
  list: (params: PageParams & { owner_id?: number; pet_id?: number; appointment_id?: number; status?: string } = {}) =>
    api.get<Invoice[]>("/invoices/", { params }),
  create: (data: InvoiceCreate) => api.post<Invoice>("/invoices/", data),
  update: (id: number, data: InvoiceUpdate) => api.patch<Invoice>(`/invoices/${id}`, data),
  preview: (id: number) => api.post<Invoice>(`/invoices/${id}/preview`),
  sync: (id: number) => api.post<Invoice>(`/invoices/${id}/sync`),
  reconcile: (id: number) => api.post<Invoice>(`/invoices/${id}/reconcile`),
};
