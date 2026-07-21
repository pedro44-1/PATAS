import { useEffect, useState } from "react";
import { petsApi, Pet, PetCreate } from "../api/pets";
import { ownersApi, Owner } from "../api/owners";

export default function Pets() {
  const [pets, setPets] = useState<Pet[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Pet | null>(null);
  const [form, setForm] = useState<PetCreate>({ owner_id: 0, name: "", species: "", breed: "", age: "", weight: undefined });

  function load() {
    Promise.all([petsApi.list(), ownersApi.list()])
      .then(([petsRes, ownersRes]) => {
        setPets(petsRes.data);
        setOwners(ownersRes.data);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function openCreate() {
    setEditing(null);
    setForm({ owner_id: owners[0]?.id ?? 0, name: "", species: "", breed: "", age: "", weight: undefined });
    setShowForm(true);
  }

  function openEdit(pet: Pet) {
    setEditing(pet);
    setForm({
      owner_id: pet.owner_id,
      name: pet.name,
      species: pet.species,
      breed: pet.breed ?? "",
      age: pet.age ?? "",
      weight: pet.weight ?? undefined,
    });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload = { ...form };
    if (!payload.weight) payload.weight = undefined;
    try {
      if (editing) {
        await petsApi.update(editing.id, payload);
      } else {
        await petsApi.create(payload as PetCreate);
      }
      setShowForm(false);
      load();
    } catch {}
  }

  async function handleDelete(id: number) {
    if (!confirm("Eliminar este animal?")) return;
    await petsApi.delete(id);
    load();
  }

  function getOwnerName(id: number) {
    return owners.find((o) => o.id === id)?.name ?? "—";
  }

  return (
    <div>
      <div style={h.header}>
        <h1 style={h.title}>Animais</h1>
        <button onClick={openCreate} style={h.addBtn}>+ Novo Animal</button>
      </div>

      {showForm && (
        <div style={h.modalOverlay}>
          <div style={h.modal}>
            <h2 style={h.modalTitle}>{editing ? "Editar Animal" : "Novo Animal"}</h2>
            <form onSubmit={handleSubmit} style={h.form}>
              <select style={h.input} value={form.owner_id} onChange={(e) => setForm({ ...form, owner_id: Number(e.target.value) })} required>
                <option value={0}>Selecionar dono</option>
                {owners.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
              <input style={h.input} placeholder="Nome do animal *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              <input style={h.input} placeholder="Espécie (Cão, Gato, Pássaro...) *" value={form.species} onChange={(e) => setForm({ ...form, species: e.target.value })} required />
              <input style={h.input} placeholder="Raça" value={form.breed} onChange={(e) => setForm({ ...form, breed: e.target.value })} />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem" }}>
                <input style={h.input} placeholder="Idade (ex: 3 anos)" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} />
                <input style={h.input} type="number" step="0.1" placeholder="Peso (kg)" value={form.weight ?? ""} onChange={(e) => setForm({ ...form, weight: e.target.value ? Number(e.target.value) : undefined })} />
              </div>
              <div style={h.formBtns}>
                <button type="button" onClick={() => setShowForm(false)} style={h.cancelBtn}>Cancelar</button>
                <button type="submit" style={h.saveBtn}>{editing ? "Guardar" : "Criar"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div style={h.card}>
        {loading ? <p style={h.empty}>A carregar...</p> : pets.length === 0 ? (
          <p style={h.empty}>Nenhum animal registado.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #f0f0f0" }}>
                <th style={h.th}>Nome</th>
                <th style={h.th}>Espécie</th>
                <th style={h.th}>Raça</th>
                <th style={h.th}>Dono</th>
                <th style={h.th}>Idade</th>
                <th style={{ ...h.th, width: 100 }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {pets.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                  <td style={h.td}>{p.name}</td>
                  <td style={h.td}>{p.species}</td>
                  <td style={{ ...h.td, color: "#666" }}>{p.breed ?? "—"}</td>
                  <td style={{ ...h.td, color: "#666" }}>{getOwnerName(p.owner_id)}</td>
                  <td style={{ ...h.td, color: "#666" }}>{p.age ?? "—"}</td>
                  <td style={h.td}>
                    <button onClick={() => openEdit(p)} style={h.editBtn}>Editar</button>
                    <button onClick={() => handleDelete(p.id)} style={h.deleteBtn}>X</button>
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
  modal: { background: "#fff", borderRadius: 16, padding: "2rem", width: 480, maxWidth: "95vw" },
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
