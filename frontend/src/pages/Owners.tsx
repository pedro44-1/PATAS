import { useEffect, useState } from "react";
import { ownersApi, Owner, OwnerCreate } from "../api/owners";

export default function Owners() {
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Owner | null>(null);
  const [form, setForm] = useState<OwnerCreate>({ name: "", phone: "", email: "", address: "", notes: "" });

  function load() {
    setLoading(true);
    ownersApi.list()
      .then((r) => setOwners(r.data))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function openCreate() {
    setEditing(null);
    setForm({ name: "", phone: "", email: "", address: "", notes: "" });
    setShowForm(true);
  }

  function openEdit(owner: Owner) {
    setEditing(owner);
    setForm({
      name: owner.name,
      phone: owner.phone ?? "",
      email: owner.email ?? "",
      address: owner.address ?? "",
      notes: owner.notes ?? "",
    });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editing) {
        await ownersApi.update(editing.id, form);
      } else {
        await ownersApi.create(form);
      }
      setShowForm(false);
      load();
    } catch {}
  }

  async function handleDelete(id: number) {
    if (!confirm("Eliminar este dono?")) return;
    await ownersApi.delete(id);
    load();
  }

  return (
    <div>
      <div style={h.header}>
        <h1 style={h.title}>Donos</h1>
        <button onClick={openCreate} style={h.addBtn}>+ Novo Dono</button>
      </div>

      {showForm && (
        <div style={h.modalOverlay}>
          <div style={h.modal}>
            <h2 style={h.modalTitle}>{editing ? "Editar Dono" : "Novo Dono"}</h2>
            <form onSubmit={handleSubmit} style={h.form}>
              <input style={h.input} placeholder="Nome *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <input style={h.input} placeholder="Telefone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              <input style={h.input} type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <input style={h.input} placeholder="Endereço" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
              <textarea style={{ ...h.input, height: 80, resize: "vertical" }} placeholder="Notas" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              <div style={h.formBtns}>
                <button type="button" onClick={() => setShowForm(false)} style={h.cancelBtn}>Cancelar</button>
                <button type="submit" style={h.saveBtn}>{editing ? "Guardar" : "Criar"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={h.card}>
        {loading ? (
          <p style={h.empty}>A carregar...</p>
        ) : owners.length === 0 ? (
          <p style={h.empty}>Nenhum dono registado. Clique em "+ Novo Dono" para começar.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                <th style={h.th}>Nome</th>
                <th style={h.th}>Telefone</th>
                <th style={h.th}>Email</th>
                <th style={h.th}>Endereço</th>
                <th style={{ ...h.th, width: 120 }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {owners.map((o) => (
                <tr key={o.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                  <td style={h.td}>{o.name}</td>
                  <td style={{ ...h.td, color: "#666" }}>{o.phone ?? "—"}</td>
                  <td style={{ ...h.td, color: "#666" }}>{o.email ?? "—"}</td>
                  <td style={{ ...h.td, color: "#666" }}>{o.address ?? "—"}</td>
                  <td style={h.td}>
                    <button onClick={() => openEdit(o)} style={h.editBtn}>Editar</button>
                    <button onClick={() => handleDelete(o.id)} style={h.deleteBtn}>Eliminar</button>
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
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" },
  title: { fontSize: "1.75rem", fontWeight: 700, color: "#1a1a2e" },
  addBtn: { padding: "0.6rem 1.2rem", background: "#4caf50", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: "0.95rem" },
  modalOverlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 },
  modal: { background: "#fff", borderRadius: 16, padding: "2rem", width: 440, maxWidth: "95vw" },
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
  editBtn: { padding: "0.3rem 0.7rem", background: "#e3f2fd", color: "#1565c0", border: "none", borderRadius: 6, cursor: "pointer", fontSize: "0.85rem", marginRight: 6 },
  deleteBtn: { padding: "0.3rem 0.7rem", background: "#fee2e2", color: "#dc2626", border: "none", borderRadius: 6, cursor: "pointer", fontSize: "0.85rem" },
};
