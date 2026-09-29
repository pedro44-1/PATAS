import type {
  ClinicRegistration,
  LogoutRequest,
  PasswordChange,
  Token,
  UserLogin,
  UserResponse,
} from "@patas/shared-types";
import api from "./client";

export type LoginPayload = UserLogin;
export type RegisterPayload = ClinicRegistration;
export type User = UserResponse;
export type { Token };

export const authApi = {
  login: (data: LoginPayload) =>
    api.post<Token>("/auth/login", data),

  register: (data: RegisterPayload) =>
    api.post<User>("/auth/register", data),

  me: () =>
    api.get<User>("/auth/me"),

  changePassword: (data: PasswordChange) =>
    api.post<Token>("/auth/change-password", data),

  logout: (data: LogoutRequest) =>
    api.post<{ ok: boolean; message: string }>("/auth/logout", data),
};
