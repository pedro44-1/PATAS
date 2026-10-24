import api from "./client";

export interface Clinic {
  id: number;
  name: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  nif: string | null;
  billing_store_external_id: string | null;
}

export const clinicsApi = {
  get: () => api.get<Clinic>("/clinics/me"),
  update: (data: Partial<Omit<Clinic, "id">>) => api.patch<Clinic>("/clinics/me", data),
};
