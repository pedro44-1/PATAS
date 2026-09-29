import api from "./client";

export type InvoiceStatus = "draft" | "sent" | "paid" | "cancelled";
export type InvoiceSyncStatus = "pending" | "synced" | "failed";

export interface Invoice {
  id: number;
  clinic_id: number;
  owner_id: number;
  appointment_id: number | null;
  amount: number;
  status: InvoiceStatus;
  currency: string;
  description: string | null;
  reason: string | null;
  external_reference: string | null;
  sync_status: InvoiceSyncStatus;
  created_at: string;
}

export interface InvoiceCreate {
  owner_id: number;
  appointment_id?: number;
  amount: number;
  description?: string;
}

export const invoicesApi = {
  list: (params?: { owner_id?: number; status?: string }) =>
    api.get<Invoice[]>("/invoices/", { params }),
  create: (data: InvoiceCreate) =>
    api.post<Invoice>("/invoices/", data),
  update: (id: number, data: { status?: InvoiceStatus; amount?: number; reason?: string }) =>
    api.patch<Invoice>(`/invoices/${id}`, data),
  sync: (id: number) => api.post<Invoice>(`/invoices/${id}/sync`),
};
