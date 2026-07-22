import { useEffect, useState } from "react";
import { ownersApi, Owner, OwnerCreate } from "@/api/owners";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { Plus, Pencil, Trash2, Phone, Mail, MapPin, Search, X } from "lucide-react";

export default function Owners() {
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Owner | null>(null);
  const [form, setForm] = useState<OwnerCreate>({
    name: "",
    phone: "",
    email: "",
    address: "",
    notes: "",
  });
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    ownersApi.list().then((r) => setOwners(r.data)).finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  const filtered = owners.filter((o) =>
    search === "" ||
    o.name.toLowerCase().includes(search.toLowerCase()) ||
    (o.email ?? "").toLowerCase().includes(search.toLowerCase()) ||
    (o.phone ?? "").includes(search)
  );

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
    setSaving(true);
    try {
      if (editing) {
        await ownersApi.update(editing.id, form);
      } else {
        await ownersApi.create(form);
      }
      setShowForm(false);
      load();
    } catch {} finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Eliminar este dono?")) return;
    await ownersApi.delete(id);
    load();
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">Donos</h2>
          <p className="text-dark-400 text-sm mt-0.5">
            {owners.length} dono{owners.length !== 1 ? "s" : ""} registado
            {owners.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Dono
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
        <Input
          placeholder="Pesquisar por nome, email ou telefone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10 h-11 rounded-xl bg-white border-dark-200"
        />
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <p className="text-sm font-medium">Nenhum dono encontrado</p>
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="mt-2 text-xs text-brand-600 hover:text-brand-700 font-semibold"
                >
                  Limpar pesquisa
                </button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5">Nome</TableHead>
                  <TableHead>Telefone</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Endereço</TableHead>
                  <TableHead className="pr-5 w-36 text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((o) => (
                  <TableRow key={o.id}>
                    <TableCell className="pl-5 font-semibold text-dark-900 text-sm">
                      {o.name}
                    </TableCell>
                    <TableCell>
                      {o.phone ? (
                        <span className="flex items-center gap-1.5 text-sm text-dark-600">
                          <Phone className="w-3.5 h-3.5 text-dark-400" />
                          {o.phone}
                        </span>
                      ) : (
                        <span className="text-dark-300 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {o.email ? (
                        <span className="flex items-center gap-1.5 text-sm text-dark-600">
                          <Mail className="w-3.5 h-3.5 text-dark-400" />
                          {o.email}
                        </span>
                      ) : (
                        <span className="text-dark-300 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {o.address ? (
                        <span className="flex items-center gap-1.5 text-sm text-dark-600">
                          <MapPin className="w-3.5 h-3.5 text-dark-400 flex-shrink-0" />
                          <span className="truncate max-w-40">{o.address}</span>
                        </span>
                      ) : (
                        <span className="text-dark-300 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell className="pr-5">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => openEdit(o)}
                          className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(o.id)}
                          className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Modal with solid background */}
      {showForm && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setShowForm(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="sticky top-0 bg-white border-b border-dark-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <div>
                <h2 className="font-bold text-dark-900">
                  {editing ? "Editar Dono" : "Novo Dono"}
                </h2>
                <p className="text-dark-400 text-xs mt-0.5">
                  {editing ? `A editar ${editing.name}` : "Registar um novo dono"}
                </p>
              </div>
              <button
                onClick={() => setShowForm(false)}
                className="w-8 h-8 rounded-xl bg-dark-100 flex items-center justify-center text-dark-400 hover:text-dark-700 hover:bg-dark-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Nome *</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Nome completo"
                  required
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Telefone</Label>
                <Input
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder="+244 923 456 789"
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Email</Label>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="email@exemplo.com"
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Endereço</Label>
                <Input
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  placeholder="Rua, número, bairro"
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Notas</Label>
                <Input
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Notas adicionais"
                  className="h-11 rounded-xl"
                />
              </div>

              {/* Modal footer */}
              <div className="flex items-center justify-end gap-3 pt-2 border-t border-dark-100">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForm(false)}
                  className="rounded-xl h-11"
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-brand-600 hover:bg-brand-700 rounded-xl h-11 font-semibold"
                >
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      A guardar...
                    </span>
                  ) : editing ? (
                    "Guardar Alterações"
                  ) : (
                    "Criar Dono"
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
