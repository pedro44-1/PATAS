import { Navigate } from "react-router-dom";

import type { UserRole } from "@patas/shared-types";
import { useAuth } from "../contexts/AuthContext";

export default function RoleRoute({ roles, children }: { roles: UserRole[]; children: JSX.Element }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}
