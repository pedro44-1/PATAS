// ─── Invoice types ────────────────────────────────────────────────────────────────

export type InvoiceStatus = "draft" | "paid" | "cancelled";

export interface InvoiceCreate {
  owner_id: number;
  appointment_id?: number;
  amount: number;
  description?: string;
  reason?: string;
}

export interface InvoiceUpdate {
  status?: InvoiceStatus;
  amount?: number;
  description?: string;
  reason?: string;
}

export interface InvoiceResponse {
  id: number;
  clinic_id: number;
  owner_id: number;
  appointment_id: number | null;
  amount: number;
  status: InvoiceStatus;
  description: string | null;
  reason: string | null;
  created_at: string; // ISO datetime
}
