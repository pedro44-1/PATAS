// ─── Appointment types ──────────────────────────────────────────────────────────

export type AppointmentStatus = "scheduled" | "in-progress" | "completed" | "cancelled" | "no-show";

export interface AppointmentCreate {
  pet_id: number;
  vet_id: number;
  scheduled_at: string; // ISO datetime
  duration_min?: number;
  reason?: string;
  notes?: string;
  weight?: number;
  status_reason?: string;
  service_type_id?: number;
}

export interface AppointmentUpdate {
  pet_id?: number;
  vet_id?: number;
  scheduled_at?: string;
  duration_min?: number;
  status?: AppointmentStatus;
  status_reason?: string;
  reason?: string;
  notes?: string;
  weight?: number;
  service_type_id?: number;
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
  status_reason: string | null;
  reason: string | null;
  notes: string | null;
  weight: number | null;
  service_type_id: number | null;
  created_at: string; // ISO datetime
}
