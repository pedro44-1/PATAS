import { useEffect, useState } from "react";
import { treatmentsApi, Treatment, TreatmentCreate } from "@/api/treatments";
import { appointmentsApi, Appointment } from "@/api/appointments";
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
import { Plus, Pencil, Trash2, Search, Pill, X } from "lucide-react";

export default function Treatments() {
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Treatment | null>(null);
  const [form, setForm] = useState<TreatmentCreate>({
    appointment_id: 0,
    diagnosis: "",
    notes: "",
    prescription: "",
  });
  const [saving, setSaving] = useState(false);

  function load() {
    Promise.all([treatmentsApi.list(), appointmentsApi.list()])
      .then(([tRes, aRes]) => {
        setTreatments(tRes.data);
        setAppointments(aRes.data);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function getApptInfo(id: number) {
    const a = appointments.find((x) => x.id === id);
    if (!a) return "—";
    return `${a.notes || a.reason || "Consulta"} · ${new Date(a.scheduled_at).toLocaleDateString("pt-AO")}`;
  }

  function openCreate() {
    setEditing(null);
    setForm({
      appointment_id: appointments[0]?.id ?? 0,
      diagnosis: "",
      notes: "",
      prescription: "",
    });
    setShowForm(true);
  }

  function openEdit(t: Treatment) {
    setEditing(t);
    setForm({
      appointment_id: t.appointment_id,
      diagnosis: t.diagnosis ?? "",
      notes: t.notes ?? "",
      prescription: t.prescription ?? "",
    });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await treatmentsApi.update(editing.id, form);
      } else {
        await treatmentsApi.create(form);
      }
      setShowForm(false);
      load();
    } catch {} finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Eliminar este tratamento?")) return;
    await treatmentsApi.delete(id);
    load();
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">Tratamentos</h2>
          <p className="text-dark-400 text-sm mt-0.5">
            {treatments.length} tratamento{treatments.length !== 1 ? "s" : ""} registado
            {treatments.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Tratamento
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : treatments.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <Pill className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">Nenhum tratamento registado</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5 w-28">Data</TableHead>
                  <TableHead>Consulta</TableHead>
                  <TableHead>Diagnóstico</TableHead>
                  <TableHead>Prescrição</TableHead>
                  <TableHead className="pr-5 w-28 text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {treatments.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell className="pl-5">
                      <span className="text-sm font-medium text-dark-700">
                        {new Date(t.created_at).toLocaleDateString("pt-AO")}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-dark-600 max-w-40 block truncate">
                        {getApptInfo(t.appointment_id)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-dark-600 max-w-56 block truncate">
                        {t.diagnosis ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-dark-500 max-w-48 block truncate">
                        {t.prescription ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell className="pr-5">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => openEdit(t)}
                          className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(t.id)}
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
                  {editing ? "Editar Tratamento" : "Novo Tratamento"}
                </h2>
                <p className="text-dark-400 text-xs mt-0.5">
                  {editing ? "A editar tratamento" : "Registar um novo tratamento"}
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
                <Label className="text-xs font-semibold text-dark-600">Consulta *</Label>
                <select
                  value={form.appointment_id}
                  onChange={(e) => setForm({ ...form, appointment_id: Number(e.target.value) })}
                  className="flex h-11 w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  required
                >
                  <option value={0}>Selecionar consulta</option>
                  {appointments.map((a) => (
                    <option key={a.id} value={a.id}>{getApptInfo(a.id)}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Diagnóstico</Label>
                <textarea
                  value={form.diagnosis}
                  onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
                  placeholder="Resultado do diagnóstico"
                  rows={3}
                  className="flex w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Prescrição / Medicação</Label>
                <textarea
                  value={form.prescription}
                  onChange={(e) => setForm({ ...form, prescription: e.target.value })}
                  placeholder="Medicação prescrita"
                  rows={3}
                  className="flex w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

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
                  ) : editing ? "Guardar Alterações" : "Criar Tratamento"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
