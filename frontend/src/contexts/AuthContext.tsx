import { createContext, useContext, useState, ReactNode } from "react";
import { authApi, Token, User } from "../api/auth";

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (tokens: Token, user: User) => void;
  logout: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => {},
  logout: async () => {},
  changePassword: async () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem("patas_user");
    if (!stored) return null;
    try {
      return JSON.parse(stored) as User;
    } catch {
      localStorage.removeItem("patas_user");
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("patas_token")
  );

  function login(tokens: Token, newUser: User) {
    localStorage.setItem("patas_token", tokens.access_token);
    localStorage.setItem("patas_refresh_token", tokens.refresh_token);
    localStorage.setItem("patas_user", JSON.stringify(newUser));
    setToken(tokens.access_token);
    setUser(newUser);
  }

  async function logout() {
    const refreshToken = localStorage.getItem("patas_refresh_token");
    try {
      if (refreshToken) await authApi.logout({ refresh_token: refreshToken });
    } finally {
      localStorage.removeItem("patas_token");
      localStorage.removeItem("patas_refresh_token");
      localStorage.removeItem("patas_user");
      setToken(null);
      setUser(null);
    }
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    const refreshToken = localStorage.getItem("patas_refresh_token");
    if (!refreshToken) throw new Error("missing-refresh-token");
    const tokenResponse = await authApi.changePassword({
      current_password: currentPassword,
      new_password: newPassword,
      refresh_token: refreshToken,
    });
    localStorage.setItem("patas_token", tokenResponse.data.access_token);
    localStorage.setItem("patas_refresh_token", tokenResponse.data.refresh_token);
    const userResponse = await authApi.me();
    login(tokenResponse.data, userResponse.data);
  }

  return (
    <AuthContext.Provider
      value={{ user, token, login, logout, changePassword, isAuthenticated: !!token }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
