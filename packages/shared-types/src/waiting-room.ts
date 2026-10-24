export type WaitingRoomStatus = "waiting" | "called" | "in-progress" | "completed" | "cancelled" | "no-show";

export interface WaitingRoomEntry {
  id: number;
  clinic_id: number;
  appointment_id: number;
  pet_id: number;
  pet_name: string;
  owner_id: number;
  owner_name: string;
  vet_id: number;
  vet_name: string;
  service_type_id: number | null;
  service_type_name: string | null;
  scheduled_at: string;
  status: WaitingRoomStatus;
  arrival_at: string;
  called_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  room: string | null;
  message: string | null;
  status_reason: string | null;
  reason: string | null;
  notes: string | null;
}

export interface WaitingRoomEntryCreate {
  appointment_id?: number;
  pet_id?: number;
  vet_id?: number;
  service_type_id?: number;
  scheduled_at?: string;
  duration_min?: number;
  reason?: string;
  notes?: string;
  room?: string;
  message?: string;
}

export interface WaitingRoomTransition {
  status: WaitingRoomStatus;
  reason?: string;
}
