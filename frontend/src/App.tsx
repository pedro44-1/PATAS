import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Owners from "./pages/Owners";
import Pets from "./pages/Pets";
import PetDetail from "./pages/PetDetail";
import Appointments from "./pages/Appointments";
import Treatments from "./pages/Treatments";
import Invoices from "./pages/Invoices";
import Layout from "./components/Layout";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
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
            <Route path="treatments" element={<Treatments />} />
            <Route path="invoices" element={<Invoices />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
