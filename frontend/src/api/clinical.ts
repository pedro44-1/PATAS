import api from "./client";

export type VaccinationStatus = "administered" | "voided";
export type MedicationStatus = "active" | "completed" | "cancelled" | "voided";

export interface Vaccination {
  id: number;
  clinic_id: number;
  pet_id: number;
  appointment_id: number | null;
  vet_id: number;
  vet_name: string | null;
  name: string;
  administered_at: string;
  dose: string;
  lot_number: string | null;
  expires_at: string | null;
  next_due_at: string | null;
  notes: string | null;
  status: VaccinationStatus;
  void_reason: string | null;
  voided_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Medication {
  id: number;
  clinic_id: number;
  pet_id: number;
  appointment_id: number | null;
  vet_id: number;
  vet_name: string | null;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  start_date: string;
  end_date: string | null;
  instructions: string | null;
  notes: string | null;
  status: MedicationStatus;
  void_reason: string | null;
  voided_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface VaccinationCreate {
  pet_id: number;
  vet_id: number;
  appointment_id?: number;
  name: string;
  administered_at: string;
  dose: string;
  lot_number?: string;
  expires_at?: string;
  next_due_at?: string;
  notes?: string;
}

export interface MedicationCreate {
  pet_id: number;
  vet_id: number;
  appointment_id?: number;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  start_date: string;
  end_date?: string;
  instructions?: string;
  notes?: string;
}

export interface ClinicalVoidRequest {
  reason: string;
}

export const clinicalApi = {
  vaccinations: (petId?: number) =>
    api.get<Vaccination[]>("/vaccinations/", { params: petId ? { pet_id: petId } : {} }),
  createVaccination: (data: VaccinationCreate) =>
    api.post<Vaccination>("/vaccinations/", data),
  updateVaccination: (id: number, data: Partial<VaccinationCreate>) =>
    api.patch<Vaccination>(`/vaccinations/${id}`, data),
  voidVaccination: (id: number, data: ClinicalVoidRequest) =>
    api.post<Vaccination>(`/vaccinations/${id}/void`, data),
  medications: (petId?: number) =>
    api.get<Medication[]>("/medications/", { params: petId ? { pet_id: petId } : {} }),
  createMedication: (data: MedicationCreate) =>
    api.post<Medication>("/medications/", data),
  updateMedication: (id: number, data: Partial<MedicationCreate> & { status?: MedicationStatus }) =>
    api.patch<Medication>(`/medications/${id}`, data),
  voidMedication: (id: number, data: ClinicalVoidRequest) =>
    api.post<Medication>(`/medications/${id}/void`, data),
};
