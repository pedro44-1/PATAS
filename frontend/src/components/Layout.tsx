import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  LayoutDashboard,
  Users,
  PawPrint,
  CalendarDays,
  Pill,
  FileText,
  Settings,
  UserCircle,
  LogOut,
  Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS: {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  badgeVariant?: "default" | "warning";
}[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/owners", label: "Donos", icon: Users },
  { to: "/pets", label: "Animais", icon: PawPrint },
  { to: "/appointments", label: "Consultas", icon: CalendarDays, badge: 3 },
  { to: "/treatments", label: "Tratamentos", icon: Pill },
  { to: "/invoices", label: "Faturas", icon: FileText, badge: 5, badgeVariant: "warning" },
];

const SYSTEM_ITEMS: {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { to: "/settings", label: "Configurações", icon: Settings },
  { to: "/users", label: "Utilizadores", icon: UserCircle },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const initials = user?.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "VS";

  const roleLabel = user?.role === "vet" ? "Veterinário" : "Rececionista";
  const pageTitle = getPageTitle(location.pathname);

  return (
    <div className="flex h-screen overflow-hidden bg-dark-100">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-dark-950 flex flex-col border-r border-dark-800">
        {/* Logo */}
        <div className="px-6 py-8">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-brand-600 rounded-xl flex items-center justify-center text-lg shadow-lg shadow-brand-600/30 flex-shrink-0">
              🐾
            </div>
            <div>
              <div className="text-white font-extrabold text-xl tracking-widest leading-none">
                PATAS
              </div>
              <div className="text-dark-500 text-[10px] tracking-widest uppercase mt-0.5">
                Vet SaaS
              </div>
            </div>
          </div>
        </div>

        {/* Nav label */}
        <div className="px-6 pb-2">
          <p className="text-dark-600 text-xs font-semibold uppercase tracking-widest">
            Menu
          </p>
        </div>

        {/* Main nav */}
        <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto scrollbar-hide">
          {NAV_ITEMS.map(({ to, label, icon: Icon, badge, badgeVariant }) => {
            const isActive = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-brand-600/15 text-brand-400 font-semibold"
                    : "text-dark-400 hover:text-dark-100 hover:bg-dark-800/60"
                )}
              >
                <Icon
                  className={cn(
                    "w-[18px] h-[18px] flex-shrink-0",
                    isActive ? "text-brand-400" : "text-dark-500"
                  )}
                />
                <span className="flex-1">{label}</span>
                {badge !== undefined && (
                  <span
                    className={cn(
                      "text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none",
                      isActive || badgeVariant === "warning"
                        ? "bg-brand-600 text-white"
                        : "bg-dark-800 text-dark-500"
                    )}
                  >
                    {badge}
                  </span>
                )}
              </NavLink>
            );
          })}

          {/* Divider */}
          <div className="pt-4 pb-2">
            <div className="px-3">
              <div className="border-t border-dark-800" />
            </div>
            <p className="text-dark-600 text-xs font-semibold uppercase tracking-widest px-3 pt-3">
              Sistema
            </p>
          </div>

          {SYSTEM_ITEMS.map(({ to, label, icon: Icon }) => {
            const isActive = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-dark-800 text-dark-100 font-semibold"
                    : "text-dark-500 hover:text-dark-200 hover:bg-dark-800/60"
                )}
              >
                <Icon className="w-[18px] h-[18px] flex-shrink-0" />
                <span>{label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Notification */}
        <div className="px-4 mx-3 mb-3">
          <button className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-dark-500 hover:text-dark-200 hover:bg-dark-800/60 transition-all text-sm">
            <Bell className="w-[18px] h-[18px]" />
            <span>Notificações</span>
            <span className="ml-auto w-2 h-2 rounded-full bg-red-500" />
          </button>
        </div>

        {/* User card */}
        <div className="p-3 mx-3 mb-4 rounded-2xl bg-dark-900 border border-dark-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-brand-600/20 flex-shrink-0">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-dark-100 font-semibold text-sm truncate">
                {user?.name ?? "Veterinário"}
              </div>
              <div className="text-dark-500 text-xs">{roleLabel}</div>
            </div>
            <button
              onClick={logout}
              className="text-dark-500 hover:text-red-400 transition-colors p-1.5 rounded-xl hover:bg-dark-800 flex-shrink-0"
              title="Sair"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-dark-200 flex items-center justify-between px-8 flex-shrink-0">
          <div>
            <h1 className="text-lg font-bold text-dark-900 leading-none">
              {pageTitle}
            </h1>
            <p className="text-dark-400 text-xs mt-0.5">
              {new Date().toLocaleDateString("pt-AO", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-brand-600/25 transition-all active:scale-95">
              <span className="text-base">+</span>
              Nova Consulta
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function getPageTitle(path: string): string {
  if (path.startsWith("/dashboard")) return "Dashboard";
  if (path.startsWith("/owners")) return "Donos";
  if (path.startsWith("/pets")) return "Animais";
  if (path.startsWith("/appointments")) return "Consultas";
  if (path.startsWith("/treatments")) return "Tratamentos";
  if (path.startsWith("/invoices")) return "Faturas";
  if (path.startsWith("/settings")) return "Configurações";
  if (path.startsWith("/users")) return "Utilizadores";
  return "PATAS";
}
