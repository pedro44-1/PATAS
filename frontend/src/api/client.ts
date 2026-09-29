import axios, { AxiosRequestConfig } from "axios";
import type { Token, UserResponse } from "@patas/shared-types";

type RetriableRequestConfig = AxiosRequestConfig & {
  _retry?: boolean;
};

let refreshPromise: Promise<Token> | null = null;

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

function isAuthenticationEndpoint(url?: string) {
  return ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout", "/auth/change-password"]
    .some((endpoint) => url?.includes(endpoint));
}

function refreshAccessToken(refreshToken: string) {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<Token>("/api/v1/auth/refresh", { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem("patas_token", data.access_token);
        localStorage.setItem("patas_refresh_token", data.refresh_token);
        return data;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("patas_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as RetriableRequestConfig | undefined;
    const refreshToken = localStorage.getItem("patas_refresh_token");
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      refreshToken &&
      !isAuthenticationEndpoint(original.url)
    ) {
      original._retry = true;
      try {
        const refreshed = await refreshAccessToken(refreshToken);
        original.headers = {
          ...original.headers,
          Authorization: `Bearer ${refreshed.access_token}`,
        };
        return api(original);
      } catch {
        // Fall through to the normal session cleanup below.
      }
    }
    if (error.response?.status === 401) {
      localStorage.removeItem("patas_token");
      localStorage.removeItem("patas_refresh_token");
      localStorage.removeItem("patas_user");
      window.location.href = "/login";
    }
    if (error.response?.status === 403 && error.response?.data?.detail === "PASSWORD_CHANGE_REQUIRED") {
      const storedUser = localStorage.getItem("patas_user");
      if (storedUser) {
        try {
          const user = JSON.parse(storedUser) as UserResponse;
          localStorage.setItem("patas_user", JSON.stringify({ ...user, must_change_password: true }));
        } catch {
          localStorage.removeItem("patas_user");
        }
      }
      if (window.location.pathname !== "/change-password") window.location.href = "/change-password";
    }
    return Promise.reject(error);
  }
);

export default api;
