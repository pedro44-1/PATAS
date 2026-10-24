import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { appointmentsApi, Appointment, AppointmentCreate, AppointmentStatus, VetOption } from "@/api/appointments";
import { petsApi, Pet, PetCreate } from "@/api/pets";
import { ownersApi, Owner, OwnerCreate } from "@/api/owners";
import { serviceTypesApi } from "@/api/serviceTypes";
import type { ServiceType } from "@patas/shared-types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
import { FormError } from "@/components/ui/form-error";
import { FormDialog } from "@/components/ui/form-dialog";
import { PromptDialog } from "@/components/ui/prompt-dialog";
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
import { clinicDateInput, clinicDateTimeInput, parseApiDate } from "@/lib/date";
import { useRemoteOptions } from "@/lib/use-remote-options";
import { Archive, CalendarClock, CalendarDays, Check, ClipboardList, Plus, X } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { apiErrorMessage } from "@/api/errors";
import { OPTIONS_LIMIT } from "@/api/pagination";

const CREATE_PET_VALUE = "__create_pet__";
const CREATE_OWNER_VALUE = "__create_owner__";
const PET_SPECIES = ["Cão", "Gato", "Ave", "Roedor", "Coelho", "Réptil", "Outro"] as const;
const DURATION_OPTIONS = [15, 30, 45, 60, 90, 120];

type ReasonStatus = Extract<AppointmentStatus, "cancelled" | "no-show">;

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

const emptyForm = (scheduledAt: string, vetId = 0): AppointmentCreate => ({
  pet_id: 0,
  vet_id: vetId,
  scheduled_at: scheduledAt,
  duration_min: 30,
  reason: "",
  notes: "",
  weight: undefined,
  service_type_id: undefined,
});

