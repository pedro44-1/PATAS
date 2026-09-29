export type ExamFindingStatus = "normal" | "abnormal" | "not-evaluated";

export interface ExamFinding {
  id: number;
  clinic_id: number;
  system_id: number;
  name: string;
  sort_order: number;
  active: boolean;
  created_at: string;
}

export interface ExamSystem {
  id: number;
  clinic_id: number;
  name: string;
  sort_order: number;
  active: boolean;
  created_at: string;
  findings: ExamFinding[];
}

export interface ExamCatalog {
  systems: ExamSystem[];
}

export interface ExamObservation {
  id: number;
  appointment_id: number;
  finding_id: number;
  finding_name: string;
  system_id: number;
  system_name: string;
  status: ExamFindingStatus;
  note: string | null;
}

export interface ClinicalMedicationLine {
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

export interface ClinicalTreatment {
  id: number;
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

export interface ClinicalRecord {
  appointment_id: number;
  treatment: ClinicalTreatment | null;
  exam_findings: ExamObservation[];
  medications: ClinicalMedicationLine[];
}

export interface ClinicalRecordUpdate {
  anamnesis?: string;
  diagnosis?: string;
  notes?: string;
  prescription?: string;
  consultation_type?: string;
  referring_vet_id?: number;
  exam_findings: { finding_id: number; status: ExamFindingStatus; note?: string }[];
  medications: ClinicalMedicationLine[];
}
