import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FormSelect } from "./form-select";

describe("FormSelect", () => {
  it("opens its portalled options and reports the selected value", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();

    render(
      <FormSelect
        ariaLabel="Animal"
        value="zara"
        onValueChange={onValueChange}
        options={[
          { value: "zara", label: "Zara" },
          { value: "duke", label: "Duke" },
        ]}
      />,
    );

    await user.click(screen.getByRole("combobox", { name: "Animal" }));
    expect(screen.getByText("Duke")).toBeVisible();

    await user.click(screen.getByText("Duke"));
    expect(onValueChange).toHaveBeenCalledWith("duke");
  });

  it("supports a workflow action at the end of the options", async () => {
    const user = userEvent.setup();
    const onValueChange = vi.fn();

    render(
      <FormSelect
        ariaLabel="Animal"
        value="zara"
        onValueChange={onValueChange}
        options={[
          { value: "__create_pet__", label: "Registar novo animal", variant: "action" },
          { value: "zara", label: "Zara" },
        ]}
      />,
    );

    await user.click(screen.getByRole("combobox", { name: "Animal" }));
    await user.click(screen.getByRole("option", { name: "Registar novo animal" }));

    expect(onValueChange).toHaveBeenCalledWith("__create_pet__");
  });
});
