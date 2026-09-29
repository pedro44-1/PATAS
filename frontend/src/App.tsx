import { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const PasswordChange = lazy(() => import("./pages/PasswordChange"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Owners = lazy(() => import("./pages/Owners"));
const Pets = lazy(() => import("./pages/Pets"));
const PetDetail = lazy(() => import("./pages/PetDetail"));
const Appointments = lazy(() => import("./pages/Appointments"));
const ClinicalAppointment = lazy(() => import("./pages/ClinicalAppointment"));
const WaitingRoom = lazy(() => import("./pages/WaitingRoom"));
const Treatments = lazy(() => import("./pages/Treatments"));
const Invoices = lazy(() => import("./pages/Invoices"));
const Users = lazy(() => import("./pages/Users"));
const Settings = lazy(() => import("./pages/Settings"));

function RouteLoading() {
  const { t } = useTranslation();

  return (
    <div
      className="flex min-h-screen items-center justify-center bg-background text-muted-foreground"
      role="status"
    >
      <div className="flex items-center gap-3 text-sm font-medium">
        <span
          className="size-5 animate-spin rounded-full border-2 border-primary/30 border-t-primary"
          aria-hidden="true"
        />
        {t("common.loading")}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<RouteLoading />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/change-password" element={<ProtectedRoute allowPasswordChange><PasswordChange /></ProtectedRoute>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="owners" element={<Owners />} />
              <Route path="pets" element={<Pets />} />
              <Route path="pets/:id" element={<PetDetail />} />
              <Route path="appointments" element={<Appointments />} />
              <Route path="appointments/:id/clinical" element={<ClinicalAppointment />} />
              <Route path="waiting-room" element={<WaitingRoom />} />
              <Route path="treatments" element={<Treatments />} />
              <Route path="invoices" element={<Invoices />} />
              <Route path="users" element={<Users />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}
