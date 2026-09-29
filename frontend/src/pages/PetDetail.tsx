import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import { petsApi, Pet, PetHistoryAppointment } from "@/api/pets";
import { ownersApi, Owner } from "@/api/owners";
import { Appointment } from "@/api/appointments";
import { Treatment } from "@/api/treatments";
import { Medication, Vaccination } from "@/api/clinical";
import { invoicesApi, Invoice } from "@/api/invoices";
import { useAuth } from "@/contexts/AuthContext";
import ClinicalHistory from "@/features/pets/ClinicalHistory";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { parseApiDate } from "@/lib/date";
import {
  ArrowLeft,
  PawPrint,
  Scale,
  CalendarDays,
  Pill,
  Syringe,
  FileText,
  Phone,
  Mail,
  MapPin,
  User,
  Stethoscope,
  TrendingUp,
  AlertCircle,
  ClipboardCheck,
  Minus,
} from "lucide-react";

function calculateAge(birthDate: string | null, t: (key: string, options?: Record<string, unknown>) => string): string {
  if (!birthDate) return "—";
  const birth = new Date(birthDate);
  const today = new Date();
  const totalMonths = (today.getFullYear() - birth.getFullYear()) * 12 + (today.getMonth() - birth.getMonth());
  if (totalMonths < 1) return t("pets.age.lessThanMonth");
  if (totalMonths < 12) return t("pets.age.months", { count: totalMonths });
  const years = Math.floor(totalMonths / 12);
  return t("pets.age.years", { count: years });
}

