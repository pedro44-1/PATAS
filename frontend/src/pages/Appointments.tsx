import { useEffect, useState } from "react";
import { appointmentsApi, Appointment, AppointmentCreate } from "../api/appointments";
import { petsApi, Pet } from "../api/pets";

export default function Appointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filterDate, setFilterDate] = useState(new Date().toISOString().split("T")[0]);
  const [form, setForm] = useState<AppointmentCreate>({ pet_id: 0, vet_id: 1, scheduled_at: "", duration_min: 30, notes: "" });

  function load() {
    Promise.all([appointmentsApi.list(filterDate), petsApi.list()])
      .then(([apptsRes, petsRes]) => {
        setAppointments(apptsRes.data);
        setPets(petsRes.data);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [filterDate]);

  function openCreate() {
    const defaultTime = `${filterDate}T09:00`;
    setForm({ pet_id: pets[0]?.id ?? 0, vet_id: 1, scheduled_at: defaultTime, duration_min: 30, notes: "" });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await appointmentsApi.create(form);
      setShowForm(false);
      load();
    } catch {}
  }

  async function handleStatus(id: number, status: string) {
    await appointmentsApi.update(id, { status: status as any });
    load();
  }

  async function handleDelete(id: number) {
    if (!confirm("Eliminar esta consulta?")) return;
    await appointmentsApi.delete(id);
    load();
  }

  function getPetName(id: number) {
    return pets.find((p) => p.id === id)?.name ?? "—";
  }

  function statusBadge(status: string) {
    const cfg = status === "completed"
      ? { bg: "#dcfce7", color: "#16a34a", label: "Concluída" }
      : status === "cancelled"
      ? { bg: "#fee2e2", color: "#dc2626", label: "Cancelada" }
      : { bg: "#fef9c3", color: "#ca8a04", label: "Agendada" };
    return <span style={{ ...badge, background: cfg.bg, color: cfg.color }}>{cfg.label}</span>;
  }

  return (
    <div>
      <div style={h.header}>
        <h1 style={h.title}>Consultas</h1>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <input type="date" value={filterDate} onChange={(e) => setFilterDate(e.target.value)} style={h.dateInput} />
          <button onClick={openCreate} style={h.addBtn}>+ Nova Consulta</button>
        </div>
      </div>

      {showForm && (
        <div style={h.modalOverlay}>
          <div style={h.modal}>
            <h2 style={h.modalTitle}>Nova Consulta</h2>
            <form onSubmit={handleSubmit} style={h.form}>
              <select style={h.input} value={form.pet_id} onChange={(e) => setForm({ ...form, pet_id: Number(e.target.value) })} required>
                <option value={0}>Selecionar animal</option>
                {pets.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <input style={h.input} type="datetime-local" value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} required />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem" }}>
                <input style={h.input} type="number" min="15" max="180" value={form.duration_min} onChange={(e) => setForm({ ...form, duration_min: Number(e.target.value) })} />
                <input style={h.input} placeholder="Notas" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
              <div style={h.formBtns}>
                <button type="button" onClick={() => setShowForm(false)} style={h.cancelBtn}>Cancelar</button>
                <button type="submit" style={h.saveBtn}>Agendar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={h.card}>
        {loading ? <p style={h.empty}>A carregar...</p> : appointments.length === 0 ? (
          <p style={h.empty}>Nenhuma consulta para este dia.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                <th style={h.th}>Hora</th>
                <th style={h.th}>Animal</th>
                <th style={h.th}>Duração</th>
                <th style={h.th}>Estado</th>
                <th style={h.th}>Notas</th>
                <th style={{ ...h.th, width: 180 }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                  <td style={h.td}>{new Date(a.scheduled_at).toLocaleTimeString("pt-AO", { hour: "2-digit", minute: "2-digit" })}</td>
                  <td style={h.td}>{getPetName(a.pet_id)}</td>
                  <td style={{ ...h.td, color: "#666" }}>{a.duration_min} min</td>
                  <td style={h.td}>{statusBadge(a.status)}</td>
                  <td style={{ ...h.td, color: "#666" }}>{a.notes || "—"}</td>
                  <td style={h.td}>
                    {a.status === "scheduled" && (
                      <>
                        <button onClick={() => handleStatus(a.id, "completed")} style={h.doneBtn}>✓ Concluir</button>
                        <button onClick={() => handleDelete(a.id)} style={h.deleteBtn}>X</button>
                      </>
                    )}
                    {a.status !== "scheduled" && (
                      <span style={{ color: "#aaa", fontSize: "0.85rem" }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const h: Record<string, React.CSSProperties> = {
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" },
  title: { fontSize: "1.75rem", fontWeight: 700, color: "#1a1a2e" },
  addBtn: { padding: "0.6rem 1.2rem", background: "#4caf50", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: "0.95rem" },
  dateInput: { padding: "0.55rem 0.8rem", border: "1.5px solid #e0e0e0", borderRadius: 8, fontSize: "0.9rem" },
  modalOverlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 },
  modal: { background: "#fff", borderRadius: 16, padding: "2rem", width: 460, maxWidth: "95vw" },
  modalTitle: { marginTop: 0, marginBottom: "1.5rem", color: "#1a1a2e" },
  form: { display: "flex", flexDirection: "column", gap: "0.8rem" },
  input: { padding: "0.65rem 0.9rem", border: "1.5px solid #e0e0e0", borderRadius: 8, fontSize: "0.95rem", width: "100%", boxSizing: "border-box" },
  formBtns: { display: "flex", gap: "0.5rem", justifyContent: "flex-end", marginTop: "0.5rem" },
  cancelBtn: { padding: "0.6rem 1.2rem", background: "#f0f0f0", color: "#333", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600 },
  saveBtn: { padding: "0.6rem 1.2rem", background: "#4caf50", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600 },
  card: { background: "#fff", borderRadius: 14, padding: "1.5rem", boxShadow: "0 2px 8px rgba(0,0,0,0.06)" },
  empty: { color: "#aaa", textAlign: "center", padding: "3rem", fontSize: "0.95rem" },
  th: { textAlign: "left", padding: "0.6rem 0.5rem", color: "#888", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.05em" },
  td: { padding: "0.75rem 0.5rem", fontSize: "0.95rem" },
  doneBtn: { padding: "0.3rem 0.7rem", background: "#dcfce7", color: "#16a34a", border: "none", borderRadius: 6, cursor: "pointer", fontSize: "0.85rem", marginRight: 6 },
  deleteBtn: { padding: "0.3rem 0.7rem", background: "#fee2e2", color: "#dc2626", border: "none", borderRadius: 6, cursor: "pointer", fontSize: "0.85rem" },
};

const badge: React.CSSProperties = { padding: "0.25rem 0.75rem", borderRadius: 20, fontSize: "0.8rem", fontWeight: 600 };
