import api from "./client";
import type { ClinicalRecord, ClinicalRecordUpdate, ExamFindingStatus } from "@patas/shared-types";

export interface ClinicalMedicationLineInput {
  id?: number;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  start_date: string;
  end_date?: string;
  instructions?: string;
  notes?: string;
}

export interface ClinicalRecordInput extends Omit<ClinicalRecordUpdate, "medications" | "exam_findings" | "referring_vet_id"> {
  referring_vet_id?: number | null;
  exam_findings: { finding_id: number; status: ExamFindingStatus; note?: string }[];
  medications: ClinicalMedicationLineInput[];
}

export const encountersApi = {
  get: (appointmentId: number) => api.get<ClinicalRecord>(`/appointments/${appointmentId}/clinical-record`),
  save: (appointmentId: number, data: ClinicalRecordInput) => api.put<ClinicalRecord>(`/appointments/${appointmentId}/clinical-record`, data),
};
