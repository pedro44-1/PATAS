import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import { BrandMark } from "@/components/BrandMark";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import {
  CalendarDays,
  ClipboardCheck,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  PawPrint,
  Pill,
  Plus,
  Settings,
  UserCircle,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/dashboard", label: "nav.dashboard", icon: LayoutDashboard },
  { to: "/waiting-room", label: "nav.waitingRoom", icon: ClipboardCheck },
  { to: "/appointments", label: "nav.appointments", icon: CalendarDays },
  { to: "/owners", label: "nav.owners", icon: Users },
  { to: "/pets", label: "nav.pets", icon: PawPrint },
  { to: "/treatments", label: "nav.treatments", icon: Pill },
  { to: "/invoices", label: "nav.invoices", icon: FileText },
];

const SYSTEM_ITEMS = [
  { to: "/settings", label: "nav.settings", icon: Settings },
  { to: "/users", label: "nav.users", icon: UserCircle },
];

const MOBILE_ITEMS = [
  { to: "/dashboard", label: "nav.dashboard", icon: LayoutDashboard },
  { to: "/waiting-room", label: "nav.waitingRoom", icon: ClipboardCheck },
  { to: "/appointments", label: "nav.appointments", icon: CalendarDays },
  { to: "/pets", label: "nav.pets", icon: PawPrint },
];

function pageKey(path: string) {
  if (path.startsWith("/waiting-room")) return "nav.waitingRoom";
  if (path.includes("/clinical")) return "nav.clinicalAppointment";
  if (path.startsWith("/appointments")) return "nav.appointments";
  if (path.startsWith("/owners")) return "nav.owners";
  if (path.startsWith("/pets")) return "nav.pets";
  if (path.startsWith("/treatments")) return "nav.treatments";
  if (path.startsWith("/invoices")) return "nav.invoices";
  if (path.startsWith("/settings")) return "nav.settings";
  if (path.startsWith("/users")) return "nav.users";
  return "nav.dashboard";
}

function initials(name?: string) {
  return name?.split(" ").map((item) => item[0]).join("").slice(0, 2).toUpperCase() || "PT";
}

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();
  const location = useLocation();

  return (
    <nav className="flex min-h-0 flex-1 flex-col gap-7 overflow-y-auto px-3 py-6">
      <div>
        <p className="px-3 text-[0.65rem] font-bold uppercase tracking-[0.16em] text-muted-foreground">{t("nav.main")}</p>
        <div className="mt-3 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                onClick={onNavigate}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="size-[18px]" strokeWidth={active ? 2.4 : 2} />
                {t(label)}
              </NavLink>
            );
          })}
        </div>
      </div>
      <div>
        <p className="px-3 text-[0.65rem] font-bold uppercase tracking-[0.16em] text-muted-foreground">{t("nav.system")}</p>
        <div className="mt-3 space-y-1">
          {SYSTEM_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                onClick={onNavigate}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active ? "bg-secondary text-secondary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="size-[18px]" />
                {t(label)}
              </NavLink>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

function UserSummary({ compact = false, onLogout }: { compact?: boolean; onLogout: () => void }) {
  const { t } = useTranslation();
  const { user } = useAuth();
  const role = user?.role === "admin" ? t("roles.admin") : user?.role === "vet" ? t("roles.vet") : t("roles.receptionist");

  return (
    <div className={cn("flex items-center gap-3", compact ? "" : "rounded-2xl border border-border/80 bg-muted/45 p-3")}>
      <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-secondary text-xs font-bold text-secondary-foreground">{initials(user?.name)}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-foreground">{user?.name}</span>
        <span className="block truncate text-xs text-muted-foreground">{role}</span>
      </span>
      <Button variant="ghost" size="icon-sm" className="rounded-lg text-muted-foreground hover:text-destructive" onClick={onLogout} title={t("nav.logout")} aria-label={t("nav.logout")}>
        <LogOut className="size-4" />
      </Button>
    </div>
  );
}

function MobileNavigation() {
  const { t } = useTranslation();
  const location = useLocation();

  return (
    <nav className="mobile-bottom-nav fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-border/80 bg-card/95 px-1 pt-2 backdrop-blur-lg md:hidden">
      {MOBILE_ITEMS.map(({ to, label, icon: Icon }) => {
        const active = location.pathname.startsWith(to);
        return (
          <NavLink key={to} to={to} className={cn("flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl px-1 text-[0.65rem] font-semibold transition-colors", active ? "text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground")}>
            <span className={cn("flex size-7 items-center justify-center rounded-lg", active && "bg-primary/12")}><Icon className="size-[18px]" strokeWidth={active ? 2.5 : 2} /></span>
            <span className="max-w-full truncate">{t(label)}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { logout } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const today = new Intl.DateTimeFormat("pt-AO", { timeZone: "Africa/Luanda", weekday: "long", day: "numeric", month: "long" }).format(new Date());

  return (
    <div className="app-shell flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-[17rem] shrink-0 flex-col border-r border-border/80 bg-card/80 backdrop-blur xl:flex">
        <div className="border-b border-border/70 px-6 py-6"><BrandMark /></div>
        <Navigation />
        <div className="border-t border-border/70 p-4"><UserSummary onLogout={logout} /></div>
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-[17rem] gap-0 border-r border-border bg-card p-0 sm:max-w-none" showCloseButton={false}>
          <div className="flex items-center justify-between border-b border-border/70 px-5 py-5">
            <BrandMark compact />
            <Button variant="ghost" size="icon-sm" className="rounded-lg" onClick={() => setMobileOpen(false)} aria-label={t("common.closeMenu")}><X className="size-4" /></Button>
          </div>
          <Navigation onNavigate={() => setMobileOpen(false)} />
          <div className="border-t border-border/70 p-4"><UserSummary onLogout={logout} /></div>
        </SheetContent>
      </Sheet>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 flex h-[4.5rem] items-center justify-between border-b border-border/70 bg-background/80 px-4 pt-[env(safe-area-inset-top)] backdrop-blur-md sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Button variant="ghost" size="icon" className="rounded-xl xl:hidden" onClick={() => setMobileOpen(true)} aria-label={t("common.openMenu")}><Menu className="size-5" /></Button>
            <div className="min-w-0">
              <h1 className="truncate text-base font-bold text-foreground sm:text-lg">{t(pageKey(location.pathname))}</h1>
              <p className="hidden truncate text-xs capitalize text-muted-foreground sm:block">{today}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />
            <Button className="h-9 rounded-xl px-3 text-xs font-semibold shadow-[0_8px_20px_oklch(var(--primary)/0.18)] sm:px-4 sm:text-sm" onClick={() => navigate("/appointments")}>
              <Plus className="size-4" />
              <span className="hidden sm:inline">{t("appointments.new")}</span>
            </Button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[96rem] px-4 py-5 pb-24 sm:px-6 sm:py-6 sm:pb-6 lg:px-8 lg:py-8"><Outlet /></main>
      </div>
      <MobileNavigation />
    </div>
  );
}
