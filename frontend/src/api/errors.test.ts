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

  it("prefers a human-readable backend detail over the generic status message", () => {
    const error = new axios.AxiosError("request failed", undefined, undefined, undefined, {
      status: 409,
      statusText: "",
      headers: {},
      config: { headers: {} } as never,
      data: { detail: "O veterinário já tem uma consulta nesse horário" },
    });

    expect(apiErrorMessage(error, translate, "fallback"))
      .toBe("O veterinário já tem uma consulta nesse horário");
  });

  it("keeps machine codes and session expiry localized", () => {
    const coded = new axios.AxiosError("request failed", undefined, undefined, undefined, {
      status: 403,
      statusText: "",
      headers: {},
      config: { headers: {} } as never,
      data: { detail: "PASSWORD_CHANGE_REQUIRED" },
    });
    const expired = new axios.AxiosError("request failed", undefined, undefined, undefined, {
      status: 401,
      statusText: "",
      headers: {},
      config: { headers: {} } as never,
      data: { detail: "Token inválido ou expirado" },
    });

    expect(apiErrorMessage(coded, translate, "fallback")).toBe("apiErrors.forbidden");
    expect(apiErrorMessage(expired, translate, "fallback")).toBe("apiErrors.sessionExpired");
  });
});