export default function Appointments() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const toast = useToast();
  const canWriteClinical = user?.role === "admin" || user?.role === "vet";
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [vets, setVets] = useState<VetOption[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [filterStartDate, setFilterStartDate] = useState(clinicDateInput());
  const [filterEndDate, setFilterEndDate] = useState(clinicDateInput());
  const [form, setForm] = useState<AppointmentCreate>(emptyForm(""));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [reasonTarget, setReasonTarget] = useState<{ appointment: Appointment; status: ReasonStatus } | null>(null);
  const [showQuickPet, setShowQuickPet] = useState(false);
  const [savingPet, setSavingPet] = useState(false);
  const [petError, setPetError] = useState("");
  const [petForm, setPetForm] = useState<PetCreate>({ owner_id: 0, name: "", species: "Cão" });
  const [showQuickOwner, setShowQuickOwner] = useState(false);
  const [savingOwner, setSavingOwner] = useState(false);
  const [ownerError, setOwnerError] = useState("");
  const [ownerForm, setOwnerForm] = useState<OwnerCreate>({ name: "", phone: "", email: "" });
  const petSearch = useRemoteOptions((query) => petsApi.list({ q: query, limit: 50 }).then((response) => response.data));
  const ownerSearch = useRemoteOptions((query) => ownersApi.list({ q: query, limit: 50 }).then((response) => response.data));

  function load() {
    setLoading(true);
    setError("");
    Promise.all([appointmentsApi.list({ dateFrom: filterStartDate, dateTo: filterEndDate, limit: OPTIONS_LIMIT }), petsApi.list({ limit: OPTIONS_LIMIT }), ownersApi.list({ limit: OPTIONS_LIMIT }), appointmentsApi.vets(), serviceTypesApi.list()])
      .then(([apptsRes, petsRes, ownersRes, vetsRes, serviceTypesRes]) => {
        setAppointments(apptsRes.data);
        setPets(petsRes.data);
        setOwners(ownersRes.data);
        setVets(vetsRes.data);
        setServiceTypes(serviceTypesRes.data);
      })
      .catch((requestError: unknown) => setError(apiErrorMessage(requestError, t, "appointments.error")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [filterStartDate, filterEndDate]);

  function openCreate() {
    const ownVet = user?.role === "vet" ? user.id : 0;
    setEditingAppointment(null);
    setForm(emptyForm(`${filterStartDate}T09:00`, ownVet));
    setFormError("");
    setShowForm(true);
  }

  function openReschedule(appointment: Appointment) {
    setEditingAppointment(appointment);
    setForm({
      pet_id: appointment.pet_id,
      vet_id: appointment.vet_id,
      scheduled_at: clinicDateTimeInput(parseApiDate(appointment.scheduled_at)),
      duration_min: appointment.duration_min,
      reason: appointment.reason ?? "",
      notes: appointment.notes ?? "",
      weight: undefined,
      service_type_id: appointment.service_type_id ?? undefined,
    });
    setFormError("");
    setShowForm(true);
  }

  function openQuickPet() {
    setPetError("");
    setPetForm({ owner_id: 0, name: "", species: "Cão" });
    setShowQuickPet(true);
  }

  function handlePetSelection(value: string) {
    if (value === CREATE_PET_VALUE) {
      openQuickPet();
      return;
    }
    setForm({ ...form, pet_id: Number(value) });
  }

  function openQuickOwner() {
    setOwnerError("");
    setOwnerForm({ name: "", phone: "", email: "" });
    setShowQuickOwner(true);
  }

  function handleOwnerSelection(value: string) {
    if (value === CREATE_OWNER_VALUE) {
      openQuickOwner();
      return;
    }
    setPetForm({ ...petForm, owner_id: Number(value) });
  }

  async function handleQuickOwnerSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSavingOwner(true);
    setOwnerError("");
    try {
      const response = await ownersApi.create({
        ...ownerForm,
        phone: ownerForm.phone || undefined,
        email: ownerForm.email || undefined,
      });
      const createdOwner = response.data;
      setOwners((current) => [createdOwner, ...current]);
      setPetForm((current) => ({ ...current, owner_id: createdOwner.id }));
      setShowQuickOwner(false);
    } catch (requestError: unknown) {
      setOwnerError(apiErrorMessage(requestError, t, "owners.error"));
    } finally {
      setSavingOwner(false);
    }
  }

  async function handleQuickPetSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!petForm.owner_id) {
      setPetError(t("pets.form.ownerRequired"));
      return;
    }
    setSavingPet(true);
    setPetError("");
    try {
      const response = await petsApi.create(petForm);
      const createdPet = response.data;
      setPets((current) => [createdPet, ...current]);
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
    if (!form.pet_id || !form.vet_id) {
      setFormError(t(!form.pet_id ? "appointments.form.animalRequired" : "appointments.form.vetRequired"));
      return;
    }
    setSaving(true);
    setFormError("");
    try {
      if (editingAppointment) {
        await appointmentsApi.update(editingAppointment.id, {
          pet_id: form.pet_id,
          vet_id: form.vet_id,
          scheduled_at: form.scheduled_at,
          duration_min: form.duration_min,
          reason: form.reason,
          notes: form.notes,
          service_type_id: form.service_type_id,
        });
        toast.success(t("appointments.rescheduled"));
      } else {
        await appointmentsApi.create(form);
        toast.success(t("appointments.created"));
      }
      setShowForm(false);
      load();
    } catch (requestError: unknown) {
      setFormError(apiErrorMessage(requestError, t, "appointments.error"));
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(appointment: Appointment, status: AppointmentStatus, statusReason?: string) {
    setBusyId(appointment.id);
    setError("");
    try {
      await appointmentsApi.update(appointment.id, { status, status_reason: statusReason });
      setReasonTarget(null);
      load();
    } catch (requestError: unknown) {
      toast.error(apiErrorMessage(requestError, t, "appointments.error"));
    } finally {
      setBusyId(null);
    }
  }

  function petLabel(pet: Pet) {
    return pet.owner_name ? `${pet.name} · ${pet.owner_name}` : pet.name;
  }

  const petOptions = petSearch.withFound(pets);
  const ownerOptions = ownerSearch.withFound(owners);

  const startLabel = new Date(filterStartDate + "T12:00:00Z").toLocaleDateString(
    "pt-AO",
    filterStartDate === filterEndDate
      ? { weekday: "long", day: "numeric", month: "long", timeZone: "Africa/Luanda" }
      : { day: "2-digit", month: "short", year: "numeric", timeZone: "Africa/Luanda" },
  );
  const endLabel = new Date(filterEndDate + "T12:00:00Z").toLocaleDateString(
    "pt-AO",
    { day: "2-digit", month: "short", year: "numeric", timeZone: "Africa/Luanda" },
  );
  const filterLabel = filterStartDate === filterEndDate
    ? startLabel
    : t("appointments.dateRange.label", { start: startLabel, end: endLabel });
  const multiDay = filterStartDate !== filterEndDate;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">{t("appointments.title")}</h2>
          <p className="text-dark-400 text-sm mt-0.5 capitalize">{filterLabel}</p>
        </div>
        <div className="flex w-full flex-wrap items-end gap-3 sm:w-auto">
          <div className="min-w-0 flex-1 space-y-1 sm:flex-none">
            <Label htmlFor="appointments-date-from" className="text-xs font-semibold text-dark-500">
              {t("appointments.dateRange.from")}
            </Label>
            <input
              id="appointments-date-from"
              type="date"
              value={filterStartDate}
              max={filterEndDate}
              onChange={(event) => event.target.value && setFilterStartDate(event.target.value)}
              required
              className="h-10 w-full rounded-xl border border-dark-200 bg-white px-3 text-sm text-dark-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="min-w-0 flex-1 space-y-1 sm:flex-none">
            <Label htmlFor="appointments-date-to" className="text-xs font-semibold text-dark-500">
              {t("appointments.dateRange.to")}
            </Label>
            <input
              id="appointments-date-to"
              type="date"
              value={filterEndDate}
              min={filterStartDate}
              onChange={(event) => event.target.value && setFilterEndDate(event.target.value)}
              required
              className="h-10 w-full rounded-xl border border-dark-200 bg-white px-3 text-sm text-dark-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <Button
            onClick={openCreate}
            className="h-10 bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
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
                  <TableHead className="pl-5 w-24">{t("appointments.table.time")}</TableHead>
                  <TableHead>{t("appointments.table.animal")}</TableHead>
                  <TableHead className="hidden md:table-cell">{t("appointments.table.vet")}</TableHead>
                  <TableHead>{t("appointments.table.reason")}</TableHead>
                  <TableHead>{t("appointments.table.status")}</TableHead>
                  <TableHead className="pr-5 text-right">{t("appointments.table.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {appointments.map((a) => {
                  const cfg = statusConfig(a.status);
                  const scheduledAt = parseApiDate(a.scheduled_at);
                  const busy = busyId === a.id;
                  return (
                    <TableRow key={a.id}>
                      <TableCell className="pl-5">
                        {multiDay && (
                          <div className="text-[11px] font-semibold uppercase text-dark-400">
                            {scheduledAt.toLocaleDateString("pt-AO", { day: "2-digit", month: "short", timeZone: "Africa/Luanda" })}
                          </div>
                        )}
                        <div className="font-bold text-sm text-dark-900">
                          {scheduledAt.toLocaleTimeString("pt-AO", {
                            hour: "2-digit",
                            minute: "2-digit",
                            timeZone: "Africa/Luanda",
                          })}
                        </div>
                        <div className="text-dark-400 text-xs">{t("common.minutesShort", { count: a.duration_min })}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap items-center gap-1.5">
                          <Link to={`/pets/${a.pet_id}`} className="font-medium text-sm text-dark-900 hover:text-brand-700 hover:underline">
                            {a.pet_name ?? pets.find((pet) => pet.id === a.pet_id)?.name ?? "—"}
                          </Link>
                          {a.subject_archived && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-dark-100 px-2 py-0.5 text-[11px] font-semibold text-dark-600">
                              <Archive className="size-3" aria-hidden="true" />
                              {t("common.archived")}
                            </span>
                          )}
                        </div>
                        {a.owner_name && <div className="text-xs text-dark-400">{a.owner_name}</div>}
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <span className="text-sm text-dark-600">{a.vet_name ?? vets.find((vet) => vet.id === a.vet_id)?.name ?? "—"}</span>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm text-dark-700">{a.reason || "—"}</div>
                        {a.notes && <div className="max-w-56 truncate text-xs text-dark-400" title={a.notes}>{a.notes}</div>}
                        {a.status_reason && <div className="max-w-56 truncate text-xs text-dark-400" title={a.status_reason}>{a.status_reason}</div>}
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold",
                            cfg.bg,
                            cfg.text
                          )}
                        >
                          <span className={cn("w-1.5 h-1.5 rounded-full", cfg.dot)} aria-hidden="true" />
                          {t(`appointments.status.${cfg.key}`)}
                        </span>
                      </TableCell>
                      <TableCell className="pr-5">
                        <div className="flex flex-wrap justify-end gap-2">
                          {a.status !== "cancelled" && a.status !== "no-show" && (
                            <Link
                              to={`/appointments/${a.id}/clinical`}
                              className="inline-flex items-center gap-1 rounded-lg bg-dark-100 px-2.5 py-1 text-xs font-semibold text-dark-700 transition-colors hover:bg-dark-200"
                            >
                              <ClipboardList className="size-3.5" aria-hidden="true" />
                              {t("appointments.actions.record")}
                            </Link>
                          )}
                          {a.status === "scheduled" && (
                            <>
                              {canWriteClinical && !a.subject_archived && (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => changeStatus(a, "in-progress")}
                                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors disabled:opacity-50"
                                >
                                  <Check className="w-3.5 h-3.5" aria-hidden="true" />
                                  {t("appointments.actions.start")}
                                </button>
                              )}
                              {!a.subject_archived && (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => openReschedule(a)}
                                  className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors disabled:opacity-50"
                                  aria-label={t("appointments.actions.reschedule")}
                                  title={t("appointments.actions.reschedule")}
                                >
                                  <CalendarClock className="w-3.5 h-3.5" />
                                </button>
                              )}
                              <button
                                type="button"
                                disabled={busy}
                                onClick={() => setReasonTarget({ appointment: a, status: "cancelled" })}
                                className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors disabled:opacity-50"
                                aria-label={t("appointments.actions.cancel")}
                                title={t("appointments.actions.cancel")}
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                disabled={busy}
                                onClick={() => setReasonTarget({ appointment: a, status: "no-show" })}
                                className="px-2.5 py-1 rounded-lg bg-dark-100 text-dark-600 hover:bg-dark-200 text-xs font-semibold transition-colors disabled:opacity-50"
                              >
                                {t("appointments.actions.noShow")}
                              </button>
                            </>
                          )}
                          {a.status === "in-progress" && canWriteClinical && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => changeStatus(a, "completed")}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors disabled:opacity-50"
                            >
                              <Check className="w-3.5 h-3.5" aria-hidden="true" />
                              {t("appointments.actions.complete")}
                            </button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <FormDialog
        open={showForm}
        onOpenChange={setShowForm}
        title={t(editingAppointment ? "appointments.reschedule.title" : "appointments.new")}
        description={editingAppointment
          ? t("appointments.reschedule.hint", { name: editingAppointment.pet_name ?? "" })
          : t("appointments.create")}
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 px-6 py-5">
            <FormError message={formError} />
            <div className="space-y-1.5">
              <Label htmlFor="appointment-pet" className="text-xs font-semibold text-dark-600">{t("appointments.form.animal")} *</Label>
              <FormSelect
                id="appointment-pet"
                value={form.pet_id || null}
                onValueChange={handlePetSelection}
                onSearchChange={petSearch.onSearchChange}
                options={[
                  ...(editingAppointment ? [] : [{
                    value: CREATE_PET_VALUE,
                    label: `+ ${t("appointments.form.createAnimal")}`,
                    variant: "action" as const,
                  }]),
                  ...petOptions.map((pet) => ({ value: pet.id, label: petLabel(pet) })),
                ]}
                placeholder={t("appointments.form.selectAnimal")}
                className="h-11 border-dark-200 bg-white"
                ariaLabel={t("appointments.form.animal")}
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="appointment-vet" className="text-xs font-semibold text-dark-600">{t("appointments.form.vet")} *</Label>
              <FormSelect
                id="appointment-vet"
                value={form.vet_id || null}
                onValueChange={(value) => setForm({ ...form, vet_id: Number(value) })}
                options={vets.map((vet) => ({ value: vet.id, label: vet.name }))}
                placeholder={t("appointments.form.selectVet")}
                className="h-11 border-dark-200 bg-white"
                ariaLabel={t("appointments.form.vet")}
                required
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_9rem]">
              <div className="space-y-1.5">
                <Label htmlFor="appointment-datetime" className="text-xs font-semibold text-dark-600">{t("appointments.form.dateTime")} *</Label>
                <Input
                  id="appointment-datetime"
                  type="datetime-local"
                  value={form.scheduled_at}
                  onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                  required
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="appointment-duration" className="text-xs font-semibold text-dark-600">{t("appointments.form.duration")}</Label>
                <FormSelect
                  id="appointment-duration"
                  value={form.duration_min}
                  onValueChange={(value) => setForm({ ...form, duration_min: Number(value) })}
                  options={DURATION_OPTIONS.map((minutes) => ({ value: minutes, label: t("form.minutes", { count: minutes }) }))}
                  className="h-11 border-dark-200 bg-white"
                  ariaLabel={t("appointments.form.duration")}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="appointment-service" className="text-xs font-semibold text-dark-600">{t("appointments.form.service")}</Label>
              <FormSelect
                id="appointment-service"
                value={form.service_type_id ?? ""}
                onValueChange={(value) => setForm({ ...form, service_type_id: value ? Number(value) : undefined })}
                options={[
                  { value: "", label: t("appointments.form.selectService") },
                  ...serviceTypes.filter((service) => service.active).map((service) => ({ value: service.id, label: service.name })),
                ]}
                placeholder={t("appointments.form.selectService")}
                className="h-11 border-dark-200 bg-white"
                ariaLabel={t("appointments.form.service")}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="appointment-reason" className="text-xs font-semibold text-dark-600">{t("appointments.form.reason")}</Label>
              <Input
                id="appointment-reason"
                value={form.reason}
                onChange={(e) => setForm({ ...form, reason: e.target.value })}
                placeholder={t("appointments.form.reasonPlaceholder")}
                className="h-11 rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="appointment-notes" className="text-xs font-semibold text-dark-600">{t("appointments.form.notes")}</Label>
              <Input
                id="appointment-notes"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder={t("appointments.form.notesPlaceholder")}
                className="h-11 rounded-xl"
              />
            </div>

            {canWriteClinical && !editingAppointment && (
              <div className="space-y-1.5">
                <Label htmlFor="appointment-weight" className="text-xs font-semibold text-dark-600">{t("appointments.form.weight")}</Label>
                <Input
                  id="appointment-weight"
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
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-dark-100 px-6 py-4">
            <Button type="button" variant="outline" onClick={() => setShowForm(false)} className="rounded-xl h-11">
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={saving} className="bg-brand-600 hover:bg-brand-700 rounded-xl h-11 font-semibold">
              {saving
                ? t("appointments.saving")
                : t(editingAppointment ? "appointments.reschedule.save" : "appointments.create")}
            </Button>
          </div>
        </form>
      </FormDialog>

      <FormDialog
        open={showQuickPet}
        onOpenChange={setShowQuickPet}
        title={t("appointments.quickPet.title")}
        description={t("appointments.quickPet.hint")}
      >
        <form onSubmit={handleQuickPetSubmit}>
          <div className="space-y-4 px-6 py-5">
            <FormError message={petError} />
            <div className="space-y-1.5">
              <Label htmlFor="quick-pet-owner" className="text-xs font-semibold text-dark-600">{t("pets.form.owner")} *</Label>
              <FormSelect
                id="quick-pet-owner"
                value={petForm.owner_id || null}
                onValueChange={handleOwnerSelection}
                onSearchChange={ownerSearch.onSearchChange}
                options={[
                  {
                    value: CREATE_OWNER_VALUE,
                    label: `+ ${t("appointments.quickPet.createOwner")}`,
                    variant: "action" as const,
                  },
                  ...ownerOptions.map((owner) => ({ value: owner.id, label: owner.phone ? `${owner.name} · ${owner.phone}` : owner.name })),
                ]}
                placeholder={t("pets.form.selectOwner")}
                className="h-11 border-dark-200 bg-white"
                ariaLabel={t("pets.form.owner")}
                required
              />
              {ownerOptions.length === 0 && (
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
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="quick-pet-species" className="text-xs font-semibold text-dark-600">{t("pets.form.species")} *</Label>
              <FormSelect
                id="quick-pet-species"
                value={petForm.species}
                onValueChange={(value) => setPetForm({ ...petForm, species: value })}
                options={PET_SPECIES.map((species) => ({ value: species, label: t(`pets.species.${species}`) }))}
                className="h-11 border-dark-200 bg-white"
                ariaLabel={t("pets.form.species")}
                required
              />
            </div>
          </div>
          <div className="flex items-center justify-end gap-3 border-t border-dark-100 px-6 py-4">
            <Button type="button" variant="outline" onClick={() => setShowQuickPet(false)} className="h-11 rounded-xl">
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={savingPet} className="h-11 rounded-xl bg-brand-600 font-semibold hover:bg-brand-700">
              {savingPet ? t("common.saving") : t("appointments.quickPet.create")}
            </Button>
          </div>
        </form>
      </FormDialog>

      <FormDialog
        open={showQuickOwner}
        onOpenChange={setShowQuickOwner}
        title={t("appointments.quickOwner.title")}
        description={t("appointments.quickOwner.hint")}
      >
        <form onSubmit={handleQuickOwnerSubmit}>
          <div className="space-y-4 px-6 py-5">
            <FormError message={ownerError} />
            <div className="space-y-1.5">
              <Label htmlFor="quick-owner-name" className="text-xs font-semibold text-dark-600">{t("owners.form.name")} *</Label>
              <Input
                id="quick-owner-name"
                value={ownerForm.name}
                onChange={(event) => setOwnerForm({ ...ownerForm, name: event.target.value })}
                className="h-11 rounded-xl"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="quick-owner-phone" className="text-xs font-semibold text-dark-600">{t("owners.form.phone")}</Label>
              <Input
                id="quick-owner-phone"
                type="tel"
                value={ownerForm.phone}
                onChange={(event) => setOwnerForm({ ...ownerForm, phone: event.target.value })}
                placeholder={t("owners.form.phonePlaceholder")}
                className="h-11 rounded-xl"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="quick-owner-email" className="text-xs font-semibold text-dark-600">{t("owners.form.email")}</Label>
              <Input
                id="quick-owner-email"
                type="email"
                value={ownerForm.email}
                onChange={(event) => setOwnerForm({ ...ownerForm, email: event.target.value })}
                placeholder={t("owners.form.emailPlaceholder")}
                className="h-11 rounded-xl"
              />
            </div>
          </div>
          <div className="flex items-center justify-end gap-3 border-t border-dark-100 px-6 py-4">
            <Button type="button" variant="outline" onClick={() => setShowQuickOwner(false)} className="h-11 rounded-xl">
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={savingOwner} className="h-11 rounded-xl bg-brand-600 font-semibold hover:bg-brand-700">
              {savingOwner ? t("common.saving") : t("appointments.quickOwner.create")}
            </Button>
          </div>
        </form>
      </FormDialog>

      <PromptDialog
        open={reasonTarget !== null}
        onOpenChange={(open) => { if (!open) setReasonTarget(null); }}
        title={t(reasonTarget?.status === "no-show" ? "appointments.noShowTitle" : "appointments.cancelTitle", { name: reasonTarget?.appointment.pet_name ?? "" })}
        label={t(reasonTarget?.status === "no-show" ? "appointments.noShowReason" : "appointments.cancelReason")}
        confirmLabel={t(reasonTarget?.status === "no-show" ? "appointments.actions.noShow" : "appointments.actions.cancel")}
        cancelLabel={t("common.back")}
        destructive
        pending={reasonTarget !== null && busyId === reasonTarget.appointment.id}
        onConfirm={(reason) => reasonTarget && changeStatus(reasonTarget.appointment, reasonTarget.status, reason)}
      />
    </div>
  );
}
