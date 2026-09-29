import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProtectedRoute from "./ProtectedRoute";

const authState = vi.hoisted(() => ({
  isAuthenticated: true,
  user: { must_change_password: false },
}));

vi.mock("../contexts/AuthContext", () => ({
  useAuth: () => authState,
}));

function renderRoute(allowPasswordChange = false) {
  return render(
    <MemoryRouter initialEntries={[allowPasswordChange ? "/change-password" : "/private"]}>
      <Routes>
        <Route path="/login" element={<div>login</div>} />
        <Route path="/dashboard" element={<div>dashboard</div>} />
        <Route path="/change-password" element={
          <ProtectedRoute allowPasswordChange><div>change password</div></ProtectedRoute>
        } />
        <Route path="/private" element={
          <ProtectedRoute><div>private</div></ProtectedRoute>
        } />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    authState.isAuthenticated = true;
    authState.user = { must_change_password: false };
  });

  it("redirects unauthenticated users to login", () => {
    authState.isAuthenticated = false;
    renderRoute();
    expect(screen.getByText("login")).toBeInTheDocument();
  });

  it("forces temporary-password users into the password flow", () => {
    authState.user = { must_change_password: true };
    renderRoute();
    expect(screen.getByText("change password")).toBeInTheDocument();
  });

  it("keeps regular users out of the forced password route", () => {
    renderRoute(true);
    expect(screen.getByText("dashboard")).toBeInTheDocument();
  });
});
