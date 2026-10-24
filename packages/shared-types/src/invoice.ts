export type InvoiceStatus = "draft" | "sent" | "paid" | "cancelled";
export type InvoiceSyncStatus = "pending" | "synced" | "failed";
export type PaymentMethod = "cash" | "bank-transfer" | "tpa" | "other";
export type InvoiceDocumentType = "FT" | "FR";
export type InvoiceLineKind = "SERVICE" | "PRODUCT";

export interface InvoiceLineCreate {
  description: string;
  code?: string;
  vat_profile_code?: string;
  kind: InvoiceLineKind;
  unit: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
}

export interface InvoiceLineResponse extends Omit<InvoiceLineCreate, "quantity" | "unit_price" | "tax_rate"> {
  id: number;
  quantity: string;
  unit_price: string;
  tax_rate: string;
  subtotal: string;
  tax_amount: string;
  total: string;
}

export interface InvoiceCreate {
  owner_id: number;
  appointment_id?: number;
  amount?: number;
  description?: string;
  items?: InvoiceLineCreate[];
  document_type?: InvoiceDocumentType;
  payment_method?: PaymentMethod;
  due_at?: string;
}

export interface InvoiceUpdate {
  status?: InvoiceStatus;
  amount?: number;
  description?: string;
  reason?: string;
  payment_method?: PaymentMethod;
}

export interface InvoiceResponse {
  id: number;
  clinic_id: number;
  owner_id: number;
  appointment_id: number | null;
  amount: number;
  subtotal: string;
  tax_total: string;
  status: InvoiceStatus;
  currency: string;
  description: string | null;
  document_type: InvoiceDocumentType;
  series: string | null;
  document_number: string | null;
  document_url: string | null;
  billing_external_id: string | null;
  idempotency_key: string | null;
  quote_id: string | null;
  quote_expires_at: string | null;
  quote_vat_configuration_version: string | null;
  quote_calculation_digest: string | null;
  quote_payable: string | null;
  provider_status: string | null;
  provider_mode: string | null;
  sync_attempts: number;
  last_sync_error: string | null;
  last_sync_at: string | null;
  payment_method: PaymentMethod | null;
  issued_at: string | null;
  due_at: string | null;
  paid_at: string | null;
  issuer_name: string | null;
  issuer_nif: string | null;
  issuer_address: string | null;
  issuer_phone: string | null;
  issuer_store_external_id: string | null;
  customer_name: string | null;
  customer_nif: string | null;
  customer_address: string | null;
  customer_phone: string | null;
  customer_email: string | null;
  reason: string | null;
  external_reference: string | null;
  sync_status: InvoiceSyncStatus;
  created_at: string;
  items: InvoiceLineResponse[];
}
