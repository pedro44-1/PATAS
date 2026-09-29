import api from "./client";

export type UserRole = "admin" | "vet" | "receptionist";

export interface ClinicUser {
  id: number;
  clinic_id: number;
  name: string;
  email: string;
  role: UserRole;
  clinic_name: string;
  must_change_password: boolean;
}

export interface CreateClinicUser {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export const usersApi = {
  list: () => api.get<ClinicUser[]>("/users/"),
  create: (data: CreateClinicUser) => api.post<ClinicUser>("/users/", data),
  updateRole: (id: number, role: UserRole) => api.patch<ClinicUser>(`/users/${id}/role`, { role }),
};
