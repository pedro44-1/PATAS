import api from "./client";

export type AppointmentStatus = "scheduled" | "in-progress" | "completed" | "cancelled" | "no-show";

export interface VetOption {
  id: number;
  name: string;
  role: "admin" | "vet" | "receptionist";
}

export interface Appointment {
  id: number;
  clinic_id: number;
  pet_id: number;
  vet_id: number;
  owner_id: number;
  scheduled_at: string;
  duration_min: number;
  status: AppointmentStatus;
  status_reason: string | null;
  reason: string | null;
  notes: string | null;
  weight: number | null;
  service_type_id: number | null;
  created_at: string;
}

export interface AppointmentCreate {
  pet_id: number;
  vet_id: number;
  scheduled_at: string;
  duration_min?: number;
  reason?: string;
  notes?: string;
  weight?: number;
  service_type_id?: number;
  status_reason?: string;
}

export const appointmentsApi = {
  list: (date?: string) =>
    api.get<Appointment[]>("/appointments/", { params: date ? { date } : {} }),
  vets: () => api.get<VetOption[]>("/appointments/vets"),
  create: (data: AppointmentCreate) =>
    api.post<Appointment>("/appointments/", data),
  get: (id: number) => api.get<Appointment>(`/appointments/${id}`),
  update: (id: number, data: Partial<AppointmentCreate & { status: AppointmentStatus }>) =>
    api.patch<Appointment>(`/appointments/${id}`, data),
  delete: (id: number) => api.delete(`/appointments/${id}`),
};
