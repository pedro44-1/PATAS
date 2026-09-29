import { FormEvent, useEffect, useMemo, useState } from "react";
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { Appointment, appointmentsApi } from "@/api/appointments";
import {
  clinicalApi,
  Medication,
  MedicationCreate,
  Vaccination,
  VaccinationCreate,
} from "@/api/clinical";
import { PetHistoryTreatment } from "@/api/pets";
import { User } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { clinicDateInput, clinicDateTimeInput, clinicInputToUtc, parseApiDate } from "@/lib/date";
import {
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Edit3,
  FileText,
  Pill,
  Plus,
  Syringe,
  X,
} from "lucide-react";

type ClinicalTab = "timeline" | "vaccinations" | "medications";
type RecordKind = "vaccination" | "medication";

type TimelineEvent = {
  id: string;
  date: string;
  icon: typeof CalendarDays;
  title: string;
  detail: string;
  status: string;
  vetName?: string | null;
};

type TimelineDay = { id: string; label: string; events: TimelineEvent[] };
type TimelineMonth = { id: string; label: string; days: TimelineDay[] };
type TimelineYear = { id: string; label: string; months: TimelineMonth[] };

interface ClinicalHistoryProps {
  petId: number;
  activeTab: ClinicalTab;
  appointments: Appointment[];
  treatments: PetHistoryTreatment[];
  vaccinations: Vaccination[];
  medications: Medication[];
  currentUser: User | null;
  onRecordsChange: (vaccinations: Vaccination[], medications: Medication[]) => void;
}

const emptyVaccination = (vetId = 0): VaccinationCreate => ({
  pet_id: 0,
  vet_id: vetId,
  name: "",
  administered_at: clinicDateTimeInput(),
  dose: "",
});

const emptyMedication = (vetId = 0): MedicationCreate => ({
  pet_id: 0,
  vet_id: vetId,
  name: "",
  dosage: "",
  frequency: "",
  route: "",
  start_date: clinicDateInput(),
});

function dateLabel(value: string) {
  return parseApiDate(value).toLocaleDateString("pt-AO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Africa/Luanda",
  });
}

