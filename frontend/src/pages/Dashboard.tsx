import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
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
import {
  PawPrint,
  Users,
  CalendarDays,
  FileText,
  TrendingUp,
  Clock,
  ChevronRight,
} from "lucide-react";

interface UpcomingAppointment {
  id: number;
  pet_id: number;
  vet_id: number;
  scheduled_at: string;
  reason: string | null;
  status: string;
}

interface DashboardStats {
  today_appointments_total: number;
  today_appointments_by_status: {
    scheduled: number;
    completed: number;
    cancelled: number;
    no_show: number;
  };
  upcoming_appointments: UpcomingAppointment[];
  total_owners: number;
  total_pets: number;
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Bom dia";
  if (h < 18) return "Boa tarde";
  return "Boa noite";
}

function statusConfig(status: string): {
  label: string;
  bg: string;
  text: string;
  dot: string;
} {
  if (status === "completed")
    return {
      label: "Concluída",
      bg: "bg-brand-50",
      text: "text-brand-700",
      dot: "bg-brand-500",
    };
  if (status === "cancelled")
    return {
      label: "Cancelada",
      bg: "bg-red-50",
      text: "text-red-700",
      dot: "bg-red-500",
    };
  if (status === "no-show")
    return {
      label: "Faltou",
      bg: "bg-dark-100",
      text: "text-dark-600",
      dot: "bg-dark-400",
    };
  return {
    label: "Agendada",
    bg: "bg-amber-50",
    text: "text-amber-700",
    dot: "bg-amber-500",
  };
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<DashboardStats>("/dashboard/")
      .then((r) => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3 text-dark-400">
          <div className="w-8 h-8 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
          <p className="text-sm">A carregar...</p>
        </div>
      </div>
    );
  }

  const s = stats;
  const today = new Date();

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Greeting */}
      <div>
        <h2 className="text-2xl font-extrabold text-dark-900">
          {greeting()}, {user?.name?.split(" ")[0]} 👋
        </h2>
        <p className="text-dark-400 text-sm mt-1 capitalize">
          {today.toLocaleDateString("pt-AO", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Animais Registados"
          value={s?.total_pets ?? 0}
          icon={<PawPrint className="w-5 h-5" />}
          iconBg="bg-brand-50"
          iconText="text-brand-600"
          trend="+2 este mês"
          trendUp
        />
        <StatCard
          label="Donos"
          value={s?.total_owners ?? 0}
          icon={<Users className="w-5 h-5" />}
          iconBg="bg-blue-50"
          iconText="text-blue-600"
          trend="+1 este mês"
          trendUp
        />
        <StatCard
          label="Consultas Hoje"
          value={s?.today_appointments_total ?? 0}
          icon={<CalendarDays className="w-5 h-5" />}
          iconBg="bg-violet-50"
          iconText="text-violet-600"
          badge={
            s
              ? [
                  { label: `${s.today_appointments_by_status.scheduled} Agendadas`, variant: "default" as const },
                  { label: `${s.today_appointments_by_status.completed} Concluídas`, variant: "secondary" as const },
                ]
              : undefined
          }
        />
        <StatCard
          label="Próximas Consultas"
          value={s?.upcoming_appointments.length ?? 0}
          icon={<Clock className="w-5 h-5" />}
          iconBg="bg-amber-50"
          iconText="text-amber-600"
          trend="Ver todas"
          trendLink
          onTrendClick={() => navigate("/appointments")}
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Appointments table */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between px-5 py-4 border-b border-dark-100">
              <div>
                <h3 className="font-bold text-dark-900 text-sm">
                  Consultas de Hoje
                </h3>
                <p className="text-dark-400 text-xs mt-0.5">
                  {today.toLocaleDateString("pt-AO")}
                </p>
              </div>
              <button
                onClick={() => navigate("/appointments")}
                className="flex items-center gap-1 text-brand-600 hover:text-brand-700 text-xs font-semibold transition-colors"
              >
                Ver todas
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <CardContent className="p-0">
              {s?.upcoming_appointments.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-dark-400">
                  <CalendarDays className="w-10 h-10 mb-3 opacity-30" />
                  <p className="text-sm font-medium">Nenhuma consulta agendada</p>
                  <button
                    onClick={() => navigate("/appointments")}
                    className="mt-2 text-xs text-brand-600 hover:text-brand-700 font-semibold"
                  >
                    Agendar nova consulta
                  </button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-b border-dark-100">
                      <TableHead className="pl-5 w-24">Hora</TableHead>
                      <TableHead>Motivo</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="pr-5 text-right">Acções</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {s?.upcoming_appointments.slice(0, 6).map((appt) => {
                      const cfg = statusConfig(appt.status);
                      return (
                        <TableRow
                          key={appt.id}
                          className="cursor-pointer"
                          onClick={() => navigate("/appointments")}
                        >
                          <TableCell className="pl-5">
                            <div className="font-bold text-sm text-dark-900">
                              {new Date(appt.scheduled_at).toLocaleTimeString(
                                "pt-AO",
                                { hour: "2-digit", minute: "2-digit" }
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="font-medium text-sm text-dark-700">
                              {appt.reason ?? "Consulta"}
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
                              <span
                                className={cn(
                                  "w-1.5 h-1.5 rounded-full flex-shrink-0",
                                  cfg.dot
                                )}
                              />
                              {cfg.label}
                            </span>
                          </TableCell>
                          <TableCell className="pr-5 text-right">
                            <button className="px-3 py-1 rounded-lg bg-dark-100 hover:bg-dark-200 text-dark-600 text-xs font-medium transition-colors">
                              Ver
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
        </div>

        {/* Quick actions */}
        <div className="space-y-5">
          {/* Quick actions card */}
          <Card>
            <div className="px-5 py-4 border-b border-dark-100">
              <h3 className="font-bold text-dark-900 text-sm">Ações Rápidas</h3>
            </div>
            <CardContent className="p-4 space-y-2">
              {[
                {
                  label: "Nova Consulta",
                  sub: "Agendar consulta",
                  icon: "📅",
                  onClick: () => navigate("/appointments"),
                },
                {
                  label: "Novo Animal",
                  sub: "Registar animal",
                  icon: "🐾",
                  onClick: () => navigate("/pets"),
                },
                {
                  label: "Novo Dono",
                  sub: "Adicionar dono",
                  icon: "👤",
                  onClick: () => navigate("/owners"),
                },
                {
                  label: "Emitir Fatura",
                  sub: "Criar fatura",
                  icon: "📄",
                  onClick: () => navigate("/invoices"),
                },
              ].map(({ label, sub, icon, onClick }) => (
                <button
                  key={label}
                  onClick={onClick}
                  className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-dark-50 transition-colors text-left group"
                >
                  <div className="w-10 h-10 rounded-xl bg-dark-100 flex items-center justify-center text-lg group-hover:bg-brand-50 transition-colors">
                    {icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-sm text-dark-900">
                      {label}
                    </div>
                    <div className="text-dark-400 text-xs">{sub}</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-dark-300 group-hover:text-brand-500 transition-colors" />
                </button>
              ))}
            </CardContent>
          </Card>

          {/* Summary */}
          <Card className="bg-dark-950 border-dark-800">
            <CardContent className="p-5 space-y-4">
              <div>
                <p className="text-dark-500 text-xs font-semibold uppercase tracking-widest mb-1">
                  Resumo do Dia
                </p>
                <p className="text-dark-100 font-bold text-2xl">
                  {s?.today_appointments_total ?? 0} consultas
                </p>
              </div>
              <div className="space-y-2">
                {[
                  { label: "Agendadas", value: s?.today_appointments_by_status.scheduled ?? 0, color: "bg-amber-500" },
                  { label: "Concluídas", value: s?.today_appointments_by_status.completed ?? 0, color: "bg-brand-500" },
                  { label: "Canceladas", value: s?.today_appointments_by_status.cancelled ?? 0, color: "bg-red-500" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex items-center gap-3">
                    <div className={cn("w-2 h-2 rounded-full flex-shrink-0", color)} />
                    <span className="text-dark-400 text-sm flex-1">{label}</span>
                    <span className="text-dark-100 font-semibold text-sm">{value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  iconBg,
  iconText,
  trend,
  trendUp,
  trendLink,
  badge,
  onTrendClick,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  iconBg: string;
  iconText: string;
  trend?: string;
  trendUp?: boolean;
  trendLink?: boolean;
  badge?: { label: string; variant: "default" | "secondary" }[];
  onTrendClick?: () => void;
}) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-dark-400 text-xs font-medium uppercase tracking-wider">
              {label}
            </p>
            <p className="text-3xl font-extrabold text-dark-900 mt-2">
              {value}
            </p>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              {badge ? (
                badge.map(({ label: bLabel, variant }) => (
                  <Badge key={bLabel} variant={variant} className="text-[10px]">
                    {bLabel}
                  </Badge>
                ))
              ) : trend ? (
                <p
                  className={cn(
                    "text-xs font-semibold flex items-center gap-1",
                    trendUp ? "text-brand-600" : "text-dark-400",
                    trendLink && "cursor-pointer hover:underline"
                  )}
                  onClick={trendLink ? onTrendClick : undefined}
                >
                  {trendUp && <TrendingUp className="w-3 h-3" />}
                  {trend}
                </p>
              ) : null}
            </div>
          </div>
          <div
            className={cn(
              "w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0",
              iconBg
            )}
          >
            <span className={iconText}>{icon}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
