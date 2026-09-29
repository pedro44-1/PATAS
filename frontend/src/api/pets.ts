import api from "./client";
import type { Medication, Vaccination } from "./clinical";

export interface Pet {
  id: number;
  clinic_id: number;
  owner_id: number;
  name: string;
  species: string;
  breed: string | null;
  birth_date: string | null;
  weight: number | null;
  notes: string | null;
  archived_at: string | null;
  archived_by_user_id: number | null;
  created_at: string;
}

export interface PetCreate {
  owner_id: number;
  name: string;
  species: string;
  breed?: string;
  birth_date?: string;
  weight?: number;
  notes?: string;
}

export interface PetHistoryTreatment {
  id: number;
  created_at: string;
  diagnosis: string | null;
  prescription: string | null;
  notes: string | null;
  anamnesis: string | null;
  consultation_type: string;
  referring_vet_id: number | null;
  updated_at: string | null;
}

export interface PetHistoryExamFinding {
  id: number;
  appointment_id: number;
  finding_id: number;
  finding_name: string;
  system_id: number;
  system_name: string;
  status: "normal" | "abnormal" | "not-evaluated";
  note: string | null;
}

export interface PetHistoryAppointment {
  id: number;
  scheduled_at: string;
  vet_id: number;
  reason: string | null;
  status: "scheduled" | "in-progress" | "completed" | "cancelled" | "no-show";
  status_reason: string | null;
  weight: number | null;
  notes: string | null;
  treatment: PetHistoryTreatment | null;
  service_type_id: number | null;
  service_type_name: string | null;
  exam_findings: PetHistoryExamFinding[];
}

export const petsApi = {
  list: (includeArchived = false) => api.get<Pet[]>("/pets/", { params: { include_archived: includeArchived } }),
  create: (data: PetCreate) => api.post<Pet>("/pets/", data),
  get: (id: number) => api.get<Pet>(`/pets/${id}`),
  history: (id: number) => api.get<{
    pet_id: number;
    appointments: PetHistoryAppointment[];
    vaccinations: Vaccination[];
    medications: Medication[];
  }>(`/pets/${id}/history`),
  update: (id: number, data: Partial<PetCreate>) =>
    api.patch<Pet>(`/pets/${id}`, data),
  delete: (id: number) => api.delete(`/pets/${id}`),
};
