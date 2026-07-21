import api from "./client";

export interface Owner {
  id: number;
  clinic_id: number;
  name: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  notes: string | null;
  created_at: string;
}

export interface OwnerCreate {
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  notes?: string;
}

export const ownersApi = {
  list: () => api.get<Owner[]>("/owners/"),
  create: (data: OwnerCreate) => api.post<Owner>("/owners/", data),
  get: (id: number) => api.get<Owner>(`/owners/${id}`),
  update: (id: number, data: Partial<OwnerCreate>) =>
    api.patch<Owner>(`/owners/${id}`, data),
  delete: (id: number) => api.delete(`/owners/${id}`),
};