function timeLabel(value: string) {
  const date = parseApiDate(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("pt-AO", { hour: "2-digit", minute: "2-digit", timeZone: "Africa/Luanda" });
}

function statusClass(status: string) {
  if (status === "active" || status === "administered") return "bg-emerald-50 text-emerald-700";
  if (status === "completed") return "bg-blue-50 text-blue-700";
  if (status === "voided") return "bg-dark-100 text-dark-500";
  return "bg-red-50 text-red-700";
}

export default function ClinicalHistory({
  petId,
  activeTab,
  appointments,
  treatments,
  vaccinations,
  medications,
  currentUser,
  onRecordsChange,
}: ClinicalHistoryProps) {
  const { t } = useTranslation();
  const canWrite = currentUser?.role === "admin" || currentUser?.role === "vet";
  const [vets, setVets] = useState<{ id: number; name: string }[]>([]);
  const [recordKind, setRecordKind] = useState<RecordKind | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [vaccineForm, setVaccineForm] = useState<VaccinationCreate>(emptyVaccination());
  const [medicationForm, setMedicationForm] = useState<MedicationCreate>(emptyMedication());
  const [saving, setSaving] = useState(false);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    appointmentsApi.vets().then((response) => setVets(response.data)).catch(() => setVets([]));
  }, []);

  const appointmentOptions = useMemo(
    () => [...appointments].sort((a, b) => parseApiDate(b.scheduled_at).getTime() - parseApiDate(a.scheduled_at).getTime()),
    [appointments],
  );

  function closeForm() {
    setRecordKind(null);
    setEditingId(null);
  }

  function startVaccination(record?: Vaccination) {
    if (!canWrite) return;
    setEditingId(record?.id ?? null);
    setVaccineForm(record ? {
      pet_id: petId,
      vet_id: record.vet_id,
      appointment_id: record.appointment_id ?? undefined,
      name: record.name,
      administered_at: clinicDateTimeInput(parseApiDate(record.administered_at)),
      dose: record.dose,
      lot_number: record.lot_number ?? undefined,
      expires_at: record.expires_at ?? undefined,
      next_due_at: record.next_due_at ?? undefined,
      notes: record.notes ?? undefined,
    } : { ...emptyVaccination(vets[0]?.id), pet_id: petId });
    setRecordKind("vaccination");
  }

  function startMedication(record?: Medication) {
    if (!canWrite) return;
    setEditingId(record?.id ?? null);
    setMedicationForm(record ? {
      pet_id: petId,
      vet_id: record.vet_id,
      appointment_id: record.appointment_id ?? undefined,
      name: record.name,
      dosage: record.dosage,
      frequency: record.frequency,
      route: record.route,
      start_date: record.start_date,
      end_date: record.end_date ?? undefined,
      instructions: record.instructions ?? undefined,
      notes: record.notes ?? undefined,
    } : { ...emptyMedication(vets[0]?.id), pet_id: petId });
    setRecordKind("medication");
  }

  async function submitVaccination(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const payload = { ...vaccineForm, administered_at: clinicInputToUtc(vaccineForm.administered_at) };
      const response = editingId
        ? await clinicalApi.updateVaccination(editingId, payload)
        : await clinicalApi.createVaccination(payload);
      const next = editingId
        ? vaccinations.map((item) => item.id === editingId ? response.data : item)
        : [response.data, ...vaccinations];
      onRecordsChange(next, medications);
      closeForm();
    } catch {
      window.alert(t("clinical.errors.save"));
    } finally {
      setSaving(false);
    }
  }

  async function submitMedication(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const response = editingId
        ? await clinicalApi.updateMedication(editingId, medicationForm)
        : await clinicalApi.createMedication(medicationForm);
      const next = editingId
        ? medications.map((item) => item.id === editingId ? response.data : item)
        : [response.data, ...medications];
      onRecordsChange(vaccinations, next);
      closeForm();
    } catch {
      window.alert(t("clinical.errors.save"));
    } finally {
      setSaving(false);
    }
  }

  async function voidRecord(kind: RecordKind, id: number) {
    const reason = window.prompt(t("clinical.actions.voidPrompt"));
    if (!reason?.trim()) return;
    try {
      if (kind === "vaccination") {
        const response = await clinicalApi.voidVaccination(id, { reason });
        onRecordsChange(vaccinations.map((item) => item.id === id ? response.data : item), medications);
      } else {
        const response = await clinicalApi.voidMedication(id, { reason });
        onRecordsChange(vaccinations, medications.map((item) => item.id === id ? response.data : item));
      }
    } catch {
      window.alert(t("clinical.errors.void"));
    }
  }

  async function updateMedicationStatus(record: Medication, status: "completed" | "cancelled") {
    try {
      const response = await clinicalApi.updateMedication(record.id, { status });
      onRecordsChange(vaccinations, medications.map((item) => item.id === record.id ? response.data : item));
    } catch {
      window.alert(t("clinical.errors.save"));
    }
  }

  const vetsById = useMemo(() => new Map(vets.map((vet) => [vet.id, vet.name])), [vets]);

  const events = useMemo<TimelineEvent[]>(() => [
    ...appointments.map((item) => ({
      id: `appointment-${item.id}`,
      date: item.scheduled_at,
      icon: CalendarDays,
      title: item.reason || t("clinical.timeline.appointment"),
      detail: item.notes || t(`status.${item.status}`),
      status: item.status,
      vetName: vetsById.get(item.vet_id),
    })),
    ...treatments.map((item) => ({
      id: `treatment-${item.id}`,
      date: item.created_at,
      icon: ClipboardList,
      title: item.diagnosis || t("clinical.timeline.treatment"),
      detail: item.prescription || item.notes || "",
      status: "completed",
    })),
    ...vaccinations.map((item) => ({
      id: `vaccination-${item.id}`,
      date: item.administered_at,
      icon: Syringe,
      title: `${t("clinical.vaccinations.item")}: ${item.name}`,
      detail: item.dose,
      status: item.status,
      vetName: item.vet_name,
    })),
    ...medications.map((item) => ({
      id: `medication-${item.id}`,
      date: item.start_date,
      icon: Pill,
      title: `${t("clinical.medications.item")}: ${item.name}`,
      detail: [item.dosage, item.frequency, item.route].filter(Boolean).join(" · "),
      status: item.status,
      vetName: item.vet_name,
    })),
  ].sort((a, b) => parseApiDate(b.date).getTime() - parseApiDate(a.date).getTime()), [appointments, treatments, vaccinations, medications, t, vetsById]);

  const timeline = useMemo<TimelineYear[]>(() => {
    const years = new Map<string, TimelineYear>();
    events.forEach((event) => {
      const date = parseApiDate(event.date);
      if (Number.isNaN(date.getTime())) return;
      const [yearValue, monthValue, dayValue] = clinicDateInput(date).split("-");
      const yearId = `year-${yearValue}`;
      const monthId = `${yearId}-month-${monthValue}`;
      const dayId = `${monthId}-day-${dayValue}`;
      let year = years.get(yearId);
      if (!year) {
        year = { id: yearId, label: yearValue, months: [] };
        years.set(yearId, year);
      }
      let month = year.months.find((item) => item.id === monthId);
      if (!month) {
        month = { id: monthId, label: date.toLocaleDateString("pt-AO", { month: "long", timeZone: "Africa/Luanda" }), days: [] };
        year.months.push(month);
      }
      let day = month.days.find((item) => item.id === dayId);
      if (!day) {
        day = { id: dayId, label: date.toLocaleDateString("pt-AO", { weekday: "long", day: "2-digit", timeZone: "Africa/Luanda" }), events: [] };
        month.days.push(day);
      }
      day.events.push(event);
    });
    return [...years.values()];
  }, [events]);

  function toggleGroup(id: string) {
    setCollapsedGroups((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function renderVaccineForm() {
    return (
      <form onSubmit={submitVaccination} className="border-t border-dark-100 p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={t("clinical.vaccinations.form.name")} required>
            <Input required value={vaccineForm.name} onChange={(e) => setVaccineForm({ ...vaccineForm, name: e.target.value })} />
          </Field>
          <Field label={t("clinical.vaccinations.form.dose")} required>
            <Input required value={vaccineForm.dose} onChange={(e) => setVaccineForm({ ...vaccineForm, dose: e.target.value })} />
          </Field>
          <Field label={t("clinical.vaccinations.form.date")} required>
            <Input required type="datetime-local" value={vaccineForm.administered_at} onChange={(e) => setVaccineForm({ ...vaccineForm, administered_at: e.target.value })} />
          </Field>
          <Field label={t("clinical.form.vet")} required>
            <SelectVet t={t} value={vaccineForm.vet_id} vets={vets} onChange={(value) => setVaccineForm({ ...vaccineForm, vet_id: value })} />
          </Field>
          <Field label={t("clinical.vaccinations.form.lot")}>
            <Input value={vaccineForm.lot_number || ""} onChange={(e) => setVaccineForm({ ...vaccineForm, lot_number: e.target.value })} />
          </Field>
          <Field label={t("clinical.vaccinations.form.expiry")}>
            <Input type="date" value={vaccineForm.expires_at || ""} onChange={(e) => setVaccineForm({ ...vaccineForm, expires_at: e.target.value || undefined })} />
          </Field>
          <Field label={t("clinical.vaccinations.form.nextDose")}>
            <Input type="date" value={vaccineForm.next_due_at || ""} onChange={(e) => setVaccineForm({ ...vaccineForm, next_due_at: e.target.value || undefined })} />
          </Field>
          <Field label={t("clinical.form.appointment")}>
            <SelectAppointment t={t} value={vaccineForm.appointment_id} appointments={appointmentOptions} onChange={(value) => setVaccineForm({ ...vaccineForm, appointment_id: value })} />
          </Field>
        </div>
        <Field label={t("clinical.form.notes")}>
          <Input value={vaccineForm.notes || ""} onChange={(e) => setVaccineForm({ ...vaccineForm, notes: e.target.value })} />
        </Field>
        <FormActions t={t} onCancel={closeForm} saving={saving} />
      </form>
    );
  }

  function renderMedicationForm() {
    return (
      <form onSubmit={submitMedication} className="border-t border-dark-100 p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={t("clinical.medications.form.name")} required>
            <Input required value={medicationForm.name} onChange={(e) => setMedicationForm({ ...medicationForm, name: e.target.value })} />
          </Field>
          <Field label={t("clinical.medications.form.dosage")} required>
            <Input required value={medicationForm.dosage} onChange={(e) => setMedicationForm({ ...medicationForm, dosage: e.target.value })} />
          </Field>
          <Field label={t("clinical.medications.form.frequency")} required>
            <Input required value={medicationForm.frequency} onChange={(e) => setMedicationForm({ ...medicationForm, frequency: e.target.value })} />
          </Field>
          <Field label={t("clinical.medications.form.route")} required>
            <Input required value={medicationForm.route} onChange={(e) => setMedicationForm({ ...medicationForm, route: e.target.value })} />
          </Field>
          <Field label={t("clinical.medications.form.start")} required>
            <Input required type="date" value={medicationForm.start_date} onChange={(e) => setMedicationForm({ ...medicationForm, start_date: e.target.value })} />
          </Field>
          <Field label={t("clinical.medications.form.end")}>
            <Input type="date" value={medicationForm.end_date || ""} onChange={(e) => setMedicationForm({ ...medicationForm, end_date: e.target.value || undefined })} />
          </Field>
          <Field label={t("clinical.form.vet")} required>
            <SelectVet t={t} value={medicationForm.vet_id} vets={vets} onChange={(value) => setMedicationForm({ ...medicationForm, vet_id: value })} />
          </Field>
          <Field label={t("clinical.form.appointment")}>
            <SelectAppointment t={t} value={medicationForm.appointment_id} appointments={appointmentOptions} onChange={(value) => setMedicationForm({ ...medicationForm, appointment_id: value })} />
          </Field>
        </div>
        <Field label={t("clinical.medications.form.instructions")}>
          <Input value={medicationForm.instructions || ""} onChange={(e) => setMedicationForm({ ...medicationForm, instructions: e.target.value })} />
        </Field>
        <Field label={t("clinical.form.notes")}>
          <Input value={medicationForm.notes || ""} onChange={(e) => setMedicationForm({ ...medicationForm, notes: e.target.value })} />
        </Field>
        <FormActions t={t} onCancel={closeForm} saving={saving} />
      </form>
    );
  }

  return (
    <div className="space-y-4">
      {activeTab === "timeline" && (
        <Card>
          <CardHeader><CardTitle>{t("clinical.timeline.title")}</CardTitle></CardHeader>
          <CardContent>
            {events.length === 0 ? <EmptyState icon={FileText} text={t("clinical.timeline.empty")} /> : (
              <div className="space-y-4">
                {timeline.map((year) => <TimelineGroup key={year.id} group={year} collapsedGroups={collapsedGroups} onToggle={toggleGroup} t={t} />)}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === "vaccinations" && (
        <RecordCard title={t("clinical.vaccinations.title")} count={vaccinations.filter((item) => item.status !== "voided").length} action={canWrite ? <Button onClick={() => startVaccination()}><Plus />{t("clinical.vaccinations.new")}</Button> : undefined}>
          {recordKind === "vaccination" && renderVaccineForm()}
          {vaccinations.length === 0 ? <EmptyState icon={Syringe} text={t("clinical.vaccinations.empty")} /> : <RecordTable>
            {vaccinations.map((item) => <RecordRow key={item.id} icon={Syringe} title={item.name} date={item.administered_at} detail={[item.dose, item.lot_number].filter(Boolean).join(" · ")} status={item.status} statusLabel={t(`clinical.status.${item.status}`)} actions={canWrite && item.status !== "voided" ? <><Button size="sm" variant="ghost" onClick={() => startVaccination(item)}><Edit3 />{t("common.edit")}</Button><Button size="sm" variant="ghost" onClick={() => voidRecord("vaccination", item.id)}><X />{t("clinical.actions.void")}</Button></> : undefined} />)}
          </RecordTable>}
        </RecordCard>
      )}

      {activeTab === "medications" && (
        <RecordCard title={t("clinical.medications.title")} count={medications.filter((item) => item.status !== "voided").length} action={canWrite ? <Button onClick={() => startMedication()}><Plus />{t("clinical.medications.new")}</Button> : undefined}>
          {recordKind === "medication" && renderMedicationForm()}
          {medications.length === 0 ? <EmptyState icon={Pill} text={t("clinical.medications.empty")} /> : <RecordTable>
            {medications.map((item) => <RecordRow key={item.id} icon={Pill} title={item.name} date={item.start_date} detail={[item.dosage, item.frequency, item.route].filter(Boolean).join(" · ")} status={item.status} statusLabel={t(`clinical.status.${item.status}`)} actions={canWrite && item.status !== "voided" ? <><Button size="sm" variant="ghost" onClick={() => startMedication(item)}><Edit3 />{t("common.edit")}</Button>{item.status === "active" && <><Button size="sm" variant="ghost" onClick={() => updateMedicationStatus(item, "completed")}><Check />{t("clinical.actions.complete")}</Button><Button size="sm" variant="ghost" onClick={() => updateMedicationStatus(item, "cancelled")}><X />{t("clinical.actions.cancel")}</Button></>}<Button size="sm" variant="ghost" onClick={() => voidRecord("medication", item.id)}><X />{t("clinical.actions.void")}</Button></> : undefined} />)}
          </RecordTable>}
        </RecordCard>
      )}
    </div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return <label className="space-y-1.5 block"><span className="text-xs font-semibold text-dark-600">{label}{required && " *"}</span>{children}</label>;
}

function TimelineToggle({ id, label, open, className, onToggle }: { id: string; label: string; open: boolean; className: string; onToggle: (id: string) => void }) {
  const Icon = open ? ChevronDown : ChevronRight;
  return <button type="button" onClick={() => onToggle(id)} aria-expanded={open} className={cn("flex w-full items-center gap-1.5 text-left", className)}><Icon className="w-4 h-4 shrink-0" />{label}</button>;
}

function TimelineGroup({ group, collapsedGroups, onToggle, t }: { group: TimelineYear; collapsedGroups: Set<string>; onToggle: (id: string) => void; t: TFunction }) {
  const yearOpen = !collapsedGroups.has(group.id);
  return <section>
    <TimelineToggle id={group.id} label={group.label} open={yearOpen} onToggle={onToggle} className="text-sm font-bold text-dark-900" />
    {yearOpen && <div className="ml-2 mt-3 space-y-4 border-l border-dark-200 pl-4">
      {group.months.map((month) => {
        const monthOpen = !collapsedGroups.has(month.id);
        return <section key={month.id}>
          <TimelineToggle id={month.id} label={month.label} open={monthOpen} onToggle={onToggle} className="text-sm font-semibold capitalize text-dark-700" />
          {monthOpen && <div className="ml-2 mt-3 space-y-4 border-l border-dark-100 pl-4">
            {month.days.map((day) => {
              const dayOpen = !collapsedGroups.has(day.id);
              return <section key={day.id}>
                <TimelineToggle id={day.id} label={day.label} open={dayOpen} onToggle={onToggle} className="text-xs font-semibold capitalize text-dark-500" />
                {dayOpen && <div className="relative ml-3 mt-3 space-y-5 border-l border-dark-200 pl-6">
                  {day.events.map((event) => {
                    const Icon = event.icon;
                    return <div key={event.id} className="relative">
                      <div className="absolute -left-[2.1rem] top-0.5 flex w-7 h-7 items-center justify-center rounded-full bg-brand-50 text-brand-700 ring-4 ring-white"><Icon className="w-3.5 h-3.5" /></div>
                      <div className="flex items-start justify-between gap-3">
                        <div><p className="font-semibold text-sm text-dark-900">{event.title}</p>{event.detail && <p className="mt-1 text-sm text-dark-500">{event.detail}</p>}{event.vetName && <p className="mt-1 text-xs text-dark-400">{t("clinical.timeline.vet", { name: event.vetName })}</p>}</div>
                        <div className="text-right shrink-0"><p className="text-xs text-dark-400">{timeLabel(event.date)}</p><span className={cn("inline-flex mt-1 px-2 py-0.5 rounded-full text-[10px] font-semibold", statusClass(event.status))}>{t(`status.${event.status}`, { defaultValue: event.status })}</span></div>
                      </div>
                    </div>;
                  })}
                </div>}
              </section>;
            })}
          </div>}
        </section>;
      })}
    </div>}
  </section>;
}

function SelectVet({ t, value, vets, onChange }: { t: TFunction; value: number; vets: { id: number; name: string }[]; onChange: (value: number) => void }) {
  return <FormSelect required value={value || null} onValueChange={(nextValue) => onChange(Number(nextValue))} options={vets.map((vet) => ({ value: vet.id, label: vet.name }))} placeholder={t("clinical.form.selectVet")} className="h-8 rounded-lg bg-transparent px-2.5" />;
}

function SelectAppointment({ t, value, appointments, onChange }: { t: TFunction; value?: number; appointments: Appointment[]; onChange: (value?: number) => void }) {
  return <FormSelect value={value || ""} onValueChange={(nextValue) => onChange(nextValue ? Number(nextValue) : undefined)} options={[{ value: "", label: t("clinical.form.noAppointment") }, ...appointments.map((item) => ({ value: item.id, label: `${dateLabel(item.scheduled_at)} — ${item.reason || t("clinical.timeline.appointment")}` }))]} className="h-8 rounded-lg bg-transparent px-2.5" />;
}

function FormActions({ t, onCancel, saving }: { t: TFunction; onCancel: () => void; saving: boolean }) {
  return <div className="flex justify-end gap-2"><Button type="button" variant="ghost" onClick={onCancel}>{t("common.cancel")}</Button><Button type="submit" disabled={saving}>{saving ? t("common.saving") : t("common.save")}</Button></div>;
}

function EmptyState({ icon: Icon, text }: { icon: typeof FileText; text: string }) {
  return <div className="flex flex-col items-center py-12 text-dark-400"><Icon className="w-9 h-9 mb-3 opacity-30" /><p className="text-sm font-medium">{text}</p></div>;
}

function RecordCard({ title, count, action, children }: { title: string; count: number; action?: React.ReactNode; children: React.ReactNode }) {
  return <Card><CardHeader className="flex-row items-center justify-between border-b border-dark-100"><CardTitle>{title} <Badge variant="outline" className="ml-2">{count}</Badge></CardTitle>{action}</CardHeader>{children}</Card>;
}

function RecordTable({ children }: { children: React.ReactNode }) {
  return <div className="divide-y divide-dark-100">{children}</div>;
}

function RecordRow({ icon: Icon, title, date, detail, status, statusLabel, actions }: { icon: typeof Pill; title: string; date: string; detail: string; status: string; statusLabel: string; actions?: React.ReactNode }) {
  return <div className="clinical-record-row flex items-start gap-3 p-4"><div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center shrink-0"><Icon className="w-4 h-4" /></div><div className="flex-1 min-w-0"><div className="flex items-center gap-2 flex-wrap"><p className="font-semibold text-sm text-dark-900">{title}</p><span className={cn("px-2 py-0.5 rounded-full text-[10px] font-semibold", statusClass(status))}>{statusLabel}</span></div><p className="text-sm text-dark-500 mt-1">{detail || "—"}</p><p className="text-xs text-dark-400 mt-1">{dateLabel(date)}</p></div>{actions && <div className="flex gap-1 flex-wrap justify-end">{actions}</div>}</div>;
}
