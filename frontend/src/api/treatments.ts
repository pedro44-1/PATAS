import api from "./client";

export interface Treatment {
  id: number;
  clinic_id: number;
  appointment_id: number;
  diagnosis: string | null;
  notes: string | null;
  prescription: string | null;
  created_at: string;
}

export interface TreatmentCreate {
  appointment_id: number;
  diagnosis?: string;
  notes?: string;
  prescription?: string;
}

export const treatmentsApi = {
  list: (appointmentId?: number) =>
    api.get<Treatment[]>("/treatments/", { params: appointmentId ? { appointment_id: appointmentId } : {} }),
  create: (data: TreatmentCreate) =>
    api.post<Treatment>("/treatments/", data),
  update: (id: number, data: Partial<TreatmentCreate>) =>
    api.patch<Treatment>(`/treatments/${id}`, data),
  delete: (id: number) =>
    api.delete(`/treatments/${id}`),
};