function statusConfig(status: string) {
  if (status === "in-progress")
    return { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" };
  if (status === "completed")
    return { bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" };
  if (status === "cancelled")
    return { bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
  if (status === "no-show")
    return { bg: "bg-dark-100", text: "text-dark-600", dot: "bg-dark-400" };
  return { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
}

function invStatusConfig(status: string) {
  if (status === "sent")
    return { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" };
  if (status === "paid")
    return { bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" };
  if (status === "cancelled")
    return { bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
  return { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
}

type Tab = "timeline" | "vaccinations" | "medications" | "appointments" | "weight" | "diagnostics" | "treatments" | "invoices";

// ─── SVG Weight Chart ───────────────────────────────────────────────────────────
function WeightChart({ appointments }: { appointments: Appointment[] }) {
  const { t } = useTranslation();
  const withWeight = appointments
    .filter((a) => a.weight != null)
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime());

  if (withWeight.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-dark-400">
        <Scale className="w-10 h-10 mb-3 opacity-30" />
        <p className="text-sm font-medium">{t("pets.detail.weight.noData")}</p>
        <p className="text-dark-400 text-xs mt-1">{t("pets.detail.weight.noDataHint")}</p>
      </div>
    );
  }

  const weights = withWeight.map((a) => a.weight!);
  const minW = Math.min(...weights);
  const maxW = Math.max(...weights);
  const range = maxW - minW || 1;
  const padded = range * 0.3;
  const yMin = minW - padded;
  const yMax = maxW + padded;

  const W = 600, H = 220, PAD = 40;
  const chartW = W - PAD * 2, chartH = H - PAD * 2;

  function x(i: number) {
    return PAD + (withWeight.length === 1 ? chartW / 2 : (i / (withWeight.length - 1)) * chartW);
  }
  function y(w: number) {
    return PAD + chartH - ((w - yMin) / (yMax - yMin)) * chartH;
  }

  const polylinePoints = withWeight
    .map((a, i) => `${x(i).toFixed(1)},${y(a.weight!).toFixed(1)}`)
    .join(" ");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-6 px-2">
        {withWeight.map((a, i) => (
          <div key={a.id} className="flex flex-col items-center gap-0.5">
            <span className="text-brand-700 font-bold text-sm">{a.weight!.toFixed(1)} kg</span>
            <span className="text-dark-400 text-[10px]">
              {parseApiDate(a.scheduled_at).toLocaleDateString("pt-AO", { day: "2-digit", month: "short", timeZone: "Africa/Luanda" })}
            </span>
          </div>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 260 }}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const yVal = yMin + t * (yMax - yMin);
          const yPos = (PAD + chartH - t * chartH).toFixed(1);
          return (
            <g key={t}>
              <line x1={PAD} y1={yPos} x2={PAD + chartW} y2={yPos}
                stroke="#e5e7eb" strokeWidth="1" />
              <text x={PAD - 6} y={(parseFloat(yPos) + 4).toFixed(1)}
                textAnchor="end" fontSize="10" fill="#9ca3af">
                {yVal.toFixed(1)}
              </text>
            </g>
          );
        })}
        {/* Line */}
        <polyline points={polylinePoints}
          fill="none" stroke="rgb(var(--brand-rgb) / 0.8)" strokeWidth="2.5"
          strokeLinejoin="round" strokeLinecap="round" />
        {/* Dots + weight labels */}
        {withWeight.map((a, i) => (
          <g key={a.id}>
            <circle cx={x(i)} cy={y(a.weight!)} r="5"
              fill="rgb(var(--brand-rgb))" stroke="white" strokeWidth="2" />
          </g>
        ))}
      </svg>
      <div className="flex items-center gap-6 px-2">
        <div className="flex items-center gap-2 text-xs text-dark-400">
          <span className="font-semibold text-brand-700">{weights[weights.length - 1].toFixed(1)} kg</span>
          <span>{t("pets.detail.weight.lastWeight")}</span>
        </div>
        {weights.length > 1 && (
          <div className="flex items-center gap-2 text-xs text-dark-400">
            {weights[weights.length - 1] > weights[0]
              ? <TrendingUp className="w-3.5 h-3.5 text-red-500" />
              : <TrendingUp className="w-3.5 h-3.5 text-brand-600 rotate-180" />}
            <span className="font-semibold">
              {Math.abs(weights[weights.length - 1] - weights[0]).toFixed(1)} kg
            </span>
            <span>{t("pets.detail.weight.totalVariation")}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function PetDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useTranslation();
  const petId = Number(id);

  const [pet, setPet] = useState<Pet | null>(null);
  const [owner, setOwner] = useState<Owner | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [vaccinations, setVaccinations] = useState<Vaccination[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("timeline");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!petId) return;
    Promise.all([
      petsApi.get(petId),
      ownersApi.list(true),
      petsApi.history(petId),
      invoicesApi.list(),
    ])
      .then(([petRes, ownersRes, historyRes, invRes]) => {
        setPet(petRes.data);
        const o = ownersRes.data.find((x: Owner) => x.id === petRes.data.owner_id);
        setOwner(o ?? null);
        const petAppts = historyRes.data.appointments.map((a: PetHistoryAppointment) => ({
          id: a.id,
          clinic_id: petRes.data.clinic_id,
          pet_id: petId,
          vet_id: a.vet_id,
          owner_id: petRes.data.owner_id,
          scheduled_at: a.scheduled_at,
          duration_min: 30,
          status: a.status,
          status_reason: a.status_reason,
          reason: a.reason,
          notes: a.notes,
          weight: a.weight,
          service_type_id: a.service_type_id,
          created_at: a.scheduled_at,
        }));
        setAppointments(petAppts);
        const petTreats = historyRes.data.appointments
          .filter((a: PetHistoryAppointment) => a.treatment)
          .map((a: PetHistoryAppointment) => ({ ...a.treatment!, appointment_id: a.id, clinic_id: petRes.data.clinic_id }));
        setTreatments(petTreats);
        setVaccinations(historyRes.data.vaccinations ?? []);
        setMedications(historyRes.data.medications ?? []);
        const petInvs = invRes.data.filter((i: Invoice) => i.owner_id === petRes.data.owner_id);
        setInvoices(petInvs);
      })
      .finally(() => setLoading(false));
  }, [petId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3 text-dark-400">
          <div className="w-8 h-8 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
          <p className="text-sm">{t("common.loading")}</p>
        </div>
      </div>
    );
  }

  if (!pet) {
    return (
      <div className="text-center py-16 text-dark-400">
        <p>{t("pets.detail.notFound")}</p>
        <button onClick={() => navigate("/pets")} className="mt-2 text-brand-600 hover:text-brand-700 text-sm font-semibold">
          {t("pets.detail.backToList")}
        </button>
      </div>
    );
  }

  const age = calculateAge(pet.birth_date, t);
  const speciesEmoji =
    pet.species === "Cão" ? "🐶"
    : pet.species === "Gato" ? "🐱"
    : pet.species === "Ave" ? "🐦"
    : "🐾";

  const appointmentsWithWeight = appointments.filter((a) => a.weight != null);
  const latestWeight = appointmentsWithWeight[appointmentsWithWeight.length - 1]?.weight ?? pet.weight;

  const petTreatments = treatments;

  const TABS: { key: Tab; label: string; icon: React.ReactNode; count: number }[] = [
    { key: "timeline", label: t("clinical.timeline.title"), icon: <FileText className="w-4 h-4" />, count: appointments.length + petTreatments.length + vaccinations.length + medications.length },
    { key: "vaccinations", label: t("clinical.vaccinations.title"), icon: <Syringe className="w-4 h-4" />, count: vaccinations.filter((item) => item.status !== "voided").length },
    { key: "medications", label: t("clinical.medications.title"), icon: <Pill className="w-4 h-4" />, count: medications.filter((item) => item.status !== "voided").length },
    { key: "appointments", label: t("pets.detail.tabs.appointments"), icon: <CalendarDays className="w-4 h-4" />, count: appointments.length },
    { key: "weight", label: t("pets.detail.tabs.weight"), icon: <Scale className="w-4 h-4" />, count: appointmentsWithWeight.length },
    { key: "diagnostics", label: t("pets.detail.tabs.diagnostics"), icon: <Stethoscope className="w-4 h-4" />, count: petTreatments.length },
    { key: "treatments", label: t("pets.detail.tabs.treatments"), icon: <Pill className="w-4 h-4" />, count: petTreatments.length },
    { key: "invoices", label: t("pets.detail.tabs.invoices"), icon: <FileText className="w-4 h-4" />, count: invoices.length },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <button
          onClick={() => navigate("/pets")}
          className="flex items-center gap-2 text-dark-400 hover:text-dark-900 transition-colors text-sm font-medium mt-1"
        >
          <ArrowLeft className="w-4 h-4" />
          {t("common.back")}
        </button>
      </div>

      {/* Pet identity card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardContent className="p-6">
            <div className="flex flex-col items-start gap-4 sm:flex-row sm:gap-5">
              <div className="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center text-3xl flex-shrink-0">
                {speciesEmoji}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-2xl font-extrabold text-dark-900">{pet.name}</h2>
                  <Badge variant="outline" className="text-xs font-medium">{pet.species}</Badge>
                  {pet.breed && <Badge variant="outline" className="text-xs">{pet.breed}</Badge>}
                  {pet.archived_at && <Badge variant="destructive" className="text-xs">{t("common.archived")}</Badge>}
                </div>
                <div className="flex flex-wrap gap-4 mt-3">
                  {pet.birth_date && (
                    <span className="flex items-center gap-1.5 text-sm text-dark-500">
                      <CalendarDays className="w-3.5 h-3.5" />
                      {age} · {t("pets.form.birthDateFormatted", { date: new Date(pet.birth_date).toLocaleDateString("pt-AO") })}
                    </span>
                  )}
                  {latestWeight && (
                    <span className="flex items-center gap-1.5 text-sm text-dark-500">
                      <Scale className="w-3.5 h-3.5" />
                      {latestWeight} kg
                    </span>
                  )}
                </div>
                {pet.notes && (
                  <p className="text-sm text-dark-400 mt-2 italic">{pet.notes}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Owner card */}
        {owner && (
          <Card className="bg-dark-950 border-dark-800">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <User className="w-4 h-4 text-dark-500" />
                <p className="text-dark-500 text-xs font-semibold uppercase tracking-widest">{t("pets.form.owner")}</p>
              </div>
              <h3 className="text-dark-100 font-bold text-base">{owner.name}</h3>
              {owner.phone && (
                <a href={`tel:${owner.phone}`} className="flex items-center gap-1.5 text-dark-400 text-sm mt-2 hover:text-brand-600 transition-colors">
                  <Phone className="w-3.5 h-3.5" />
                  {owner.phone}
                </a>
              )}
              {owner.email && (
                <a href={`mailto:${owner.email}`} className="flex items-center gap-1.5 text-dark-400 text-sm mt-1 hover:text-brand-600 transition-colors">
                  <Mail className="w-3.5 h-3.5" />
                  {owner.email}
                </a>
              )}
              {owner.address && (
                <div className="flex items-start gap-1.5 text-dark-400 text-sm mt-1">
                  <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                  {owner.address}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-dark-200">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map(({ key, label, icon, count }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all -mb-px whitespace-nowrap",
                activeTab === key
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-dark-400 hover:text-dark-700 hover:border-dark-200"
              )}
            >
              {icon}
              {label}
              <span className={cn(
                "text-[10px] font-bold px-1.5 py-0.5 rounded-full",
                activeTab === key ? "bg-brand-100 text-brand-700" : "bg-dark-100 text-dark-500"
              )}>
                {count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Appointments tab ── */}
      {(activeTab === "timeline" || activeTab === "vaccinations" || activeTab === "medications") && (
        <ClinicalHistory
          petId={petId}
          activeTab={activeTab}
          appointments={appointments}
          treatments={petTreatments}
          vaccinations={vaccinations}
          medications={medications}
          currentUser={user}
          onRecordsChange={(nextVaccinations, nextMedications) => {
            setVaccinations(nextVaccinations);
            setMedications(nextMedications);
          }}
        />
      )}

      {/* ── Appointments tab ── */}
      {activeTab === "appointments" && (
        <Card>
          <CardContent className="p-0">
            {appointments.length === 0 ? (
              <div className="flex flex-col items-center py-16 text-dark-400">
                <CalendarDays className="w-10 h-10 mb-3 opacity-30" />
                <p className="text-sm font-medium">{t("pets.detail.appointments.noData")}</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-b border-dark-100">
                    <TableHead className="pl-5">{t("invoices.table.date")}</TableHead>
                    <TableHead>{t("appointments.table.reason")}</TableHead>
                    <TableHead>{t("appointments.form.weight")}</TableHead>
                    <TableHead>{t("appointments.form.notes")}</TableHead>
                    <TableHead>{t("appointments.table.status")}</TableHead>
                    <TableHead className="pr-5 text-right">{t("pets.detail.appointments.encounter")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {appointments.map((a) => {
                    const cfg = statusConfig(a.status);
                    return (
                      <TableRow key={a.id}>
                        <TableCell className="pl-5">
                          <div className="font-semibold text-sm text-dark-900">
                            {parseApiDate(a.scheduled_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" })}
                          </div>
                          <div className="text-dark-400 text-xs">
                            {parseApiDate(a.scheduled_at).toLocaleTimeString("pt-AO", { hour: "2-digit", minute: "2-digit", timeZone: "Africa/Luanda" })}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="font-medium text-sm text-dark-700">{a.reason ?? t("dashboard.defaultReason")}</span>
                        </TableCell>
                        <TableCell>
                          {a.weight ? (
                            <span className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700">
                              <Scale className="w-3.5 h-3.5" />
                              {a.weight} kg
                            </span>
                          ) : (
                            <span className="text-dark-300 text-sm flex items-center gap-1">
                              <Minus className="w-3 h-3" />
                              —
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-dark-500">{a.notes ?? "—"}</span>
                        </TableCell>
                        <TableCell>
                          <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold", cfg.bg, cfg.text)}>
                            <span className={cn("w-1.5 h-1.5 rounded-full", cfg.dot)} />
                            {t(`appointments.status.${a.status}`)}
                          </span>
                        </TableCell>
                        <TableCell className="pr-5 text-right">
                          <button onClick={() => navigate(`/appointments/${a.id}/clinical`)} className="inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-semibold text-primary hover:bg-primary/5">
                            <ClipboardCheck className="size-3.5" />
                            {t("clinicalAppointment.openEncounter")}
                          </button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Weight History tab ── */}
      {activeTab === "weight" && (
        <Card>
          <CardContent className="p-6">
            <div className="mb-4">
              <h3 className="text-base font-bold text-dark-900">{t("pets.detail.weight.history")}</h3>
              <p className="text-dark-400 text-xs mt-0.5">{t("pets.detail.weight.subtitle")}</p>
            </div>
            <WeightChart appointments={appointments} />
          </CardContent>
        </Card>
      )}

      {/* ── Diagnostics tab ── */}
      {activeTab === "diagnostics" && (
        <Card>
          <CardContent className="p-0">
            {petTreatments.length === 0 ? (
              <div className="flex flex-col items-center py-16 text-dark-400">
                <Stethoscope className="w-10 h-10 mb-3 opacity-30" />
                <p className="text-sm font-medium">{t("pets.detail.diagnostics.noData")}</p>
                <p className="text-dark-400 text-xs mt-1">{t("pets.detail.diagnostics.noDataHint")}</p>
              </div>
            ) : (
              <div className="divide-y divide-dark-100">
                {petTreatments.map((treatment) => {
                  const appt = appointments.find((a) => a.id === treatment.appointment_id);
                  return (
                    <div key={treatment.id} className="p-5">
                      <div className="flex items-start gap-4">
                        <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <AlertCircle className="w-4 h-4 text-amber-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 flex-wrap mb-1">
                            <h4 className="font-bold text-dark-900 text-sm">
                              {treatment.diagnosis ?? t("pets.detail.diagnostics.unspecified")}
                            </h4>
                            {appt && (
                              <span className="text-dark-400 text-xs">
                                {parseApiDate(appt.scheduled_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" })}
                              </span>
                            )}
                          </div>
                          {treatment.notes && (
                            <p className="text-dark-500 text-sm mt-1">{treatment.notes}</p>
                          )}
                          {treatment.prescription && (
                            <div className="mt-2 bg-brand-50 border border-brand-200 rounded-lg px-3 py-2">
                              <p className="text-brand-700 text-xs font-semibold mb-0.5">{t("pets.detail.diagnostics.prescription")}:</p>
                              <p className="text-brand-600 text-xs">{treatment.prescription}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Treatments tab ── */}
      {activeTab === "treatments" && (
        <Card>
          <CardContent className="p-0">
            {petTreatments.length === 0 ? (
              <div className="flex flex-col items-center py-16 text-dark-400">
                <Pill className="w-10 h-10 mb-3 opacity-30" />
                <p className="text-sm font-medium">{t("pets.detail.treatments.noData")}</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-b border-dark-100">
                    <TableHead className="pl-5 w-28">{t("invoices.table.date")}</TableHead>
                    <TableHead>{t("pets.detail.tabs.diagnostics")}</TableHead>
                    <TableHead>{t("pets.detail.diagnostics.prescription")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {petTreatments.map((treatment) => (
                    <TableRow key={treatment.id}>
                      <TableCell className="pl-5 font-medium text-sm text-dark-700">
                        {parseApiDate(treatment.created_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" })}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-dark-600">{treatment.diagnosis ?? "—"}</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-dark-500">{treatment.prescription ?? "—"}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Invoices tab ── */}
      {activeTab === "invoices" && (
        <Card>
          <CardContent className="p-0">
            {invoices.length === 0 ? (
              <div className="flex flex-col items-center py-16 text-dark-400">
                <FileText className="w-10 h-10 mb-3 opacity-30" />
                <p className="text-sm font-medium">{t("pets.detail.invoices.noData")}</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-b border-dark-100">
                    <TableHead className="pl-5 w-16">{t("invoices.table.number")}</TableHead>
                    <TableHead>{t("invoices.table.description")}</TableHead>
                    <TableHead>{t("invoices.table.value")}</TableHead>
                    <TableHead>{t("invoices.table.status")}</TableHead>
                    <TableHead className="pr-5">{t("invoices.table.date")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoices.map((inv) => {
                    const cfg = invStatusConfig(inv.status);
                    return (
                      <TableRow key={inv.id}>
                        <TableCell className="pl-5 font-bold text-sm text-dark-500">#{inv.id}</TableCell>
                        <TableCell>
                          <span className="text-sm text-dark-600">{inv.description ?? "—"}</span>
                        </TableCell>
                        <TableCell>
                          <span className="font-bold text-sm text-dark-900">{inv.amount.toLocaleString("pt-AO")} Kz</span>
                        </TableCell>
                        <TableCell>
                          <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold", cfg.bg, cfg.text)}>
                            <span className={cn("w-1.5 h-1.5 rounded-full", cfg.dot)} />
                            {t(`invoices.status.${inv.status}`)}
                          </span>
                        </TableCell>
                        <TableCell className="pr-5 text-sm text-dark-500">
                          {parseApiDate(inv.created_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" })}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
