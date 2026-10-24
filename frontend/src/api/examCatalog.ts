import api from "./client";
import type { ExamCatalog, ExamFinding, ExamSystem } from "@patas/shared-types";

export const examCatalogApi = {
  get: () => api.get<ExamCatalog>("/exam-catalog/"),
  createSystem: (data: { name: string; sort_order?: number }) => api.post<ExamSystem>("/exam-catalog/systems", data),
  updateSystem: (id: number, data: { name?: string; sort_order?: number; active?: boolean }) => api.patch<ExamSystem>(`/exam-catalog/systems/${id}`, data),
  createFinding: (systemId: number, data: { name: string; sort_order?: number }) => api.post<ExamFinding>(`/exam-catalog/systems/${systemId}/findings`, data),
  updateFinding: (id: number, data: { name?: string; sort_order?: number; active?: boolean }) => api.patch<ExamFinding>(`/exam-catalog/findings/${id}`, data),
};
