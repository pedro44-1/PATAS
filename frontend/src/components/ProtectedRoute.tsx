import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function ProtectedRoute({ children, allowPasswordChange = false }: { children: JSX.Element; allowPasswordChange?: boolean }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (user?.must_change_password && !allowPasswordChange) {
    return <Navigate to="/change-password" replace />;
  }
  if (!user?.must_change_password && allowPasswordChange) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}
