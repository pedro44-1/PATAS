import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { appointmentsApi, Appointment, AppointmentCreate, VetOption } from "@/api/appointments";
import { petsApi, Pet, PetCreate } from "@/api/pets";
import { ownersApi, Owner } from "@/api/owners";
import { serviceTypesApi } from "@/api/serviceTypes";
import type { ServiceType } from "@patas/shared-types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
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
import { clinicDateInput, parseApiDate } from "@/lib/date";
import { Plus, Search, CalendarDays, Check, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiErrorMessage } from "@/api/errors";

const CREATE_PET_VALUE = "__create_pet__";
const PET_SPECIES = ["Cão", "Gato", "Ave", "Roedor", "Coelho", "Réptil", "Outro"] as const;

function statusConfig(status: string) {
  if (status === "in-progress")
    return { key: "in-progress", bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" };
  if (status === "completed")
    return { key: "completed", bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" };
  if (status === "cancelled")
    return { key: "cancelled", bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
  if (status === "no-show")
    return { key: "no-show", bg: "bg-dark-100", text: "text-dark-600", dot: "bg-dark-400" };
  return { key: "scheduled", bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
}

export default function Appointments() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWriteClinical = user?.role === "admin" || user?.role === "vet";
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [vets, setVets] = useState<VetOption[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filterDate, setFilterDate] = useState(
    clinicDateInput()
  );
  const [form, setForm] = useState<AppointmentCreate>({
    pet_id: 0,
    vet_id: 0,
    scheduled_at: "",
    duration_min: 30,
    reason: "",
    notes: "",
    weight: undefined,
    service_type_id: undefined,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showQuickPet, setShowQuickPet] = useState(false);
  const [savingPet, setSavingPet] = useState(false);
  const [petError, setPetError] = useState("");
  const [petForm, setPetForm] = useState<PetCreate>({ owner_id: 0, name: "", species: "Cão" });

  function load() {
    Promise.all([appointmentsApi.list(filterDate), petsApi.list(), ownersApi.list(), appointmentsApi.vets(), serviceTypesApi.list()])
      .then(([apptsRes, petsRes, ownersRes, vetsRes, serviceTypesRes]) => {
        setAppointments(apptsRes.data);
        setPets(petsRes.data);
        setOwners(ownersRes.data);
        setVets(vetsRes.data);
        setServiceTypes(serviceTypesRes.data);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [filterDate]);

  function openCreate() {
    const defaultTime = `${filterDate}T09:00`;
    setForm({
      pet_id: pets[0]?.id ?? 0,
      vet_id: vets[0]?.id ?? 0,
      scheduled_at: defaultTime,
      duration_min: 30,
      reason: "",
      notes: "",
      weight: undefined,
      service_type_id: serviceTypes[0]?.id,
    });
    setShowForm(true);
  }

  function openQuickPet() {
    setPetError("");
    setPetForm({ owner_id: owners[0]?.id ?? 0, name: "", species: "Cão" });
    setShowQuickPet(true);
  }

  function handlePetSelection(value: string) {
    if (value === CREATE_PET_VALUE) {
      openQuickPet();
      return;
    }
    setForm({ ...form, pet_id: Number(value) });
  }

  async function handleQuickPetSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSavingPet(true);
    setPetError("");
    try {
      const response = await petsApi.create(petForm);
      const createdPet = response.data;
      setPets((current) => [...current, createdPet]);
      setForm((current) => ({ ...current, pet_id: createdPet.id }));
      setShowQuickPet(false);
    } catch (requestError: unknown) {
      setPetError(apiErrorMessage(requestError, t, "pets.error"));
    } finally {
      setSavingPet(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await appointmentsApi.create(form);
      setShowForm(false);
      load();
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "appointments.error"));
    } finally {
      setSaving(false);
    }
  }

  async function handleStatus(id: number, status: string) {
    const requiresReason = status === "cancelled" || status === "no-show";
    const status_reason = requiresReason
      ? window.prompt(t(status === "cancelled" ? "appointments.cancelReason" : "appointments.noShowReason")) ?? ""
      : undefined;
    if (requiresReason && !status_reason?.trim()) return;
    setError("");
    try {
      await appointmentsApi.update(id, { status: status as any, status_reason });
      load();
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "appointments.error"));
    }
  }

  function getPetName(id: number) {
    return pets.find((p) => p.id === id)?.name ?? "—";
  }

  const todayLabel = new Date(filterDate + "T12:00:00Z").toLocaleDateString(
    "pt-AO",
    { weekday: "long", day: "numeric", month: "long", timeZone: "Africa/Luanda" }
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">{t("appointments.title")}</h2>
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
            {t("appointments.new")}
          </Button>
        </div>
      </div>
      {error && <div role="alert" className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : appointments.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <CalendarDays className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">{t("appointments.noResults")}</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5 w-20">{t("appointments.table.time")}</TableHead>
                  <TableHead>{t("appointments.table.animal")}</TableHead>
                  <TableHead>{t("appointments.table.reason")}</TableHead>
                  <TableHead>{t("appointments.table.duration")}</TableHead>
                  <TableHead>{t("appointments.table.status")}</TableHead>
                  <TableHead className="pr-5 w-48 text-right">{t("appointments.table.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {appointments.map((a) => {
                  const cfg = statusConfig(a.status);
                  return (
                    <TableRow key={a.id}>
                      <TableCell className="pl-5">
                        <div className="font-bold text-sm text-dark-900">
                          {parseApiDate(a.scheduled_at).toLocaleTimeString("pt-AO", {
                            hour: "2-digit",
                            minute: "2-digit",
                            timeZone: "Africa/Luanda",
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
                          {t(`appointments.status.${cfg.key}`)}
                        </span>
                      </TableCell>
                      <TableCell className="pr-5">
                        {a.status === "scheduled" ? (
                          <div className="flex justify-end gap-2">
                            {canWriteClinical && <button
                              onClick={() => handleStatus(a.id, "in-progress")}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors"
                              title={t("appointments.actions.start")}
                            >
                              <Check className="w-3.5 h-3.5" />
                              {t("appointments.actions.start")}
                            </button>}
                            <button
                              onClick={() => handleStatus(a.id, "cancelled")}
                              className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                              title={t("appointments.actions.cancel")}
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={() => handleStatus(a.id, "no-show")} className="px-2.5 py-1 rounded-lg bg-dark-100 text-dark-600 hover:bg-dark-200 text-xs font-semibold transition-colors">{t("appointments.actions.noShow")}</button>
                          </div>
                        ) : a.status === "in-progress" && canWriteClinical ? (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleStatus(a.id, "completed")}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors"
                            >
                              <Check className="w-3.5 h-3.5" />
                              {t("appointments.actions.complete")}
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
      {showForm && createPortal(
        <div
          className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-black/60 p-4 backdrop-blur-sm"
          onClick={() => setShowForm(false)}
        >
          <div
            className="relative flex max-h-[calc(100dvh-2rem)] w-full max-w-md flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex shrink-0 items-center justify-between rounded-t-2xl border-b border-dark-100 bg-white px-6 py-4">
              <div>
                <h2 className="font-bold text-dark-900">{t("appointments.new")}</h2>
                <p className="text-dark-400 text-xs mt-0.5">{t("appointments.create")}</p>
              </div>
              <button
                onClick={() => setShowForm(false)}
                className="w-8 h-8 rounded-xl bg-dark-100 flex items-center justify-center text-dark-400 hover:text-dark-700 hover:bg-dark-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal body */}
            <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
              <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.animal")} *</Label>
                <FormSelect
                  value={form.pet_id || null}
                  onValueChange={handlePetSelection}
                  options={[
                    ...pets.map((pet) => ({ value: pet.id, label: pet.name })),
                    {
                      value: CREATE_PET_VALUE,
                      label: (
                        <span className="flex items-center gap-2">
                          <Plus className="size-4" />
                          {t("appointments.form.createAnimal")}
                        </span>
                      ),
                      variant: "action" as const,
                    },
                  ]}
                  placeholder={t("appointments.form.selectAnimal")}
                  className="h-11 border-dark-200 bg-white"
                  ariaLabel={t("appointments.form.animal")}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.vet")} *</Label>
                <FormSelect
                  value={form.vet_id || null}
                  onValueChange={(value) => setForm({ ...form, vet_id: Number(value) })}
                  options={vets.map((vet) => ({ value: vet.id, label: vet.name }))}
                  placeholder={t("appointments.form.selectVet")}
                  className="h-11 border-dark-200 bg-white"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.dateTime")} *</Label>
                <Input
                  type="datetime-local"
                  value={form.scheduled_at}
                  onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                  required
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.reason")}</Label>
                <Input
                  value={form.reason}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  placeholder={t("appointments.form.reasonPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.service")}</Label>
                <FormSelect
                  value={form.service_type_id ?? ""}
                  onValueChange={(value) => setForm({ ...form, service_type_id: value ? Number(value) : undefined })}
                  options={[
                    { value: "", label: t("appointments.form.selectService") },
                    ...serviceTypes.filter((service) => service.active).map((service) => ({ value: service.id, label: service.name })),
                  ]}
                  placeholder={t("appointments.form.selectService")}
                  className="h-11 border-dark-200 bg-white"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.notes")}</Label>
                <Input
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder={t("appointments.form.notesPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.duration")}</Label>
                  <FormSelect
                    value={form.duration_min}
                    onValueChange={(value) => setForm({ ...form, duration_min: Number(value) })}
                    options={[15, 30, 45, 60, 90].map((minutes) => ({ value: minutes, label: `${minutes} minutos` }))}
                    className="h-11 border-dark-200 bg-white"
                  />
                </div>
                {canWriteClinical && <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.weight")}</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    value={form.weight ?? ""}
                    onChange={(e) =>
                      setForm({ ...form, weight: e.target.value ? Number(e.target.value) : undefined })
                    }
                    placeholder={t("appointments.form.weightPlaceholder")}
                    className="h-11 rounded-xl"
                  />
                </div>}
              </div>
              </div>

              {/* Modal footer */}
              <div className="flex shrink-0 items-center justify-end gap-3 border-t border-dark-100 bg-white px-6 py-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForm(false)}
                  className="rounded-xl h-11"
                >
                  {t("common.cancel")}
                </Button>
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-brand-600 hover:bg-brand-700 rounded-xl h-11 font-semibold"
                >
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      {t("appointments.saving")}
                    </span>
                  ) : t("appointments.create")}
                </Button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}
      {showQuickPet && createPortal(
        <div
          className="fixed inset-0 z-[60] grid place-items-center overflow-y-auto bg-black/45 p-4 backdrop-blur-sm"
          onClick={() => setShowQuickPet(false)}
        >
          <div
            className="w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-dark-100 px-6 py-4">
              <div>
                <h2 className="font-bold text-dark-900">{t("appointments.quickPet.title")}</h2>
                <p className="mt-0.5 text-xs text-dark-400">{t("appointments.quickPet.hint")}</p>
              </div>
              <button
                type="button"
                onClick={() => setShowQuickPet(false)}
                aria-label={t("common.close")}
                className="flex size-8 items-center justify-center rounded-xl bg-dark-100 text-dark-400 transition-colors hover:bg-dark-200 hover:text-dark-700"
              >
                <X className="size-4" />
              </button>
            </div>
            <form onSubmit={handleQuickPetSubmit}>
              <div className="space-y-4 px-6 py-5">
                {petError && (
                  <div role="alert" className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {petError}
                  </div>
                )}
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("pets.form.owner")} *</Label>
                  <FormSelect
                    value={petForm.owner_id || null}
                    onValueChange={(value) => setPetForm({ ...petForm, owner_id: Number(value) })}
                    options={owners.map((owner) => ({ value: owner.id, label: owner.name }))}
                    placeholder={t("pets.form.selectOwner")}
                    className="h-11 border-dark-200 bg-white"
                    required
                  />
                  {owners.length === 0 && (
                    <p className="text-xs text-amber-700">{t("appointments.quickPet.noOwners")}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="quick-pet-name" className="text-xs font-semibold text-dark-600">{t("pets.form.name")} *</Label>
                  <Input
                    id="quick-pet-name"
                    value={petForm.name}
                    onChange={(event) => setPetForm({ ...petForm, name: event.target.value })}
                    placeholder={t("pets.form.namePlaceholder")}
                    className="h-11 rounded-xl"
                    autoFocus
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("pets.form.species")} *</Label>
                  <FormSelect
                    value={petForm.species}
                    onValueChange={(value) => setPetForm({ ...petForm, species: value })}
                    options={PET_SPECIES.map((species) => ({ value: species, label: t(`pets.species.${species}`) }))}
                    className="h-11 border-dark-200 bg-white"
                    required
                  />
                </div>
              </div>
              <div className="flex items-center justify-end gap-3 border-t border-dark-100 px-6 py-4">
                <Button type="button" variant="outline" onClick={() => setShowQuickPet(false)} className="h-11 rounded-xl">
                  {t("common.cancel")}
                </Button>
                <Button
                  type="submit"
                  disabled={savingPet || owners.length === 0}
                  className="h-11 rounded-xl bg-brand-600 font-semibold hover:bg-brand-700"
                >
                  {savingPet ? t("common.saving") : t("appointments.quickPet.create")}
                </Button>
              </div>
            </form>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
