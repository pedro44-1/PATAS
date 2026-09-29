import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { treatmentsApi, Treatment, TreatmentCreate } from "@/api/treatments";
import { appointmentsApi, Appointment, AppointmentCreate, VetOption } from "@/api/appointments";
import { petsApi, Pet } from "@/api/pets";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CalendarPlus, Mic, Pencil, Pill, Square, X } from "lucide-react";
import { clinicDateTimeInput, parseApiDate } from "@/lib/date";

type DictationField = "diagnosis" | "prescription";

interface BrowserSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: {
    resultIndex: number;
    results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>;
  }) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
}

type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

function getSpeechRecognition() {
  const browser = window as typeof window & {
    SpeechRecognition?: BrowserSpeechRecognitionConstructor;
    webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
  };
  return browser.SpeechRecognition ?? browser.webkitSpeechRecognition;
}

function appendTranscript(existing: string, transcript: string) {
  const next = transcript.trim();
  if (!next) return existing;
  return existing.trim() ? `${existing.trimEnd()} ${next}` : next;
}

function defaultAppointmentDateTime() {
  const value = new Date(Date.now() + 60 * 60 * 1000);
  value.setUTCMinutes(0, 0, 0);
  return clinicDateTimeInput(value);
}

export default function Treatments() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canWrite = user?.role === "admin" || user?.role === "vet";
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showAppointmentForm, setShowAppointmentForm] = useState(false);
  const [editing, setEditing] = useState<Treatment | null>(null);
  const [form, setForm] = useState<TreatmentCreate>({
    appointment_id: 0,
    diagnosis: "",
    notes: "",
    prescription: "",
  });
  const [saving, setSaving] = useState(false);
  const [pets, setPets] = useState<Pet[]>([]);
  const [vets, setVets] = useState<VetOption[]>([]);
  const [appointmentOptionsLoading, setAppointmentOptionsLoading] = useState(false);
  const [appointmentSaving, setAppointmentSaving] = useState(false);
  const [appointmentForm, setAppointmentForm] = useState<AppointmentCreate>({
    pet_id: 0,
    vet_id: 0,
    scheduled_at: "",
    duration_min: 30,
    reason: "",
    notes: "",
  });
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const [dictationTarget, setDictationTarget] = useState<DictationField | null>(null);
  const [dictationError, setDictationError] = useState<string | null>(null);

  function load() {
    Promise.all([treatmentsApi.list(), appointmentsApi.list()])
      .then(([tRes, aRes]) => {
        setTreatments(tRes.data);
        setAppointments(aRes.data);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => () => recognitionRef.current?.stop(), []);

  function getApptInfo(id: number) {
    const appointment = appointments.find((item) => item.id === id);
    if (!appointment) return "—";
    return `${appointment.notes || appointment.reason || t("treatments.appointmentFallback")} · ${parseApiDate(appointment.scheduled_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" })}`;
  }

  function closeTreatmentForm() {
    recognitionRef.current?.stop();
    setDictationTarget(null);
    setDictationError(null);
    setShowForm(false);
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

  function openEdit(treatment: Treatment) {
    setEditing(treatment);
    setForm({
      appointment_id: treatment.appointment_id,
      diagnosis: treatment.diagnosis ?? "",
      notes: treatment.notes ?? "",
      prescription: treatment.prescription ?? "",
    });
    setShowForm(true);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await treatmentsApi.update(editing.id, form);
      } else {
        await treatmentsApi.create(form);
      }
      closeTreatmentForm();
      load();
    } catch {
    } finally {
      setSaving(false);
    }
  }

  function openAppointmentCreate() {
    setShowAppointmentForm(true);
    setAppointmentOptionsLoading(true);
    Promise.all([petsApi.list(), appointmentsApi.vets()])
      .then(([petsResponse, vetsResponse]) => {
        setPets(petsResponse.data);
        setVets(vetsResponse.data);
        setAppointmentForm({
          pet_id: petsResponse.data[0]?.id ?? 0,
          vet_id: vetsResponse.data[0]?.id ?? 0,
          scheduled_at: defaultAppointmentDateTime(),
          duration_min: 30,
          reason: "",
          notes: "",
        });
      })
      .finally(() => setAppointmentOptionsLoading(false));
  }

  async function handleAppointmentSubmit(event: React.FormEvent) {
    event.preventDefault();
    setAppointmentSaving(true);
    try {
      const response = await appointmentsApi.create(appointmentForm);
      const createdAppointment = response.data;
      setAppointments((current) => [createdAppointment, ...current.filter((item) => item.id !== createdAppointment.id)]);
      setForm((current) => ({ ...current, appointment_id: createdAppointment.id }));
      setShowAppointmentForm(false);
    } catch {
    } finally {
      setAppointmentSaving(false);
    }
  }

  function toggleDictation(field: DictationField) {
    if (dictationTarget) {
      recognitionRef.current?.stop();
      return;
    }

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      setDictationError(t("treatments.voice.unsupported"));
      return;
    }

    setDictationError(null);
    const recognition = new SpeechRecognition();
    const initialValue = form[field] ?? "";
    let finalTranscript = "";
    recognition.lang = "pt-PT";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
      let interimTranscript = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }
      setForm((current) => ({
        ...current,
        [field]: appendTranscript(initialValue, `${finalTranscript} ${interimTranscript}`),
      }));
    };
    recognition.onerror = (event) => {
      if (event.error !== "aborted") setDictationError(t("treatments.voice.error"));
    };
    recognition.onend = () => {
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null;
        setDictationTarget(null);
      }
    };
    recognitionRef.current = recognition;
    setDictationTarget(field);
    recognition.start();
  }

  function renderDictationButton(field: DictationField) {
    const isRecording = dictationTarget === field;
    return (
      <button
        type="button"
        onClick={() => toggleDictation(field)}
        className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold transition-colors ${
          isRecording
            ? "bg-red-50 text-red-700 hover:bg-red-100"
            : "bg-brand-50 text-brand-700 hover:bg-brand-100"
        }`}
        aria-label={t(isRecording ? "treatments.voice.stop" : "treatments.voice.start")}
        title={t(isRecording ? "treatments.voice.stop" : "treatments.voice.start")}
      >
        {isRecording ? <Square className="h-3 w-3 fill-current" /> : <Mic className="h-3.5 w-3.5" />}
        {t(isRecording ? "treatments.voice.recording" : "treatments.voice.start")}
      </button>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">{t("treatments.title")}</h2>
          <p className="mt-0.5 text-sm text-dark-400">
            {t("treatments.count", { count: treatments.length })}
          </p>
        </div>
        {canWrite && (
          <Button
            onClick={openCreate}
            className="rounded-xl bg-brand-600 font-semibold shadow-lg shadow-brand-600/20 hover:bg-brand-700"
          >
            <Pill className="mr-2 h-4 w-4" />
            {t("treatments.new")}
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600/30 border-t-brand-600" />
            </div>
          ) : treatments.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <Pill className="mb-3 h-10 w-10 opacity-30" />
              <p className="text-sm font-medium">{t("treatments.noResults")}</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-b border-dark-100 hover:bg-transparent">
                  <TableHead className="w-28 pl-5">{t("treatments.table.date")}</TableHead>
                  <TableHead>{t("treatments.table.appointment")}</TableHead>
                  <TableHead>{t("treatments.table.diagnosis")}</TableHead>
                  <TableHead>{t("treatments.table.prescription")}</TableHead>
                  <TableHead className="w-28 pr-5 text-right">{t("treatments.table.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {treatments.map((treatment) => (
                  <TableRow key={treatment.id}>
                    <TableCell className="pl-5">
                      <span className="text-sm font-medium text-dark-700">
                        {parseApiDate(treatment.created_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" })}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="block max-w-40 truncate text-sm text-dark-600">
                        {getApptInfo(treatment.appointment_id)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="block max-w-56 truncate text-sm text-dark-600">
                        {treatment.diagnosis ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="block max-w-48 truncate text-sm text-dark-500">
                        {treatment.prescription ?? "—"}
                      </span>
                    </TableCell>
                    <TableCell className="pr-5">
                      <div className="flex justify-end gap-2">
                        {canWrite && (
                          <button
                            onClick={() => openEdit(treatment)}
                            className="rounded-lg bg-blue-50 p-1.5 text-blue-600 transition-colors hover:bg-blue-100"
                            aria-label={t("common.edit")}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                        )}
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
        <div className="fixed inset-0 z-50 bg-black/60 p-4 backdrop-blur-sm" onClick={closeTreatmentForm}>
          <div
            className="absolute left-1/2 top-1/2 max-h-[calc(100dvh-2rem)] w-full max-w-md -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="sticky top-0 flex items-center justify-between rounded-t-2xl border-b border-dark-100 bg-white px-6 py-4">
              <div>
                <h2 className="font-bold text-dark-900">{t(editing ? "treatments.edit" : "treatments.new")}</h2>
                <p className="mt-0.5 text-xs text-dark-400">{t(editing ? "treatments.editHint" : "treatments.createHint")}</p>
              </div>
              <button
                onClick={closeTreatmentForm}
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-dark-100 text-dark-400 transition-colors hover:bg-dark-200 hover:text-dark-700"
                aria-label={t("common.cancel")}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 p-6">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-3">
                  <Label className="text-xs font-semibold text-dark-600">{t("treatments.form.appointment")} *</Label>
                  <button
                    type="button"
                    onClick={openAppointmentCreate}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-800"
                  >
                    <CalendarPlus className="h-3.5 w-3.5" />
                    {t("treatments.createAppointment")}
                  </button>
                </div>
                <FormSelect
                  value={form.appointment_id || null}
                  onValueChange={(value) => setForm({ ...form, appointment_id: Number(value) })}
                  options={appointments.map((appointment) => ({ value: appointment.id, label: getApptInfo(appointment.id) }))}
                  placeholder={t("treatments.form.selectAppointment")}
                  className="h-11 border-dark-200 bg-white"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-3">
                  <Label className="text-xs font-semibold text-dark-600">{t("treatments.form.diagnosis")}</Label>
                  {renderDictationButton("diagnosis")}
                </div>
                <textarea
                  value={form.diagnosis}
                  onChange={(event) => setForm({ ...form, diagnosis: event.target.value })}
                  placeholder={t("treatments.form.diagnosisPlaceholder")}
                  rows={3}
                  className="flex w-full resize-none rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                {dictationTarget === "diagnosis" && <p className="text-xs text-red-600">{t("treatments.voice.listening")}</p>}
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-3">
                  <Label className="text-xs font-semibold text-dark-600">{t("treatments.form.prescription")}</Label>
                  {renderDictationButton("prescription")}
                </div>
                <textarea
                  value={form.prescription}
                  onChange={(event) => setForm({ ...form, prescription: event.target.value })}
                  placeholder={t("treatments.form.prescriptionPlaceholder")}
                  rows={3}
                  className="flex w-full resize-none rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                {dictationTarget === "prescription" && <p className="text-xs text-red-600">{t("treatments.voice.listening")}</p>}
                {dictationError && <p className="text-xs text-red-600">{dictationError}</p>}
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-dark-100 pt-2">
                <Button type="button" variant="outline" onClick={closeTreatmentForm} className="h-11 rounded-xl">
                  {t("common.cancel")}
                </Button>
                <Button type="submit" disabled={saving} className="h-11 rounded-xl bg-brand-600 font-semibold hover:bg-brand-700">
                  {saving ? t("treatments.saving") : t(editing ? "treatments.saveChanges" : "treatments.create")}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAppointmentForm && (
        <div className="fixed inset-0 z-[60] bg-black/60 p-4 backdrop-blur-sm" onClick={() => setShowAppointmentForm(false)}>
          <div
            className="absolute left-1/2 top-1/2 max-h-[calc(100dvh-2rem)] w-full max-w-md -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="sticky top-0 flex items-center justify-between rounded-t-2xl border-b border-dark-100 bg-white px-6 py-4">
              <div>
                <h2 className="font-bold text-dark-900">{t("treatments.newAppointment.title")}</h2>
                <p className="mt-0.5 text-xs text-dark-400">{t("treatments.newAppointment.hint")}</p>
              </div>
              <button
                onClick={() => setShowAppointmentForm(false)}
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-dark-100 text-dark-400 transition-colors hover:bg-dark-200 hover:text-dark-700"
                aria-label={t("common.cancel")}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleAppointmentSubmit} className="space-y-4 p-6">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.animal")} *</Label>
                <FormSelect
                  value={appointmentForm.pet_id || null}
                  onValueChange={(value) => setAppointmentForm({ ...appointmentForm, pet_id: Number(value) })}
                  options={pets.map((pet) => ({ value: pet.id, label: pet.name }))}
                  placeholder={t("appointments.form.selectAnimal")}
                  className="h-11 border-dark-200 bg-white"
                  disabled={appointmentOptionsLoading}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.vet")} *</Label>
                <FormSelect
                  value={appointmentForm.vet_id || null}
                  onValueChange={(value) => setAppointmentForm({ ...appointmentForm, vet_id: Number(value) })}
                  options={vets.map((vet) => ({ value: vet.id, label: vet.name }))}
                  placeholder={t("appointments.form.selectVet")}
                  className="h-11 border-dark-200 bg-white"
                  disabled={appointmentOptionsLoading}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.dateTime")} *</Label>
                <Input
                  type="datetime-local"
                  value={appointmentForm.scheduled_at}
                  onChange={(event) => setAppointmentForm({ ...appointmentForm, scheduled_at: event.target.value })}
                  required
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("appointments.form.reason")}</Label>
                <Input
                  value={appointmentForm.reason}
                  onChange={(event) => setAppointmentForm({ ...appointmentForm, reason: event.target.value })}
                  placeholder={t("appointments.form.reasonPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-dark-100 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAppointmentForm(false)} className="h-11 rounded-xl">
                  {t("common.cancel")}
                </Button>
                <Button
                  type="submit"
                  disabled={appointmentOptionsLoading || appointmentSaving || !appointmentForm.pet_id || !appointmentForm.vet_id}
                  className="h-11 rounded-xl bg-brand-600 font-semibold hover:bg-brand-700"
                >
                  {appointmentSaving ? t("appointments.saving") : t("treatments.newAppointment.create")}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
