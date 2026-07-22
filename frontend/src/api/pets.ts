import api from "./client";

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

export const petsApi = {
  list: () => api.get<Pet[]>("/pets/"),
  create: (data: PetCreate) => api.post<Pet>("/pets/", data),
  get: (id: number) => api.get<Pet>(`/pets/${id}`),
  update: (id: number, data: Partial<PetCreate>) =>
    api.patch<Pet>(`/pets/${id}`, data),
  delete: (id: number) => api.delete(`/pets/${id}`),
};
