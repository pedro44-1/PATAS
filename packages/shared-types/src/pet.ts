// ─── Pet types ─────────────────────────────────────────────────────────────────

export type PetSpecies =
  | "Cão"
  | "Gato"
  | "Ave"
  | "Roedor"
  | "Coelho"
  | "Réptil"
  | "Outro";

export interface PetCreate {
  owner_id: number;
  name: string;
  species: string;
  breed?: string;
  birth_date?: string; // ISO date "YYYY-MM-DD"
  weight?: number;
  notes?: string;
}

export interface PetUpdate {
  name?: string;
  species?: string;
  breed?: string;
  birth_date?: string;
  weight?: number;
  notes?: string;
}

export interface PetResponse {
  id: number;
  clinic_id: number;
  owner_id: number;
  name: string;
  species: string;
  breed: string | null;
  birth_date: string | null;
  weight: number | null;
  notes: string | null;
  created_at: string; // ISO datetime
}
