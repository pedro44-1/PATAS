import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import axios from "axios";
import { describe, expect, it, vi } from "vitest";
import Owners from "./Owners";

const ownersApi = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("@/api/owners", () => ({ ownersApi }));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("Owners form errors", () => {
  it("shows the backend error inside the open modal", async () => {
    ownersApi.list.mockResolvedValue({ data: [] });
    ownersApi.create.mockRejectedValue(
      new axios.AxiosError("conflict", undefined, undefined, undefined, {
        status: 409,
        statusText: "",
        headers: {},
        config: { headers: {} } as never,
        data: { detail: "Já existe um dono com este NIF" },
      }),
    );

    render(<Owners />);
    await waitFor(() => expect(ownersApi.list).toHaveBeenCalled());
    fireEvent.click(screen.getByText("owners.new"));
    const nameInput = screen.getAllByPlaceholderText("owners.form.name")[0];
    fireEvent.change(nameInput, { target: { value: "Maria" } });
    const form = nameInput.closest("form") as HTMLFormElement;
    fireEvent.submit(form);

    const alert = await within(form).findByRole("alert");
    expect(alert).toHaveTextContent("Já existe um dono com este NIF");
  });
});
