import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CalendarDays, Check, ChevronRight, Clock3, DoorOpen, MessageSquare, PawPrint, PhoneCall, Plus, Search, UserRound, X } from "lucide-react";

import { appointmentsApi, Appointment, VetOption } from "@/api/appointments";
import { petsApi, Pet } from "@/api/pets";
import { serviceTypesApi } from "@/api/serviceTypes";
import { waitingRoomApi } from "@/api/waitingRoom";
import { useAuth } from "@/contexts/AuthContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
import type { ServiceType, WaitingRoomEntry, WaitingRoomStatus } from "@patas/shared-types";
import { clinicDateInput, parseApiDate } from "@/lib/date";

function statusStyle(status: WaitingRoomStatus) {
  if (status === "in-progress") return "bg-blue-50 text-blue-700";
  if (status === "completed") return "bg-emerald-50 text-emerald-700";
  if (status === "cancelled") return "bg-red-50 text-red-700";
  if (status === "no-show") return "bg-slate-100 text-slate-600";
  if (status === "called") return "bg-violet-50 text-violet-700";
  return "bg-amber-50 text-amber-700";
}

export default function WaitingRoom() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [date, setDate] = useState(clinicDateInput());
  const [entries, setEntries] = useState<WaitingRoomEntry[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [pets, setPets] = useState<Pet[]>([]);
  const [vets, setVets] = useState<VetOption[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [showWalkIn, setShowWalkIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ pet_id: 0, vet_id: 0, service_type_id: 0, reason: "", room: "", message: "" });

  const canWrite = Boolean(user);
  const canClinical = user?.role === "admin" || user?.role === "vet";

  function load() {
    setLoading(true);
    Promise.all([
      waitingRoomApi.list({ date, q: search || undefined }),
      appointmentsApi.list(date),
      petsApi.list(),
      appointmentsApi.vets(),
      serviceTypesApi.list(),
    ])
      .then(([entriesResponse, appointmentsResponse, petsResponse, vetsResponse, servicesResponse]) => {
        setEntries(entriesResponse.data);
        setAppointments(appointmentsResponse.data);
        setPets(petsResponse.data);
        setVets(vetsResponse.data);
        setServiceTypes(servicesResponse.data);
      })
      .catch(() => window.alert(t("waitingRoom.errors.load")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [date]);

  useEffect(() => {
    const timer = window.setTimeout(() => load(), 250);
    return () => window.clearTimeout(timer);
  }, [search]);

  const visibleEntries = useMemo(() => {
    if (filter === "all") return entries;
    return entries.filter((entry) => String(entry.service_type_id) === filter);
  }, [entries, filter]);

  const queuedAppointmentIds = useMemo(() => new Set(entries.map((entry) => entry.appointment_id)), [entries]);
  const scheduledAppointments = appointments.filter((appointment) => appointment.status === "scheduled" && !queuedAppointmentIds.has(appointment.id));

  function openWalkIn() {
    setForm({
      pet_id: pets[0]?.id ?? 0,
      vet_id: vets[0]?.id ?? 0,
      service_type_id: serviceTypes[0]?.id ?? 0,
      reason: "",
      room: "",
      message: "",
    });
    setShowWalkIn(true);
  }

  async function addAppointment(appointment: Appointment) {
    try {
      await waitingRoomApi.create({ appointment_id: appointment.id, service_type_id: appointment.service_type_id ?? undefined });
      load();
    } catch {
      window.alert(t("waitingRoom.errors.save"));
    }
  }

  async function createWalkIn(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await waitingRoomApi.create({
        pet_id: form.pet_id,
        vet_id: form.vet_id,
        service_type_id: form.service_type_id || undefined,
        reason: form.reason || undefined,
        room: form.room || undefined,
        message: form.message || undefined,
      });
      setShowWalkIn(false);
      load();
    } catch {
      window.alert(t("waitingRoom.errors.save"));
    } finally {
      setSaving(false);
    }
  }

  async function transition(entry: WaitingRoomEntry, status: WaitingRoomStatus) {
    const requiresReason = status === "cancelled" || status === "no-show";
    const reason = requiresReason ? window.prompt(t(status === "cancelled" ? "waitingRoom.actions.cancelPrompt" : "waitingRoom.actions.noShowPrompt")) ?? "" : undefined;
    if (requiresReason && !reason?.trim()) return;
    try {
      await waitingRoomApi.transition(entry.id, { status, reason });
      load();
    } catch {
      window.alert(t("waitingRoom.errors.transition"));
    }
  }

  function statusLabel(status: WaitingRoomStatus) {
    return t(`waitingRoom.status.${status}`);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{t("waitingRoom.eyebrow")}</p>
          <h2 className="mt-1 text-2xl font-extrabold text-foreground">{t("waitingRoom.title")}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t("waitingRoom.subtitle")}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Input type="date" value={date} onChange={(event) => setDate(event.target.value)} className="h-10 w-40 rounded-xl" />
          {canWrite && <Button onClick={openWalkIn} className="rounded-xl"><Plus className="mr-2 size-4" />{t("waitingRoom.newWalkIn")}</Button>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
        <button onClick={() => setFilter("all")} className={`rounded-2xl border p-4 text-left transition ${filter === "all" ? "border-primary bg-primary/5" : "border-border bg-card hover:bg-muted/50"}`}>
          <p className="text-xs font-semibold text-muted-foreground">{t("waitingRoom.all")}</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{entries.length}</p>
        </button>
        {serviceTypes.map((service) => {
          const count = entries.filter((entry) => entry.service_type_id === service.id).length;
          return <button key={service.id} onClick={() => setFilter(String(service.id))} className={`rounded-2xl border p-4 text-left transition ${filter === String(service.id) ? "border-primary bg-primary/5" : "border-border bg-card hover:bg-muted/50"}`}>
            <p className="truncate text-xs font-semibold text-muted-foreground">{service.name}</p>
            <p className="mt-1 text-2xl font-bold text-foreground">{count}</p>
          </button>;
        })}
      </div>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 px-5 py-4">
          <div><h3 className="font-bold text-foreground">{t("waitingRoom.queueTitle")}</h3><p className="mt-0.5 text-xs text-muted-foreground">{t("waitingRoom.queueHint")}</p></div>
          <div className="relative w-full sm:w-64"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t("waitingRoom.search")} className="h-9 rounded-xl pl-9" /></div>
        </div>
        <CardContent className="p-0">
          {loading ? <div className="flex justify-center py-16"><div className="size-6 animate-spin rounded-full border-2 border-primary/30 border-t-primary" /></div> : visibleEntries.length === 0 ? <div className="flex flex-col items-center py-16 text-muted-foreground"><Clock3 className="mb-3 size-10 opacity-30" /><p className="text-sm font-medium">{t("waitingRoom.empty")}</p></div> : (
            <div className="divide-y divide-border/70">
              {visibleEntries.map((entry) => <div key={entry.id} className="flex flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center">
                <div className="flex min-w-0 flex-1 items-start gap-3">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground"><PawPrint className="size-4" /></div>
                  <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><p className="font-bold text-foreground">{entry.pet_name}</p><Badge variant="outline">{entry.service_type_name ?? t("waitingRoom.defaultService")}</Badge><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${statusStyle(entry.status)}`}>{statusLabel(entry.status)}</span></div><p className="mt-1 text-sm text-muted-foreground">{entry.owner_name} · {entry.reason || t("waitingRoom.defaultReason")}</p><div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground"><span className="inline-flex items-center gap-1"><UserRound className="size-3.5" />{entry.vet_name}</span><span className="inline-flex items-center gap-1"><Clock3 className="size-3.5" />{parseApiDate(entry.scheduled_at).toLocaleTimeString("pt-AO", { hour: "2-digit", minute: "2-digit", timeZone: "Africa/Luanda" })}</span>{entry.room && <span className="inline-flex items-center gap-1"><DoorOpen className="size-3.5" />{entry.room}</span>}{entry.message && <span className="inline-flex items-center gap-1"><MessageSquare className="size-3.5" />{entry.message}</span>}</div></div>
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2 lg:w-[26rem]">
                  {entry.status === "waiting" && <Button size="sm" variant="outline" onClick={() => transition(entry, "called")}><PhoneCall className="mr-1.5 size-3.5" />{t("waitingRoom.actions.call")}</Button>}
                  {entry.status === "called" && canClinical && <Button size="sm" onClick={() => transition(entry, "in-progress")}><ChevronRight className="mr-1.5 size-3.5" />{t("waitingRoom.actions.start")}</Button>}
                  {entry.status === "in-progress" && canClinical && <Button size="sm" onClick={() => transition(entry, "completed")}><Check className="mr-1.5 size-3.5" />{t("waitingRoom.actions.complete")}</Button>}
                  {(entry.status === "waiting" || entry.status === "called") && <Button size="sm" variant="ghost" onClick={() => transition(entry, "no-show")}>{t("waitingRoom.actions.noShow")}</Button>}
                  {(entry.status === "waiting" || entry.status === "called") && <Button size="sm" variant="ghost" onClick={() => transition(entry, "cancelled")}><X className="mr-1 size-3.5" />{t("waitingRoom.actions.cancel")}</Button>}
                  <Button size="sm" variant="outline" onClick={() => navigate(`/appointments/${entry.appointment_id}/clinical`)}>{t("waitingRoom.actions.openClinical")}</Button>
                </div>
              </div>)}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("waitingRoom.scheduledTitle")}</h3><p className="mt-0.5 text-xs text-muted-foreground">{t("waitingRoom.scheduledHint")}</p></div><CalendarDays className="size-5 text-muted-foreground" /></div>
        <CardContent className="p-0">{scheduledAppointments.length === 0 ? <p className="px-5 py-8 text-sm text-muted-foreground">{t("waitingRoom.scheduledEmpty")}</p> : <div className="divide-y divide-border/70">{scheduledAppointments.map((appointment) => <div key={appointment.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"><div><p className="font-semibold text-foreground">{pets.find((pet) => pet.id === appointment.pet_id)?.name ?? t("waitingRoom.unknownPet")}</p><p className="text-xs text-muted-foreground">{appointment.reason || t("waitingRoom.defaultReason")} · {parseApiDate(appointment.scheduled_at).toLocaleTimeString("pt-AO", { hour: "2-digit", minute: "2-digit", timeZone: "Africa/Luanda" })}</p></div><Button size="sm" variant="outline" onClick={() => addAppointment(appointment)}><Plus className="mr-1.5 size-3.5" />{t("waitingRoom.actions.checkIn")}</Button></div>)}</div>}</CardContent>
      </Card>

      {showWalkIn && <div className="fixed inset-0 z-50 bg-black/50 p-4 backdrop-blur-sm" onClick={() => setShowWalkIn(false)}><div className="absolute left-1/2 top-1/2 max-h-[calc(100dvh-2rem)] w-full max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl bg-background shadow-2xl" onClick={(event) => event.stopPropagation()}><div className="flex items-center justify-between border-b border-border/70 px-6 py-4"><div><h3 className="font-bold text-foreground">{t("waitingRoom.walkInTitle")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("waitingRoom.walkInHint")}</p></div><Button variant="ghost" size="icon-sm" onClick={() => setShowWalkIn(false)}><X className="size-4" /></Button></div><form onSubmit={createWalkIn} className="grid gap-4 p-6 sm:grid-cols-2"><Field label={t("waitingRoom.form.pet")}><FormSelect required value={form.pet_id || null} onValueChange={(value) => setForm({ ...form, pet_id: Number(value) })} options={pets.map((pet) => ({ value: pet.id, label: pet.name }))} placeholder={t("waitingRoom.form.selectPet")} /></Field><Field label={t("waitingRoom.form.vet")}><FormSelect required value={form.vet_id || null} onValueChange={(value) => setForm({ ...form, vet_id: Number(value) })} options={vets.map((vet) => ({ value: vet.id, label: vet.name }))} placeholder={t("waitingRoom.form.selectVet")} /></Field><Field label={t("waitingRoom.form.service")}><FormSelect required value={form.service_type_id || null} onValueChange={(value) => setForm({ ...form, service_type_id: Number(value) })} options={serviceTypes.filter((service) => service.active).map((service) => ({ value: service.id, label: service.name }))} placeholder={t("waitingRoom.form.selectService")} /></Field><Field label={t("waitingRoom.form.reason")}><Input value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} placeholder={t("waitingRoom.form.reasonPlaceholder")} /></Field><Field label={t("waitingRoom.form.room")}><Input value={form.room} onChange={(event) => setForm({ ...form, room: event.target.value })} placeholder={t("waitingRoom.form.roomPlaceholder")} /></Field><Field label={t("waitingRoom.form.message")}><Input value={form.message} onChange={(event) => setForm({ ...form, message: event.target.value })} placeholder={t("waitingRoom.form.messagePlaceholder")} /></Field><div className="flex justify-end gap-2 border-t border-border/70 pt-4 sm:col-span-2"><Button type="button" variant="ghost" onClick={() => setShowWalkIn(false)}>{t("common.cancel")}</Button><Button type="submit" disabled={saving}>{saving ? t("common.saving") : t("waitingRoom.create")}</Button></div></form></div></div>}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="space-y-1.5"><span className="text-xs font-semibold text-muted-foreground">{label}</span>{children}</label>;
}
