import { useEffect, useState } from "react";
import { appointmentsApi, Appointment, AppointmentCreate } from "@/api/appointments";
import { petsApi, Pet } from "@/api/pets";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
import { Plus, Search, CalendarDays, Check, X } from "lucide-react";

function statusConfig(status: string) {
  if (status === "completed")
    return { label: "Concluída", bg: "bg-brand-50", text: "text-brand-700", dot: "bg-brand-500" };
  if (status === "cancelled")
    return { label: "Cancelada", bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
  if (status === "no-show")
    return { label: "Faltou", bg: "bg-dark-100", text: "text-dark-600", dot: "bg-dark-400" };
  return { label: "Agendada", bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
}

export default function Appointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filterDate, setFilterDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [form, setForm] = useState<AppointmentCreate>({
    pet_id: 0,
    vet_id: 1,
    scheduled_at: "",
    duration_min: 30,
    reason: "",
    notes: "",
    weight: undefined,
  });
  const [saving, setSaving] = useState(false);

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
    setForm({
      pet_id: pets[0]?.id ?? 0,
      vet_id: 1,
      scheduled_at: defaultTime,
      duration_min: 30,
      reason: "",
      notes: "",
      weight: undefined,
    });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await appointmentsApi.create(form);
      setShowForm(false);
      load();
    } catch {} finally {
      setSaving(false);
    }
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

  const todayLabel = new Date(filterDate + "T00:00:00").toLocaleDateString(
    "pt-AO",
    { weekday: "long", day: "numeric", month: "long" }
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">Consultas</h2>
          <p className="text-dark-400 text-sm mt-0.5 capitalize">{todayLabel}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400 pointer-events-none" />
            <input
              type="date"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="pl-9 h-10 rounded-xl border border-dark-200 bg-white px-3 text-sm text-dark-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <Button
            onClick={openCreate}
            className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
          >
            <Plus className="w-4 h-4 mr-2" />
            Nova Consulta
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : appointments.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <CalendarDays className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">Nenhuma consulta para este dia</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5 w-20">Hora</TableHead>
                  <TableHead>Animal</TableHead>
                  <TableHead>Motivo</TableHead>
                  <TableHead>Duração</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="pr-5 w-48 text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {appointments.map((a) => {
                  const cfg = statusConfig(a.status);
                  return (
                    <TableRow key={a.id}>
                      <TableCell className="pl-5">
                        <div className="font-bold text-sm text-dark-900">
                          {new Date(a.scheduled_at).toLocaleTimeString("pt-AO", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                        <div className="text-dark-400 text-xs">{a.duration_min} min</div>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium text-sm text-dark-900">
                          {getPetName(a.pet_id)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-dark-600">
                          {a.notes || a.reason || "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-dark-500">
                          {a.duration_min} min
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold",
                            cfg.bg,
                            cfg.text
                          )}
                        >
                          <span className={cn("w-1.5 h-1.5 rounded-full", cfg.dot)} />
                          {cfg.label}
                        </span>
                      </TableCell>
                      <TableCell className="pr-5">
                        {a.status === "scheduled" ? (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleStatus(a.id, "completed")}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors"
                              title="Marcar como concluída"
                            >
                              <Check className="w-3.5 h-3.5" />
                              Concluir
                            </button>
                            <button
                              onClick={() => handleStatus(a.id, "cancelled")}
                              className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                              title="Cancelar"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <span className="text-dark-300 text-xs">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Form Dialog */}
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
                <h2 className="font-bold text-dark-900">Nova Consulta</h2>
                <p className="text-dark-400 text-xs mt-0.5">Registar uma nova consulta</p>
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
                <Label className="text-xs font-semibold text-dark-600">Animal *</Label>
                <select
                  value={form.pet_id}
                  onChange={(e) => setForm({ ...form, pet_id: Number(e.target.value) })}
                  className="flex h-11 w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  required
                >
                  <option value={0}>Selecionar animal</option>
                  {pets.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Data e Hora *</Label>
                <Input
                  type="datetime-local"
                  value={form.scheduled_at}
                  onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                  required
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Motivo da Consulta</Label>
                <Input
                  value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  placeholder="Ex: Vacinação, Consulta geral, Exame de sangue"
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

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">Duração</Label>
                  <select
                    value={form.duration_min}
                    onChange={(e) => setForm({ ...form, duration_min: Number(e.target.value) })}
                    className="flex h-11 w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value={15}>15 minutos</option>
                    <option value={30}>30 minutos</option>
                    <option value={45}>45 minutos</option>
                    <option value={60}>60 minutos</option>
                    <option value={90}>90 minutos</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">Peso registado (kg)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    value={form.weight ?? ""}
                    onChange={(e) =>
                      setForm({ ...form, weight: e.target.value ? Number(e.target.value) : undefined })
                    }
                    placeholder="Ex: 12.5"
                    className="h-11 rounded-xl"
                  />
                </div>
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
                      A agendar...
                    </span>
                  ) : "Agendar Consulta"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
