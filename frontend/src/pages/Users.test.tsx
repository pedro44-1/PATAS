import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Users from "./Users";

const listUsers = vi.hoisted(() => vi.fn());

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: 2,
      clinic_id: 1,
      clinic_name: "Clínica",
      name: "Receção",
      email: "reception@test.ao",
      role: "receptionist",
      must_change_password: false,
    },
  }),
}));

vi.mock("@/api/users", () => ({
  usersApi: { list: listUsers },
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("Users role guard", () => {
  it("keeps team administration hidden from receptionists", () => {
    render(<Users />);
    expect(screen.getByText("users.restricted")).toBeInTheDocument();
    expect(screen.queryByText("users.create")).not.toBeInTheDocument();
    expect(listUsers).not.toHaveBeenCalled();
  });
});
