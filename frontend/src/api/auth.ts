import api from "./client";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role: "vet" | "receptionist";
}

export interface User {
  id: number;
  clinic_id: number;
  name: string;
  email: string;
  role: "vet" | "receptionist";
}

export interface Token {
  access_token: string;
  token_type: string;
}

export const authApi = {
  login: (data: LoginPayload) =>
    api.post<Token>("/auth/login", data),

  register: (data: RegisterPayload) =>
    api.post<User>("/auth/register", data),

  me: () =>
    api.get<User>("/auth/me"),
};
