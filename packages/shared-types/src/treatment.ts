// ─── Treatment types ────────────────────────────────────────────────────────────

export interface TreatmentCreate {
  appointment_id: number;
  diagnosis?: string;
  notes?: string;
  prescription?: string;
}

export interface TreatmentUpdate {
  diagnosis?: string;
  notes?: string;
  prescription?: string;
}

export interface TreatmentResponse {
  id: number;
  clinic_id: number;
  appointment_id: number;
  diagnosis: string | null;
  notes: string | null;
  prescription: string | null;
  created_at: string; // ISO datetime
}
