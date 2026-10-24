import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { KeyRound } from "lucide-react";

import { BrandMark } from "@/components/BrandMark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { apiErrorMessage } from "@/api/errors";

export default function PasswordChange() {
  const { t } = useTranslation();
  const { changePassword, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (newPassword !== confirmation) {
      setError(t("auth.passwordMismatch"));
      return;
    }
    setSaving(true);
    setError("");
    try {
      await changePassword(currentPassword, newPassword);
      navigate("/dashboard", { replace: true });
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "auth.passwordChangeError"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-5 py-12">
      <ThemeToggle className="absolute right-5 top-5" />
      <div className="w-full max-w-md space-y-7">
        <BrandMark />
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">{t("auth.passwordChangeTitle")}</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{t("auth.passwordChangeHint")}</p>
        </div>
        <form onSubmit={submit} className="page-card space-y-5 p-6 sm:p-7">
          <div className="space-y-2"><Label htmlFor="current-password">{t("auth.currentPassword")}</Label><Input id="current-password" type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required autoFocus /></div>
          <div className="space-y-2"><Label htmlFor="new-password">{t("auth.newPassword")}</Label><Input id="new-password" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={8} maxLength={128} required /><p className="text-xs text-muted-foreground">{t("auth.passwordRules")}</p></div>
          <div className="space-y-2"><Label htmlFor="confirm-password">{t("auth.confirmPassword")}</Label><Input id="confirm-password" type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} minLength={8} maxLength={128} required /></div>
          {error && <div role="alert" className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">{error}</div>}
          <Button type="submit" className="w-full" disabled={saving}><KeyRound className="mr-2 size-4" />{saving ? t("common.saving") : t("auth.changePassword")}</Button>
          <Button type="button" variant="ghost" className="w-full" onClick={() => void logout()}>{t("auth.logoutInstead")}</Button>
        </form>
      </div>
    </main>
  );
}
