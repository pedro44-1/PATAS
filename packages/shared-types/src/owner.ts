// ─── Owner types ────────────────────────────────────────────────────────────────

export interface OwnerCreate {
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  notes?: string;
}

export interface OwnerUpdate {
  name?: string;
  phone?: string;
  email?: string;
  address?: string;
  notes?: string;
}

export interface OwnerResponse {
  id: number;
  clinic_id: number;
  name: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  notes: string | null;
  archived_at: string | null;
  archived_by_user_id: number | null;
  created_at: string; // ISO datetime
}
