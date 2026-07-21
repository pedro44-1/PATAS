import api from "./client";

export type AppointmentStatus = "scheduled" | "completed" | "cancelled";

export interface Appointment {
  id: number;
  clinic_id: number;
  pet_id: number;
  vet_id: number;
  scheduled_at: string;
  duration_min: number;
  status: AppointmentStatus;
  notes: string | null;
  created_at: string;
}

export interface AppointmentCreate {
  pet_id: number;
  vet_id: number;
  scheduled_at: string;
  duration_min?: number;
  notes?: string;
}

export const appointmentsApi = {
  list: (date?: string) =>
    api.get<Appointment[]>("/appointments/", { params: date ? { date } : {} }),
  create: (data: AppointmentCreate) =>
    api.post<Appointment>("/appointments/", data),
  get: (id: number) => api.get<Appointment>(`/appointments/${id}`),
  update: (id: number, data: Partial<AppointmentCreate & { status: AppointmentStatus }>) =>
    api.patch<Appointment>(`/appointments/${id}`, data),
  delete: (id: number) => api.delete(`/appointments/${id}`),
};
