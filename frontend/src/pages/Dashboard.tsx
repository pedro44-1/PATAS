import { useEffect, useState } from "react";
import { appointmentsApi } from "../api/appointments";
import { petsApi } from "../api/pets";
import { ownersApi } from "../api/owners";
import { useAuth } from "../contexts/AuthContext";

interface Stats {
  totalPets: number;
  totalOwners: number;
  todayAppointments: number;
  pendingInvoices: number;
}

interface Appointment {
  id: number;
  pet_id: number;
  vet_id: number;
  scheduled_at: string;
  duration_min: number;
  status: string;
  notes: string | null;
}

export default function Dashboard() {
  const { user, logout } = useAuth();

  const [stats, setStats] = useState<Stats>({
    totalPets: 0,
    totalOwners: 0,
    todayAppointments: 0,
    pendingInvoices: 0,
  });
  const [todayAppts, setTodayAppts] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = new Date().toISOString().split("T")[0];
    Promise.all([
      petsApi.list(),
      ownersApi.list(),
      appointmentsApi.list(today),
    ]).then(([petsRes, ownersRes, apptsRes]) => {
      setStats({
        totalPets: petsRes.data.length,
        totalOwners: ownersRes.data.length,
        todayAppointments: apptsRes.data.length,
        pendingInvoices: 0,
      });
      setTodayAppts(apptsRes.data);
    }).catch(() => {
      // auth error handled by interceptor
    }).finally(() => setLoading(false));
  }, []);

  function greeting() {
    const h = new Date().getHours();
    if (h < 12) return "Bom dia";
    if (h < 18) return "Boa tarde";
    return "Boa noite";
  }

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>{greeting()}, {user?.name}</h1>
          <p style={styles.date}>{new Date().toLocaleDateString("pt-AO", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</p>
        </div>
        <button onClick={logout} style={styles.logoutBtn}>Sair</button>
      </div>

      <div style={styles.grid}>
        <StatCard label="Animais registados" value={stats.totalPets} icon="🐶" />
        <StatCard label="Donos" value={stats.totalOwners} icon="👤" />
        <StatCard label="Consultas hoje" value={stats.todayAppointments} icon="📅" />
        <StatCard label="Faturas pendentes" value={stats.pendingInvoices} icon="📄" />
      </div>

      <h2 style={styles.sectionTitle}>Consultas de hoje</h2>
      <div style={styles.card}>
        {loading ? (
          <p style={styles.empty}>A carregar...</p>
        ) : todayAppts.length === 0 ? (
          <p style={styles.empty}>Nenhuma consulta hoje</p>
        ) : (
          todayAppts.map((appt) => (
            <div key={appt.id} style={styles.apptRow}>
              <div>
                <div style={styles.apptTime}>
                  {new Date(appt.scheduled_at).toLocaleTimeString("pt-AO", { hour: "2-digit", minute: "2-digit" })}
                </div>
                <div style={styles.apptDuration}>{appt.duration_min} min</div>
              </div>
              <div>
                <span style={{ ...styles.badge, background: statusBg(appt.status), color: statusColor(appt.status) }}>
                  {statusLabel(appt.status)}
                </span>
              </div>
              <div style={styles.apptNotes}>{appt.notes || "Sem notas"}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: string }) {
  return (
    <div style={styles.statCard}>
      <span style={styles.statIcon}>{icon}</span>
      <div>
        <div style={styles.statValue}>{value}</div>
        <div style={styles.statLabel}>{label}</div>
      </div>
    </div>
  );
}

function statusBg(s: string) {
  return s === "completed" ? "#dcfce7" : s === "cancelled" ? "#fee2e2" : "#fef9c3";
}
function statusColor(s: string) {
  return s === "completed" ? "#16a34a" : s === "cancelled" ? "#dc2626" : "#ca8a04";
}
function statusLabel(s: string) {
  return s === "completed" ? "Concluída" : s === "cancelled" ? "Cancelada" : "Agendada";
}

const styles: Record<string, React.CSSProperties> = {
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "2rem" },
  title: { fontSize: "1.75rem", fontWeight: 700, color: "#1a1a2e", margin: 0 },
  date: { color: "#888", marginTop: 4, fontSize: "0.9rem", textTransform: "capitalize" },
  logoutBtn: { padding: "0.5rem 1.2rem", background: "#fee2e2", color: "#dc2626", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600 },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "2rem" },
  statCard: { background: "#fff", borderRadius: 14, padding: "1.5rem", display: "flex", alignItems: "center", gap: "1rem", boxShadow: "0 2px 8px rgba(0,0,0,0.06)", transition: "transform 0.1s", cursor: "pointer" },
  statIcon: { fontSize: "2rem" },
  statValue: { fontSize: "2rem", fontWeight: 800, color: "#1a1a2e", lineHeight: 1 },
  statLabel: { color: "#888", fontSize: "0.85rem", marginTop: 4 },
  sectionTitle: { fontSize: "1.25rem", fontWeight: 700, color: "#1a1a2e", marginBottom: "1rem" },
  card: { background: "#fff", borderRadius: 14, padding: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.06)" },
  empty: { color: "#aaa", textAlign: "center", padding: "2rem", fontSize: "0.95rem" },
  apptRow: { display: "flex", alignItems: "center", gap: "1rem", padding: "0.75rem 0", borderBottom: "1px solid #f0f0f0" },
  apptTime: { fontWeight: 700, fontSize: "1rem", color: "#1a1a2e" },
  apptDuration: { fontSize: "0.8rem", color: "#888" },
  badge: { padding: "0.25rem 0.75rem", borderRadius: 20, fontSize: "0.8rem", fontWeight: 600 },
  apptNotes: { flex: 1, color: "#666", fontSize: "0.9rem" },
};
