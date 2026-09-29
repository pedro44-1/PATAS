import api from "./client";

export interface Treatment {
  id: number;
  clinic_id: number;
  appointment_id: number;
  diagnosis: string | null;
  notes: string | null;
  prescription: string | null;
  anamnesis: string | null;
  consultation_type: string;
  referring_vet_id: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface TreatmentCreate {
  appointment_id: number;
  diagnosis?: string;
  notes?: string;
  prescription?: string;
  anamnesis?: string;
  consultation_type?: string;
  referring_vet_id?: number;
}

export const treatmentsApi = {
  list: (appointmentId?: number) =>
    api.get<Treatment[]>("/treatments/", { params: appointmentId ? { appointment_id: appointmentId } : {} }),
  create: (data: TreatmentCreate) =>
    api.post<Treatment>("/treatments/", data),
  update: (id: number, data: Partial<TreatmentCreate>) =>
    api.patch<Treatment>(`/treatments/${id}`, data),
};
