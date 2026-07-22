import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import {
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  PawPrint,
  CalendarDays,
  FileText,
  Users,
  ArrowRight,
} from "lucide-react";

const DEMO_USERS = [
  { name: "Dr. Ana", role: "Veterinário", email: "ana@patas.ao", initials: "AS" },
  { name: "Dr. João", role: "Veterinário", email: "joao@patas.ao", initials: "JM" },
  { name: "Carla", role: "Rececionista", email: "carla@patas.ao", initials: "CR" },
];

const FEATURES = [
  { icon: <PawPrint className="w-4 h-4" />, text: "Gestão completa de animais e donos" },
  { icon: <CalendarDays className="w-4 h-4" />, text: "Agenda inteligente de consultas" },
  { icon: <FileText className="w-4 h-4" />, text: "Faturas e tratamentos digitais" },
  { icon: <Users className="w-4 h-4" />, text: "Multi-utilizador com permissões" },
];

export default function Login() {
  const [email, setEmail] = useState("ana@patas.ao");
  const [password, setPassword] = useState("patas2026");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 80);
    return () => clearTimeout(t);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokenRes = await authApi.login({ email, password });
      const token = tokenRes.data.access_token;
      localStorage.setItem("patas_token", token);
      const userRes = await authApi.me();
      login(token, userRes.data);
      navigate("/dashboard");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Credenciais inválidas. Tente novamente."
      );
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(demoEmail: string) {
    setEmail(demoEmail);
    setPassword("patas2026");
    setError("");
  }

  return (
    <div className="min-h-screen flex">
      {/* ─── LEFT PANEL ─────────────────────────── */}
      <div className="hidden lg:flex lg:w-[48%] bg-dark-950 relative overflow-hidden flex-col justify-between p-12">
        {/* Ambient background blobs */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-80 h-80 rounded-full bg-brand-600/[0.06] blur-3xl animate-pulse" style={{ animationDuration: "6s" }} />
          <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-brand-600/[0.04] blur-3xl animate-pulse" style={{ animationDuration: "8s", animationDelay: "2s" }} />
          {/* Grid pattern */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
              backgroundSize: "48px 48px",
            }}
          />
        </div>

        {/* Logo */}
        <div className="relative flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center text-2xl shadow-2xl shadow-brand-600/40">
            🐾
          </div>
          <div>
            <div className="text-white font-extrabold text-3xl tracking-widest leading-none">
              PATAS
            </div>
            <div className="text-dark-500 text-xs tracking-widest uppercase mt-1 font-medium">
              Sistema Veterinário
            </div>
          </div>
        </div>

        {/* Hero copy */}
        <div className="relative space-y-8">
          <div>
            <h1 className="text-4xl font-extrabold text-white leading-tight">
              A clínica na palma da sua mão.
            </h1>
            <p className="text-dark-400 text-base mt-4 leading-relaxed max-w-sm">
              Gestão completa de animais, donos, consultas e faturas — tudo em
              tempo real, em qualquer lugar.
            </p>
          </div>

          {/* Feature list */}
          <ul className="space-y-3">
            {FEATURES.map(({ icon, text }, i) => (
              <li
                key={i}
                className={cn(
                  "flex items-center gap-3 text-dark-300 text-sm transition-all duration-300",
                  loaded ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4"
                )}
                style={{ transitionDelay: `${200 + i * 80}ms` }}
              >
                <span className="w-7 h-7 rounded-lg bg-brand-600/20 text-brand-400 flex items-center justify-center flex-shrink-0">
                  {icon}
                </span>
                {text}
              </li>
            ))}
          </ul>

          {/* Stats bar */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-dark-800">
            {[
              { value: "247+", label: "Animais geridos" },
              { value: "5", label: "Veterinários" },
              { value: "100%", label: "Digital" },
            ].map(({ value, label }) => (
              <div key={label}>
                <div className="text-white font-extrabold text-xl">{value}</div>
                <div className="text-dark-500 text-xs mt-0.5">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600/30 border border-brand-600/40 flex items-center justify-center text-sm">
              🐾
            </div>
            <div>
              <div className="text-dark-400 text-xs">
                Clínica Veterinária Luanda Sul
              </div>
              <div className="text-dark-600 text-[10px]">
                Benguela • Luanda • Angola
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── RIGHT PANEL (FORM) ─────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 bg-white relative overflow-hidden">
        {/* Top decorative arc */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-brand-50 -translate-y-1/2 translate-x-1/3 pointer-events-none" />

        <div
          className={cn(
            "w-full max-w-md transition-all duration-500 ease-out",
            loaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
          )}
        >
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center text-xl shadow-lg shadow-brand-600/30">
              🐾
            </div>
            <div>
              <div className="font-extrabold text-xl tracking-widest text-dark-900 leading-none">
                PATAS
              </div>
              <div className="text-dark-400 text-[10px] tracking-widest uppercase">
                Sistema Veterinário
              </div>
            </div>
          </div>

          {/* Heading */}
          <div className="mb-8">
            <h2 className="text-2xl font-extrabold text-dark-900">
              Boas-vindas 👋
            </h2>
            <p className="text-dark-400 text-sm mt-1.5">
              Entre com as suas credenciais para aceder ao sistema.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email field */}
            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="text-xs font-semibold text-dark-600"
              >
                Email
              </label>
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="veterinario@clinica.ao"
                  required
                  className="w-full h-11 pl-4 pr-4 rounded-xl border border-dark-200 bg-white text-sm text-dark-900 placeholder:text-dark-300 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
              </div>
            </div>

            {/* Password field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-xs font-semibold text-dark-600"
                >
                  Palavra-passe
                </label>
                <button
                  type="button"
                  className="text-xs text-dark-400 hover:text-brand-600 font-medium transition-colors"
                >
                  Esqueceu?
                </button>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full h-11 pl-4 pr-11 rounded-xl border border-dark-200 bg-white text-sm text-dark-900 placeholder:text-dark-300 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-600 transition-colors p-1"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Error alert */}
            {error && (
              <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 rounded-xl px-4 py-3 animate-fade-in">
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-red-700 text-sm leading-snug">{error}</p>
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className={cn(
                "w-full h-11 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all duration-200",
                loading
                  ? "bg-brand-400/80 cursor-not-allowed"
                  : "bg-brand-600 hover:bg-brand-700 shadow-lg shadow-brand-600/30 hover:shadow-brand-600/40 active:scale-[0.98]"
              )}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  A entrar...
                </>
              ) : (
                <>
                  Entrar na conta
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Demo users */}
          <div className="mt-8 pt-6 border-t border-dark-100">
            <p className="text-xs text-dark-400 font-medium mb-3 text-center">
              Entrar como — demonstração rápida
            </p>
            <div className="grid grid-cols-3 gap-2">
              {DEMO_USERS.map(({ name, role, email: demoEmail, initials }) => (
                <button
                  key={demoEmail}
                  type="button"
                  onClick={() => fillDemo(demoEmail)}
                  className={cn(
                    "flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all duration-150 text-center",
                    email === demoEmail
                      ? "border-brand-500 bg-brand-50 text-brand-700"
                      : "border-dark-200 hover:border-dark-300 hover:bg-dark-50 text-dark-600"
                  )}
                >
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold",
                      email === demoEmail
                        ? "bg-brand-600"
                        : "bg-dark-300"
                    )}
                  >
                    {initials}
                  </div>
                  <div>
                    <div className="text-xs font-semibold leading-tight">{name}</div>
                    <div className="text-[10px] text-dark-400 leading-tight mt-0.5">
                      {role}
                    </div>
                  </div>
                  {email === demoEmail && (
                    <CheckCircle className="absolute top-1 right-1 w-3 h-3 text-brand-600" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-dark-300 text-xs mt-8">
            © 2026 PATAS — Clínica Veterinária · Luanda, Angola
          </p>
        </div>
      </div>
    </div>
  );
}
