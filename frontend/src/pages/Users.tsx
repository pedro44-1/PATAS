import { useEffect, useState } from "react";
import { Plus, ShieldCheck, Users as UsersIcon } from "lucide-react";
import { useTranslation } from "react-i18next";
import { usersApi, ClinicUser, UserRole } from "@/api/users";
import { apiErrorMessage } from "@/api/errors";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";

export default function Users() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [users, setUsers] = useState<ClinicUser[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "receptionist" as UserRole });
  const roleLabels: Record<UserRole, string> = { admin: t("roles.admin"), vet: t("roles.vet"), receptionist: t("roles.receptionist") };

  function load() {
    usersApi.list().then((response) => setUsers(response.data)).catch(() => setError(t("users.restricted")));
  }

  useEffect(() => {
    if (user?.role === "admin") load();
  }, [user?.role]);

  async function changeRole(id: number, role: UserRole) {
    setError("");
    try {
      await usersApi.updateRole(id, role);
      load();
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "users.createError"));
    }
  }

  async function createUser(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await usersApi.create(form);
      setForm({ name: "", email: "", password: "", role: "receptionist" });
      setShowCreate(false);
      setMessage(t("users.created"));
      load();
    } catch (requestError: unknown) {
      setError(apiErrorMessage(requestError, t, "users.createError"));
    } finally {
      setSaving(false);
    }
  }

  if (user?.role !== "admin") return <Card className="max-w-2xl"><CardContent className="flex items-center gap-3 p-6 text-sm text-muted-foreground"><ShieldCheck className="size-5 text-primary" />{t("users.restricted")}</CardContent></Card>;

  return (
    <div className="page-enter space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-2xl font-semibold tracking-tight text-foreground">{t("users.title")}</h2><p className="mt-1 text-sm text-muted-foreground">{t("users.subtitle")}</p></div><Button onClick={() => setShowCreate((value) => !value)}><Plus className="mr-2 size-4" />{t("users.create")}</Button></div>
      {showCreate && <Card><CardContent className="p-5 sm:p-6"><div className="mb-5"><h3 className="font-semibold text-foreground">{t("users.createTitle")}</h3><p className="mt-1 text-sm text-muted-foreground">{t("users.createHint")}</p></div><form onSubmit={createUser} className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor="team-name">{t("users.name")}</Label><Input id="team-name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} maxLength={100} required /></div><div className="space-y-2"><Label htmlFor="team-email">{t("users.email")}</Label><Input id="team-email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></div><div className="space-y-2"><Label htmlFor="team-password">{t("users.temporaryPassword")}</Label><Input id="team-password" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} minLength={8} maxLength={128} required /><p className="text-xs text-muted-foreground">{t("auth.passwordRules")}</p></div><div className="space-y-2"><Label htmlFor="team-role">{t("users.role")}</Label><FormSelect id="team-role" value={form.role} onValueChange={(value) => setForm({ ...form, role: value as UserRole })} options={Object.entries(roleLabels).map(([value, label]) => ({ value, label }))} /></div><div className="flex justify-end gap-2 border-t border-border/70 pt-4 sm:col-span-2"><Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>{t("common.cancel")}</Button><Button type="submit" disabled={saving}>{saving ? t("common.saving") : t("users.create")}</Button></div></form></CardContent></Card>}
      {message && <div role="status" className="rounded-xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm text-primary">{message}</div>}
      <Card><CardContent className="p-0">{error ? <div className="p-6 text-sm text-destructive">{error}</div> : users.length === 0 ? <div className="flex flex-col items-center py-16 text-muted-foreground"><UsersIcon className="mb-3 size-10 opacity-35" /><p className="text-sm font-medium">{t("users.empty")}</p></div> : users.map((clinicUser) => <div key={clinicUser.id} className="flex flex-col gap-4 border-b border-border/70 px-5 py-4 last:border-0 sm:flex-row sm:items-center sm:px-6"><span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-sm font-bold text-secondary-foreground">{clinicUser.name.slice(0, 1).toUpperCase()}</span><div className="min-w-0 flex-1"><p className="truncate font-semibold text-foreground">{clinicUser.name}</p><p className="truncate text-xs text-muted-foreground">{clinicUser.email}</p></div><FormSelect value={clinicUser.role} disabled={clinicUser.id === user.id} onValueChange={(value) => changeRole(clinicUser.id, value as UserRole)} options={Object.entries(roleLabels).map(([value, label]) => ({ value, label }))} className="w-full text-foreground sm:w-44" /></div>)}</CardContent></Card>
    </div>
  );
}
