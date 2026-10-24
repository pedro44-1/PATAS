import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowRight, Eye, EyeOff, LockKeyhole, ShieldCheck } from "lucide-react";
import { authApi } from "@/api/auth";
import { apiErrorMessage } from "@/api/errors";
import { useAuth } from "@/contexts/AuthContext";
import { BrandMark } from "@/components/BrandMark";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";

const DEMO_USERS = [
  { name: "Dr. António Silva", role: "vet", email: "vet@patas.ao", initials: "AS" },
  { name: "Maria Santos", role: "receptionist", email: "receptionist@patas.ao", initials: "MS" },
];

export default function Login() {
  const [email, setEmail] = useState("vet@patas.ao");
  const [password, setPassword] = useState("Password1");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokenResponse = await authApi.login({ email, password });
      localStorage.setItem("patas_token", tokenResponse.data.access_token);
      localStorage.setItem("patas_refresh_token", tokenResponse.data.refresh_token);
      const userResponse = await authApi.me();
      login(tokenResponse.data, userResponse.data);
      navigate(userResponse.data.must_change_password ? "/change-password" : "/dashboard");
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "auth.loginError", { 401: "auth.loginError" }));
    } finally {
      setLoading(false);
    }
  }

  function chooseDemo(demoEmail: string) {
    setEmail(demoEmail);
    setPassword("Password1");
    setError("");
  }

  return (
    <main className="grid min-h-screen bg-background lg:grid-cols-[1.08fr_0.92fr]">
      <section className="login-hero relative flex flex-col overflow-hidden px-5 pb-5 pt-5 sm:px-10 lg:min-h-screen lg:justify-between lg:p-10 xl:p-14">
        <BrandMark className="relative z-10 [&_span:nth-child(2)>span:first-child]:text-white [&_span:nth-child(2)>span:last-child]:text-white/70" />
        <div className="relative z-10 flex min-h-0 flex-1 items-center justify-center py-3 lg:py-6">
          <img
            src="/brand/hibisco-login-960.webp"
            srcSet="/brand/hibisco-login-960.webp 960w, /brand/hibisco-login-1920.webp 1920w"
            sizes="(min-width: 1024px) 640px, 240px"
            width={1920}
            height={1674}
            alt=""
            aria-hidden="true"
            loading="eager"
            decoding="async"
            className="h-36 w-auto max-w-full object-contain sm:h-44 lg:h-[clamp(18rem,48vh,34rem)]"
          />
        </div>
        <div className="relative z-10 hidden max-w-xl lg:block">
          <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white/85"><ShieldCheck className="size-4" />{t("auth.secureAccess")}</span>
          <h1 className="text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">{t("app.tagline")}</h1>
          <p className="mt-4 max-w-md text-base leading-7 text-white/75">{t("auth.accessHint")}</p>
          <div className="mt-8 grid grid-cols-3 gap-3 border-t border-white/15 pt-6">
            {["nav.pets", "nav.appointments", "nav.invoices"].map((item) => <span key={item} className="text-sm font-medium text-white/80">{t(item)}</span>)}
          </div>
          <p className="mt-8 text-xs font-medium tracking-wide text-white/65">{t("auth.location")}</p>
        </div>
      </section>

      <section className="relative flex items-start justify-center px-5 pb-12 pt-16 sm:px-10 lg:min-h-screen lg:items-center lg:p-10">
        <ThemeToggle className="absolute right-5 top-5 sm:right-8 sm:top-8" />
        <div className="w-full max-w-md page-enter">
          <div className="mb-8">
            <p className="mb-3 text-sm font-semibold text-primary">{t("app.name")}</p>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground">{t("auth.welcome")}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{t("auth.accessHint")}</p>
          </div>

          <form onSubmit={handleSubmit} className="page-card space-y-5 p-6 sm:p-7">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-semibold text-foreground">{t("auth.email")}</label>
              <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required className="h-11 w-full rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus-visible:ring-2 focus-visible:ring-primary/55 focus-visible:ring-offset-2 focus-visible:ring-offset-card" />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-semibold text-foreground">{t("auth.password")}</label>
              <div className="relative">
                <input id="password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} required className="h-11 w-full rounded-xl border border-input bg-background px-3 pr-11 text-sm text-foreground outline-none transition focus:border-primary focus-visible:ring-2 focus-visible:ring-primary/55 focus-visible:ring-offset-2 focus-visible:ring-offset-card" />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-1 top-1 flex size-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground" aria-label={showPassword ? t("auth.hidePassword") : t("auth.showPassword")}>
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>
            {error && <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">{error}</div>}
            <button type="submit" disabled={loading} className="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground shadow-[0_10px_20px_oklch(var(--primary)/0.22)] transition hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60">
              {loading ? <span className="size-4 animate-spin rounded-full border-2 border-primary-foreground/35 border-t-primary-foreground" /> : <LockKeyhole className="size-4" />}
              {loading ? t("auth.loggingIn") : t("auth.loginButton")}
              {!loading && <ArrowRight className="size-4" />}
            </button>
          </form>

          <div className="mt-7">
            <p className="mb-3 text-center text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">{t("auth.demoHint")}</p>
            <div className="grid grid-cols-2 gap-3">
              {DEMO_USERS.map((demo) => (
                <button key={demo.email} type="button" onClick={() => chooseDemo(demo.email)} className={cn("flex items-center gap-3 rounded-2xl border p-3 text-left transition", email === demo.email ? "border-primary bg-primary/8" : "border-border bg-card hover:border-primary/40 hover:bg-muted/50")}>
                  <span className="flex size-9 items-center justify-center rounded-xl bg-secondary text-xs font-bold text-secondary-foreground">{demo.initials}</span>
                  <span className="min-w-0"><span className="block truncate text-xs font-semibold text-foreground">{demo.name}</span><span className="mt-0.5 block text-[0.68rem] text-muted-foreground">{t(`roles.${demo.role}`)}</span></span>
                </button>
              ))}
            </div>
          </div>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            {t("auth.noClinic")} <Link to="/register" className="font-semibold text-primary hover:underline">{t("auth.registerClinic")}</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
