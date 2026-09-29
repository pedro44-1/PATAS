// ─── Treatment types ────────────────────────────────────────────────────────────

export interface TreatmentCreate {
  appointment_id: number;
  diagnosis?: string;
  notes?: string;
  prescription?: string;
  anamnesis?: string;
  consultation_type?: string;
  referring_vet_id?: number;
}

export interface TreatmentUpdate {
  diagnosis?: string;
  notes?: string;
  prescription?: string;
  anamnesis?: string;
  consultation_type?: string;
  referring_vet_id?: number;
}

export interface TreatmentResponse {
  id: number;
  clinic_id: number;
  appointment_id: number;
  diagnosis: string | null;
  notes: string | null;
  prescription: string | null;
  anamnesis: string | null;
  consultation_type: string;
  referring_vet_id: number | null;
  created_at: string; // ISO datetime
  updated_at: string | null;
}
