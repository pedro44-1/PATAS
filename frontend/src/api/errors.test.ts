import axios from "axios";
import { describe, expect, it } from "vitest";
import { apiErrorMessage } from "./errors";

const translate = ((key: string) => key) as never;

describe("apiErrorMessage", () => {
  it.each([
    [401, "apiErrors.sessionExpired"],
    [403, "apiErrors.forbidden"],
    [409, "apiErrors.conflict"],
    [422, "apiErrors.validation"],
  ])("maps HTTP %s to a localized message", (status, key) => {
    const error = new axios.AxiosError("request failed", undefined, undefined, undefined, {
      status,
      statusText: "",
      headers: {},
      config: { headers: {} } as never,
      data: status === 422 ? { detail: [{ msg: "raw validation detail" }] } : {},
    });

    expect(apiErrorMessage(error, translate, "fallback")).toBe(key);
  });

  it("allows a flow-specific status message", () => {
    const error = new axios.AxiosError("request failed", undefined, undefined, undefined, {
      status: 401,
      statusText: "",
      headers: {},
      config: { headers: {} } as never,
      data: {},
    });

    expect(apiErrorMessage(error, translate, "fallback", { 401: "auth.loginError" }))
      .toBe("auth.loginError");
  });
});
