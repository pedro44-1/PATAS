export interface ServiceType {
  id: number;
  clinic_id: number;
  name: string;
  slug: string;
  sort_order: number;
  active: boolean;
  created_at: string;
}

export interface ServiceTypeCreate {
  name: string;
  sort_order?: number;
}

export interface ServiceTypeUpdate {
  name?: string;
  sort_order?: number;
  active?: boolean;
}
