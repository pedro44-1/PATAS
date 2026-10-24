import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { afterEach, describe, expect, it } from "vitest";
import api from "./client";

describe("API session renewal", () => {
  const apiMock = new MockAdapter(api);
  const axiosMock = new MockAdapter(axios);

  afterEach(() => {
    apiMock.reset();
    axiosMock.reset();
  });

  it("rotates tokens once and retries an expired request", async () => {
    localStorage.setItem("patas_token", "expired-access");
    localStorage.setItem("patas_refresh_token", "valid-refresh");
    axiosMock.onPost("/api/v1/auth/refresh").reply(200, {
      access_token: "new-access",
      refresh_token: "new-refresh",
      token_type: "bearer",
      must_change_password: false,
    });
    apiMock.onGet("/owners/").replyOnce(401).onGet("/owners/").reply((config) => [
      config.headers?.Authorization === "Bearer new-access" ? 200 : 401,
      [],
    ]);

    const response = await api.get("/owners/");

    expect(response.status).toBe(200);
    expect(localStorage.getItem("patas_token")).toBe("new-access");
    expect(localStorage.getItem("patas_refresh_token")).toBe("new-refresh");
  });
});
