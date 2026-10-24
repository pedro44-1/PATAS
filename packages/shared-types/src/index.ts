// ─── Shared types barrel ──────────────────────────────────────────────────────────
// These types are the SINGLE SOURCE OF TRUTH for both backend (Pydantic)
// and frontend (TypeScript). When a backend schema changes, update these types
// and the frontend API layer automatically stays in sync.

export * from "./user.js";
export * from "./owner.js";
export * from "./pet.js";
export * from "./appointment.js";
export * from "./treatment.js";
export * from "./invoice.js";
export * from "./service-type.js";
export * from "./waiting-room.js";
export * from "./clinical.js";

// ─── Common / utility types ─────────────────────────────────────────────────────

/** Standard paginated API response wrapper */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/** Standard API error shape */
export interface ApiError {
  detail: string;
  status_code?: number;
}

/** Dashboard stats returned by GET /dashboard/stats */
export interface DashboardStats {
  total_pets: number;
  total_owners: number;
  total_appointments: number;
  total_treatments: number;
  upcoming_appointments: import("./appointment.js").AppointmentResponse[];
}
