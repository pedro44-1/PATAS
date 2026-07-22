// ─── User & Auth types ──────────────────────────────────────────────────────────

export type UserRole = "vet" | "receptionist" | "admin";

export interface UserResponse {
  id: number;
  clinic_id: number;
  name: string;
  email: string;
  role: UserRole;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRoleUpdate {
  role: UserRole;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenRefresh {
  refresh_token: string;
}

// Token payload (decoded JWT claims)
export interface TokenPayload {
  sub: string;        // user_id
  clinic_id: string;
  role: UserRole;
  exp: number;
  jti: string;
  type: "access" | "refresh";
}
