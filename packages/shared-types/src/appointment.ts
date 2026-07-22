// ─── Appointment types ──────────────────────────────────────────────────────────

export type AppointmentStatus = "scheduled" | "completed" | "cancelled" | "no-show";

export interface AppointmentCreate {
  pet_id: number;
  vet_id: number;
  scheduled_at: string; // ISO datetime
  duration_min?: number;
  reason?: string;
  notes?: string;
  weight?: number;
}

export interface AppointmentUpdate {
  scheduled_at?: string;
  duration_min?: number;
  status?: AppointmentStatus;
  reason?: string;
  notes?: string;
  weight?: number;
}

export interface AppointmentResponse {
  id: number;
  clinic_id: number;
  pet_id: number;
  vet_id: number;
  owner_id: number;
  scheduled_at: string; // ISO datetime
  duration_min: number;
  status: AppointmentStatus;
  reason: string | null;
  notes: string | null;
  weight: number | null;
  created_at: string; // ISO datetime
}
