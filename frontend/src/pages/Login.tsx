import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokenRes = await authApi.login({ email, password });
      const token = tokenRes.data.access_token;
      // Save token to localStorage BEFORE /me so the interceptor can attach it
      localStorage.setItem("patas_token", token);
      const userRes = await authApi.me();
      login(token, userRes.data);
      navigate("/dashboard");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Credenciais inválidas. Tente novamente."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <span style={styles.logoIcon}>🐾</span>
          <span style={styles.logoText}>PATAS</span>
        </div>
        <p style={styles.subtitle}>Sistema de Gestão Veterinária</p>
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="veterinario@clinica.ao"
              style={styles.input}
              required
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Palavra-passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={styles.input}
              required
            />
          </div>
          {error && <div style={styles.error}>{error}</div>}
          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? "A entrar..." : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "100vh",
    background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
  },
  card: {
    width: 380,
    padding: "2.5rem",
    background: "#fff",
    borderRadius: 16,
    boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    marginBottom: 4,
  },
  logoIcon: { fontSize: "2.5rem" },
  logoText: {
    fontSize: "2rem",
    fontWeight: 800,
    color: "#1a1a2e",
    letterSpacing: 2,
  },
  subtitle: {
    textAlign: "center",
    color: "#888",
    marginBottom: "2rem",
    fontSize: "0.9rem",
  },
  form: { display: "flex", flexDirection: "column", gap: "1.2rem" },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  label: { fontSize: "0.85rem", fontWeight: 600, color: "#333" },
  input: {
    padding: "0.75rem 1rem",
    border: "1.5px solid #e0e0e0",
    borderRadius: 10,
    fontSize: "1rem",
    outline: "none",
    transition: "border-color 0.2s",
    boxSizing: "border-box",
  },
  error: {
    padding: "0.75rem",
    background: "#fee2e2",
    color: "#dc2626",
    borderRadius: 8,
    fontSize: "0.9rem",
    textAlign: "center",
  },
  button: {
    padding: "0.85rem",
    background: "linear-gradient(135deg, #4caf50, #2e7d32)",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    fontSize: "1rem",
    fontWeight: 700,
    cursor: "pointer",
    transition: "opacity 0.2s",
  },
};
