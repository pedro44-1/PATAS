import api from "./client";
import type { PageParams } from "./pagination";

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
  pet_name?: string | null;
  owner_name?: string | null;
  vet_name?: string | null;
  subject_archived?: boolean;
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

export interface AppointmentListFilters extends PageParams {
  dateFrom?: string;
  dateTo?: string;
  petId?: number;
  ownerId?: number;
  status?: AppointmentStatus;
  order?: "asc" | "desc";
}

export const appointmentsApi = {
  list: (filter?: string | AppointmentListFilters) => {
    const params = typeof filter === "string"
      ? { date: filter }
      : filter
        ? {
          date_from: filter.dateFrom,
          date_to: filter.dateTo,
          pet_id: filter.petId,
          owner_id: filter.ownerId,
          status: filter.status,
          order: filter.order,
          q: filter.q,
          skip: filter.skip,
          limit: filter.limit,
        }
        : {};
    return api.get<Appointment[]>("/appointments/", { params });
  },
  vets: () => api.get<VetOption[]>("/appointments/vets"),
  create: (data: AppointmentCreate) =>
    api.post<Appointment>("/appointments/", data),
  get: (id: number) => api.get<Appointment>(`/appointments/${id}`),
  update: (id: number, data: Partial<AppointmentCreate & { status: AppointmentStatus }>) =>
    api.patch<Appointment>(`/appointments/${id}`, data),
  delete: (id: number) => api.delete(`/appointments/${id}`),
};
