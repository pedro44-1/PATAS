import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";

const logoutRequest = vi.hoisted(() => vi.fn().mockResolvedValue({ data: { ok: true } }));

vi.mock("../api/auth", () => ({
  authApi: {
    logout: logoutRequest,
  },
}));

function LogoutButton() {
  const { logout } = useAuth();
  return <button onClick={() => void logout()}>logout</button>;
}

describe("AuthProvider logout", () => {
  beforeEach(() => {
    logoutRequest.mockClear();
    localStorage.setItem("patas_token", "access");
    localStorage.setItem("patas_refresh_token", "refresh");
    localStorage.setItem("patas_user", JSON.stringify({
      id: 1,
      clinic_id: 1,
      clinic_name: "Clínica",
      name: "Admin",
      email: "admin@test.ao",
      role: "admin",
      must_change_password: false,
    }));
  });

  it("revokes the refresh token and clears local session data", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    render(<AuthProvider><LogoutButton /></AuthProvider>);
    await userEvent.click(screen.getByRole("button", { name: "logout" }));
    await waitFor(() => expect(logoutRequest).toHaveBeenCalledWith({ refresh_token: "refresh" }));
    expect(localStorage.getItem("patas_token")).toBeNull();
    expect(localStorage.getItem("patas_refresh_token")).toBeNull();
    expect(localStorage.getItem("patas_user")).toBeNull();
  });
});
