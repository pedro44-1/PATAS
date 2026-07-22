import api from "./client";

export type InvoiceStatus = "draft" | "paid" | "cancelled";

export interface Invoice {
  id: number;
  clinic_id: number;
  owner_id: number;
  appointment_id: number | null;
  amount: number;
  status: InvoiceStatus;
  description: string | null;
  reason: string | null;
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
  delete: (id: number) =>
    api.delete(`/invoices/${id}`),
};
