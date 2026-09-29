import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, ChevronDown, ChevronRight, ClipboardList, FileText, Plus, Save, Stethoscope, Trash2, UserRound, X } from "lucide-react";

import { appointmentsApi, Appointment, VetOption } from "@/api/appointments";
import { encountersApi, ClinicalMedicationLineInput } from "@/api/encounters";
import { examCatalogApi } from "@/api/examCatalog";
import { ownersApi, Owner } from "@/api/owners";
import { petsApi, Pet } from "@/api/pets";
import { useAuth } from "@/contexts/AuthContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
import type { ExamCatalog, ExamFindingStatus } from "@patas/shared-types";
import { clinicDateInput, parseApiDate } from "@/lib/date";
import { apiErrorMessage } from "@/api/errors";

interface FindingState {
  status: ExamFindingStatus;
  note: string;
}

interface MedicationDraft extends ClinicalMedicationLineInput {
  status?: string;
}

const emptyMedication = (): MedicationDraft => ({
  name: "",
  dosage: "",
  frequency: "",
  route: "oral",
  start_date: clinicDateInput(),
  end_date: "",
  instructions: "",
  notes: "",
});

export default function ClinicalAppointment() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const appointmentId = Number(id);
  const canWrite = user?.role === "admin" || user?.role === "vet";
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [pet, setPet] = useState<Pet | null>(null);
  const [owner, setOwner] = useState<Owner | null>(null);
  const [vets, setVets] = useState<VetOption[]>([]);
  const [catalog, setCatalog] = useState<ExamCatalog>({ systems: [] });
  const [findingState, setFindingState] = useState<Record<number, FindingState>>({});
  const [openSystems, setOpenSystems] = useState<Set<number>>(new Set());
  const [medications, setMedications] = useState<MedicationDraft[]>([]);
  const [form, setForm] = useState({ anamnesis: "", diagnosis: "", notes: "", prescription: "", consultation_type: "normal", referring_vet_id: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!appointmentId) return;
    Promise.all([
      appointmentsApi.get(appointmentId),
      petsApi.list(true),
      ownersApi.list(true),
      appointmentsApi.vets(),
      examCatalogApi.get(),
      encountersApi.get(appointmentId),
    ])
      .then(([appointmentResponse, petsResponse, ownersResponse, vetsResponse, catalogResponse, recordResponse]) => {
        const nextAppointment = appointmentResponse.data;
        const record = recordResponse.data;
        setAppointment(nextAppointment);
        setPet(petsResponse.data.find((item) => item.id === nextAppointment.pet_id) ?? null);
        setOwner(ownersResponse.data.find((item) => item.id === nextAppointment.owner_id) ?? null);
        setVets(vetsResponse.data);
        setCatalog(catalogResponse.data);
        const nextFindingState: Record<number, FindingState> = {};
        catalogResponse.data.systems.forEach((system) => system.findings.filter((finding) => finding.active).forEach((finding) => { nextFindingState[finding.id] = { status: "not-evaluated", note: "" }; }));
        record.exam_findings.forEach((finding) => { nextFindingState[finding.finding_id] = { status: finding.status, note: finding.note ?? "" }; });
        setFindingState(nextFindingState);
        setOpenSystems(new Set(catalogResponse.data.systems.slice(0, 1).map((system) => system.id)));
        setMedications(record.medications.map((medication) => ({ ...medication, end_date: medication.end_date ?? "", instructions: medication.instructions ?? "", notes: medication.notes ?? "" })));
        setForm({
          anamnesis: record.treatment?.anamnesis ?? "",
          diagnosis: record.treatment?.diagnosis ?? "",
          notes: record.treatment?.notes ?? "",
          prescription: record.treatment?.prescription ?? "",
          consultation_type: record.treatment?.consultation_type ?? "normal",
          referring_vet_id: record.treatment?.referring_vet_id ? String(record.treatment.referring_vet_id) : "",
        });
      })
      .catch(() => setMessage(t("clinicalAppointment.errors.load")))
      .finally(() => setLoading(false));
  }, [appointmentId]);

  const findingCount = useMemo(() => Object.values(findingState).filter((item) => item.status === "abnormal").length, [findingState]);

  function toggleSystem(systemId: number) {
    setOpenSystems((current) => {
      const next = new Set(current);
      if (next.has(systemId)) next.delete(systemId); else next.add(systemId);
      return next;
    });
  }

  function setFinding(findingId: number, data: Partial<FindingState>) {
    setFindingState((current) => ({ ...current, [findingId]: { ...(current[findingId] ?? { status: "not-evaluated", note: "" }), ...data } }));
  }

  function updateMedication(index: number, data: Partial<MedicationDraft>) {
    setMedications((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...data } : item));
  }

  async function save(event?: FormEvent): Promise<boolean> {
    event?.preventDefault();
    if (!canWrite) return false;
    setSaving(true);
    setMessage(null);
    try {
      const response = await encountersApi.save(appointmentId, {
        ...form,
        referring_vet_id: form.referring_vet_id ? Number(form.referring_vet_id) : null,
        exam_findings: Object.entries(findingState).map(([findingId, state]) => ({ finding_id: Number(findingId), status: state.status, note: state.note || undefined })),
        medications: medications.filter((medication) => medication.name.trim()).map(({ status: _status, ...medication }) => ({ ...medication, end_date: medication.end_date || undefined, instructions: medication.instructions || undefined, notes: medication.notes || undefined })),
      });
      setMedications(response.data.medications.map((medication) => ({ ...medication, end_date: medication.end_date ?? "", instructions: medication.instructions ?? "", notes: medication.notes ?? "" })));
      setMessage(t("clinicalAppointment.saved"));
      return true;
    } catch {
      setMessage(t("clinicalAppointment.errors.save"));
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function completeAppointment() {
    if (transitioning) return;
    setTransitioning(true);
    try {
      const saved = await save();
      if (!saved) return;
      await appointmentsApi.update(appointmentId, { status: "completed" });
      setAppointment((current) => current ? { ...current, status: "completed" } : current);
      setMessage(t("clinicalAppointment.completed"));
    } catch {
      setMessage(t("clinicalAppointment.errors.complete"));
    } finally {
      setTransitioning(false);
    }
  }

  async function startAppointment() {
    if (transitioning) return;
    setTransitioning(true);
    setMessage(null);
    try {
      await appointmentsApi.update(appointmentId, { status: "in-progress" });
      setAppointment((current) => current ? { ...current, status: "in-progress" } : current);
      setMessage(t("clinicalAppointment.started"));
    } catch (requestError: unknown) {
      setMessage(apiErrorMessage(requestError, t, "clinicalAppointment.errors.start"));
    } finally {
      setTransitioning(false);
    }
  }

  if (loading) return <div className="flex h-64 items-center justify-center"><div className="size-7 animate-spin rounded-full border-2 border-primary/30 border-t-primary" /></div>;
  if (!appointment || !pet) return <div className="py-16 text-center text-sm text-muted-foreground">{t("clinicalAppointment.errors.notFound")}</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" onClick={() => navigate(-1)}><ArrowLeft className="mr-2 size-4" />{t("common.back")}</Button>
        <div className="flex items-center gap-2">{message && <span className="text-sm text-muted-foreground">{message}</span>}{canWrite && <Button onClick={() => save()} disabled={saving || transitioning}><Save className="mr-2 size-4" />{saving ? t("common.saving") : t("clinicalAppointment.save")}</Button>}{canWrite && appointment.status === "scheduled" && <Button variant="outline" onClick={startAppointment} disabled={transitioning}>{t("clinicalAppointment.start")}</Button>}{canWrite && appointment.status === "in-progress" && <Button variant="outline" onClick={completeAppointment} disabled={saving || transitioning}>{t("clinicalAppointment.complete")}</Button>}</div>
      </div>

      <Card className="overflow-hidden"><CardContent className="p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div className="flex items-start gap-3"><div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground"><Stethoscope className="size-5" /></div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 className="break-words text-xl font-extrabold text-foreground">{pet.name}</h2><Badge variant="outline">{pet.species}</Badge>{pet.breed && <Badge variant="outline">{pet.breed}</Badge>}{pet.archived_at && <Badge variant="destructive">{t("common.archived")}</Badge>}</div><p className="mt-1 text-sm text-muted-foreground">{owner?.name ?? "—"} · {parseApiDate(appointment.scheduled_at).toLocaleString("pt-AO", { dateStyle: "short", timeStyle: "short", timeZone: "Africa/Luanda" })}</p></div></div><div className="text-right"><p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("clinicalAppointment.responsible")}</p><p className="mt-1 text-sm font-bold text-foreground">{vets.find((vet) => vet.id === appointment.vet_id)?.name ?? "—"}</p><Badge className="mt-2" variant="secondary">{t(`status.${appointment.status}`)}</Badge></div></div></CardContent></Card>

      <form onSubmit={save} className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(22rem,0.9fr)]">
        <div className="space-y-6">
          <Card><div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("clinicalAppointment.examTitle")}</h3><p className="mt-0.5 text-xs text-muted-foreground">{t("clinicalAppointment.examHint")}</p></div><Badge variant="outline">{findingCount} {t("clinicalAppointment.abnormal")}</Badge></div><CardContent className="p-3">{catalog.systems.filter((system) => system.active).map((system) => { const open = openSystems.has(system.id); return <section key={system.id} className="border-b border-border/60 last:border-0"><button type="button" onClick={() => toggleSystem(system.id)} className="flex w-full items-center gap-2 px-2 py-3 text-left text-sm font-bold text-foreground">{open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}{system.name}<span className="ml-auto text-xs font-normal text-muted-foreground">{system.findings.filter((finding) => finding.active && findingState[finding.id]?.status === "abnormal").length}</span></button>{open && <div className="space-y-2 px-2 pb-4">{system.findings.filter((finding) => finding.active).map((finding) => { const state = findingState[finding.id] ?? { status: "not-evaluated" as ExamFindingStatus, note: "" }; return <div key={finding.id} className="grid gap-2 rounded-xl border border-border/70 p-3 sm:grid-cols-[minmax(0,1fr)_9rem] sm:items-center"><span className="text-sm text-foreground">{finding.name}</span><FormSelect value={state.status} disabled={!canWrite} onValueChange={(value) => setFinding(finding.id, { status: value as ExamFindingStatus })} options={[{ value: "not-evaluated", label: t("clinicalAppointment.finding.notEvaluated") }, { value: "normal", label: t("clinicalAppointment.finding.normal") }, { value: "abnormal", label: t("clinicalAppointment.finding.abnormal") }]} className="h-9 rounded-lg px-2 text-xs" />{state.status === "abnormal" && <Input value={state.note} disabled={!canWrite} onChange={(event) => setFinding(finding.id, { note: event.target.value })} placeholder={t("clinicalAppointment.finding.note")} className="sm:col-span-2" />}</div>; })}</div>}</section>; })}</CardContent></Card>
          <Card><div className="border-b border-border/70 px-5 py-4"><h3 className="font-bold text-foreground">{t("clinicalAppointment.historyTitle")}</h3></div><CardContent className="space-y-4 p-5"><Field label={t("clinicalAppointment.anamnesis")}><textarea rows={5} disabled={!canWrite} value={form.anamnesis} onChange={(event) => setForm({ ...form, anamnesis: event.target.value })} className="w-full resize-y rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/30" /></Field><div className="grid gap-4 sm:grid-cols-2"><Field label={t("clinicalAppointment.consultationType")}><FormSelect disabled={!canWrite} value={form.consultation_type} onValueChange={(value) => setForm({ ...form, consultation_type: value })} options={[{ value: "normal", label: t("clinicalAppointment.types.normal") }, { value: "urgente", label: t("clinicalAppointment.types.urgent") }, { value: "retorno", label: t("clinicalAppointment.types.return") }]} /></Field><Field label={t("clinicalAppointment.referringVet")}><FormSelect disabled={!canWrite} value={form.referring_vet_id} onValueChange={(value) => setForm({ ...form, referring_vet_id: value })} options={[{ value: "", label: t("clinicalAppointment.noReferringVet") }, ...vets.map((vet) => ({ value: vet.id, label: vet.name }))]} /></Field></div><Field label={t("clinicalAppointment.diagnosis")}><textarea rows={4} disabled={!canWrite} value={form.diagnosis} onChange={(event) => setForm({ ...form, diagnosis: event.target.value })} className="w-full resize-y rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/30" /></Field><Field label={t("clinicalAppointment.notes")}><textarea rows={3} disabled={!canWrite} value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} className="w-full resize-y rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/30" /></Field></CardContent></Card>
        </div>

        <div className="space-y-6"><Card><div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("clinicalAppointment.prescriptionTitle")}</h3><p className="mt-0.5 text-xs text-muted-foreground">{t("clinicalAppointment.prescriptionHint")}</p></div>{canWrite && <Button type="button" size="sm" variant="outline" onClick={() => setMedications((current) => [...current, emptyMedication()])}><Plus className="mr-1.5 size-3.5" />{t("clinicalAppointment.addMedication")}</Button>}</div><CardContent className="space-y-4 p-5">{medications.length === 0 ? <div className="py-8 text-center text-sm text-muted-foreground">{t("clinicalAppointment.noMedications")}</div> : medications.map((medication, index) => <div key={medication.id ?? `new-${index}`} className="space-y-3 rounded-xl border border-border/70 p-4"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><ClipboardList className="size-4 text-primary" /><span className="text-sm font-semibold text-foreground">{medication.name || t("clinicalAppointment.newMedication")}</span></div>{canWrite && !medication.id && <Button type="button" size="icon-xs" variant="ghost" onClick={() => setMedications((current) => current.filter((_, itemIndex) => itemIndex !== index))}><Trash2 className="size-3.5 text-destructive" /></Button>}</div><div className="grid gap-3 sm:grid-cols-2"><Field label={t("clinicalAppointment.medication.name")}><Input disabled={!canWrite} value={medication.name} onChange={(event) => updateMedication(index, { name: event.target.value })} /></Field><Field label={t("clinicalAppointment.medication.dosage")}><Input disabled={!canWrite} value={medication.dosage} onChange={(event) => updateMedication(index, { dosage: event.target.value })} /></Field><Field label={t("clinicalAppointment.medication.frequency")}><Input disabled={!canWrite} value={medication.frequency} onChange={(event) => updateMedication(index, { frequency: event.target.value })} /></Field><Field label={t("clinicalAppointment.medication.route")}><Input disabled={!canWrite} value={medication.route} onChange={(event) => updateMedication(index, { route: event.target.value })} /></Field><Field label={t("clinicalAppointment.medication.start")}><Input disabled={!canWrite} type="date" value={medication.start_date} onChange={(event) => updateMedication(index, { start_date: event.target.value })} /></Field><Field label={t("clinicalAppointment.medication.end")}><Input disabled={!canWrite} type="date" value={medication.end_date ?? ""} onChange={(event) => updateMedication(index, { end_date: event.target.value })} /></Field></div><Field label={t("clinicalAppointment.medication.instructions")}><Input disabled={!canWrite} value={medication.instructions ?? ""} onChange={(event) => updateMedication(index, { instructions: event.target.value })} /></Field></div>)}</CardContent></Card><Card><div className="border-b border-border/70 px-5 py-4"><h3 className="font-bold text-foreground">{t("clinicalAppointment.freePrescription")}</h3></div><CardContent className="p-5"><textarea rows={6} disabled={!canWrite} value={form.prescription} onChange={(event) => setForm({ ...form, prescription: event.target.value })} className="w-full resize-y rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/30" placeholder={t("clinicalAppointment.freePrescriptionPlaceholder")} /></CardContent></Card><Card><CardContent className="space-y-3 p-5"><div className="flex items-center gap-2 text-sm font-semibold text-foreground"><UserRound className="size-4 text-primary" />{t("clinicalAppointment.petSummary")}</div><p className="text-sm text-muted-foreground">{pet.species}{pet.breed ? ` · ${pet.breed}` : ""}{pet.weight ? ` · ${pet.weight} kg` : ""}</p><Button type="button" variant="outline" className="w-full" onClick={() => navigate(`/pets/${pet.id}`)}><FileText className="mr-2 size-4" />{t("clinicalAppointment.openPet")}</Button></CardContent></Card></div>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5"><span className="text-xs font-semibold text-muted-foreground">{label}</span>{children}</label>;
}
