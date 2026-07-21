import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: "🏠" },
  { to: "/owners", label: "Donos", icon: "👤" },
  { to: "/pets", label: "Animais", icon: "🐾" },
  { to: "/appointments", label: "Consultas", icon: "📅" },
];

export default function Layout() {
  const { user } = useAuth();

  return (
    <div style={styles.shell}>
      <aside style={styles.sidebar}>
        <div style={styles.logoWrap}>
          <span style={styles.logoIcon}>🐾</span>
          <span style={styles.logoText}>PATAS</span>
        </div>

        <nav style={styles.nav}>
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
            >
              <span style={styles.navIcon}>{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div style={styles.userWrap}>
          <div style={styles.userAvatar}>{user?.name?.[0] ?? "V"}</div>
          <div>
            <div style={styles.userName}>{user?.name ?? "Veterinário"}</div>
            <div style={styles.userRole}>{user?.role === "vet" ? "Veterinário" : "Rececionista"}</div>
          </div>
        </div>
      </aside>

      <main style={styles.main}>
        <div style={styles.content}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  shell: { display: "flex", minHeight: "100vh" },
  sidebar: {
    width: 240,
    background: "#1a1a2e",
    display: "flex",
    flexDirection: "column",
    padding: "1.5rem 1rem",
    flexShrink: 0,
  },
  logoWrap: { display: "flex", alignItems: "center", gap: 10, marginBottom: "2.5rem", paddingLeft: "0.5rem" },
  logoIcon: { fontSize: "1.8rem" },
  logoText: { fontSize: "1.5rem", fontWeight: 800, color: "#fff", letterSpacing: 3 },
  nav: { display: "flex", flexDirection: "column", gap: "0.25rem", flex: 1 },
  navLink: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    color: "#9ca3af",
    textDecoration: "none",
    padding: "0.65rem 0.9rem",
    borderRadius: 10,
    fontSize: "0.95rem",
    fontWeight: 500,
    transition: "background 0.15s, color 0.15s",
  },
  navLinkActive: {
    background: "rgba(76, 175, 80, 0.15)",
    color: "#4caf50",
    fontWeight: 600,
  },
  navIcon: { fontSize: "1.1rem" },
  userWrap: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "0.75rem",
    borderRadius: 10,
    background: "rgba(255,255,255,0.05)",
  },
  userAvatar: {
    width: 36,
    height: 36,
    borderRadius: "50%",
    background: "#4caf50",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
    fontSize: "0.9rem",
    flexShrink: 0,
  },
  userName: { color: "#fff", fontSize: "0.9rem", fontWeight: 600 },
  userRole: { color: "#6b7280", fontSize: "0.75rem" },
  main: { flex: 1, background: "#f0f2f8", overflowY: "auto" },
  content: { padding: "2rem" },
};
