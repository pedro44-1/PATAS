import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Building2 } from "lucide-react";

import { authApi } from "@/api/auth";
import { apiErrorMessage } from "@/api/errors";
import { BrandMark } from "@/components/BrandMark";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";

export default function Register() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ clinic_name: "", name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await authApi.register(form);
      const tokenResponse = await authApi.login({ email: form.email, password: form.password });
      localStorage.setItem("patas_token", tokenResponse.data.access_token);
      localStorage.setItem("patas_refresh_token", tokenResponse.data.refresh_token);
      const userResponse = await authApi.me();
      login(tokenResponse.data, userResponse.data);
      navigate("/dashboard");
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "auth.registerError"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-5 py-12">
      <ThemeToggle className="absolute right-5 top-5" />
      <div className="w-full max-w-lg space-y-7">
        <BrandMark />
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">{t("auth.registerTitle")}</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{t("auth.registerHint")}</p>
        </div>
        <form onSubmit={submit} className="page-card space-y-5 p-6 sm:p-7">
          <div className="space-y-2"><Label htmlFor="clinic-name">{t("auth.clinicName")}</Label><Input id="clinic-name" value={form.clinic_name} onChange={(event) => setForm({ ...form, clinic_name: event.target.value })} maxLength={255} required autoFocus /></div>
          <div className="space-y-2"><Label htmlFor="admin-name">{t("auth.adminName")}</Label><Input id="admin-name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} maxLength={100} required /></div>
          <div className="space-y-2"><Label htmlFor="register-email">{t("auth.email")}</Label><Input id="register-email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></div>
          <div className="space-y-2"><Label htmlFor="register-password">{t("auth.password")}</Label><Input id="register-password" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} minLength={8} maxLength={128} required /><p className="text-xs text-muted-foreground">{t("auth.passwordRules")}</p></div>
          {error && <div role="alert" className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">{error}</div>}
          <Button type="submit" className="w-full" disabled={saving}><Building2 className="mr-2 size-4" />{saving ? t("common.saving") : t("auth.createClinic")}</Button>
        </form>
        <Link to="/login" className="flex items-center justify-center gap-2 text-sm font-semibold text-primary hover:underline"><ArrowLeft className="size-4" />{t("auth.backToLogin")}</Link>
      </div>
    </main>
  );
}
