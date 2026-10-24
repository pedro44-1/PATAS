import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiErrorMessage } from "@/api/errors";
import { FormError } from "@/components/ui/form-error";
import { PromptDialog } from "@/components/ui/prompt-dialog";
import { useToast } from "@/contexts/ToastContext";
import { Building2, Check, Clock3, Coins, Edit3, FolderTree, Plus, Stethoscope, X } from "lucide-react";

import { examCatalogApi } from "@/api/examCatalog";
import { Clinic, clinicsApi } from "@/api/clinics";
import { serviceTypesApi } from "@/api/serviceTypes";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ExamCatalog, ServiceType } from "@patas/shared-types";

export default function Settings() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [catalog, setCatalog] = useState<ExamCatalog>({ systems: [] });
  const [newService, setNewService] = useState("");
  const [newSystem, setNewSystem] = useState("");
  const [loading, setLoading] = useState(true);
  const [clinic, setClinic] = useState<Clinic | null>(null);
  const [clinicNif, setClinicNif] = useState("");
  const [billingStoreId, setBillingStoreId] = useState("");
  const isAdmin = user?.role === "admin";
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [prompt, setPrompt] = useState<{ kind: "rename"; service: ServiceType } | { kind: "finding"; systemId: number } | null>(null);

  function load() {
    setLoadError("");
    Promise.allSettled([serviceTypesApi.list(), examCatalogApi.get(), clinicsApi.get()]).then(([serviceResult, catalogResult, clinicResult]) => {
      if (serviceResult.status === "fulfilled") setServiceTypes(serviceResult.value.data);
      if (catalogResult.status === "fulfilled") setCatalog(catalogResult.value.data);
      if (clinicResult.status === "fulfilled") {
        setClinic(clinicResult.value.data);
        setClinicNif(clinicResult.value.data.nif ?? "");
        setBillingStoreId(clinicResult.value.data.billing_store_external_id ?? "");
      }
      const failure = [serviceResult, catalogResult, clinicResult].find((result) => result.status === "rejected");
      if (failure && failure.status === "rejected") setLoadError(apiErrorMessage(failure.reason, t, "settings.loadError"));
    }).finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function run(action: () => Promise<unknown>, successKey?: string) {
    setBusy(true);
    try {
      await action();
      if (successKey) toast.success(t(successKey));
      load();
      return true;
    } catch (requestError: unknown) {
      toast.error(apiErrorMessage(requestError, t, "settings.saveError"));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function createService(event: React.FormEvent) {
    event.preventDefault();
    if (!newService.trim()) return;
    if (await run(() => serviceTypesApi.create({ name: newService.trim(), sort_order: serviceTypes.length }), "settings.catalog.saved")) setNewService("");
  }

  async function createSystem(event: React.FormEvent) {
    event.preventDefault();
    if (!newSystem.trim()) return;
    if (await run(() => examCatalogApi.createSystem({ name: newSystem.trim(), sort_order: catalog.systems.length }), "settings.catalog.saved")) setNewSystem("");
  }

  async function submitPrompt(name: string) {
    if (!prompt) return;
    const target = prompt;
    const saved = target.kind === "rename"
      ? await run(() => serviceTypesApi.update(target.service.id, { name }), "settings.catalog.saved")
      : await run(() => examCatalogApi.createFinding(target.systemId, {
        name,
        sort_order: catalog.systems.find((item) => item.id === target.systemId)?.findings.length ?? 0,
      }), "settings.catalog.saved");
    if (saved) setPrompt(null);
  }

  function toggleService(service: ServiceType) {
    return run(() => serviceTypesApi.update(service.id, { active: !service.active }));
  }

  function toggleSystem(id: number, active: boolean) {
    return run(() => examCatalogApi.updateSystem(id, { active: !active }));
  }

  function toggleFinding(id: number, active: boolean) {
    return run(() => examCatalogApi.updateFinding(id, { active: !active }));
  }

  async function saveClinicNif(event: React.FormEvent) {
    event.preventDefault();
    await run(() => clinicsApi.update({
      nif: clinicNif.trim() || null,
      billing_store_external_id: billingStoreId.trim() || null,
    }), "settings.billingSaved");
  }

  const items = [
    { label: t("settings.clinic"), value: clinic?.name ?? t("settings.clinicValue", { id: user?.clinic_id }), icon: Building2 },
    { label: t("settings.currency"), value: t("settings.currencyValue"), icon: Coins },
    { label: t("settings.timezone"), value: t("settings.timezoneValue"), icon: Clock3 },
  ];

  return <div className="page-enter space-y-6">
    <div><h2 className="text-2xl font-semibold tracking-tight text-foreground">{t("settings.title")}</h2><p className="mt-1 text-sm text-muted-foreground">{t("settings.subtitle")}</p></div>
    {loadError && <div className="max-w-3xl"><FormError message={loadError} /></div>}
    <Card className="max-w-3xl"><CardContent className="p-0">{items.map(({ label, value, icon: Icon }) => <div key={label} className="flex items-center gap-4 border-b border-border/70 px-5 py-5 last:border-0 sm:px-6"><span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground"><Icon className="size-4" /></span><div><p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold text-foreground">{value}</p></div></div>)}</CardContent></Card>
    <Card className="max-w-3xl"><CardContent className="p-5 sm:p-6"><form onSubmit={saveClinicNif} className="grid gap-4 sm:grid-cols-2"><div className="space-y-1.5"><Label htmlFor="clinic-nif">{t("settings.billingNif")}</Label><Input id="clinic-nif" value={clinicNif} onChange={(event) => setClinicNif(event.target.value)} maxLength={30} disabled={!isAdmin} placeholder={t("settings.billingNifPlaceholder")} /><p className="text-xs text-muted-foreground">{t("settings.billingNifHint")}</p></div><div className="space-y-1.5"><Label htmlFor="billing-store-id">{t("settings.billingStoreId")}</Label><Input id="billing-store-id" value={billingStoreId} onChange={(event) => setBillingStoreId(event.target.value)} maxLength={100} disabled={!isAdmin} placeholder={t("settings.billingStoreIdPlaceholder")} /><p className="text-xs text-muted-foreground">{t("settings.billingStoreIdHint")}</p></div>{isAdmin && <div className="sm:col-span-2"><Button type="submit" disabled={busy}>{busy ? t("common.saving") : t("common.save")}</Button></div>}</form></CardContent></Card>
    <div className="grid gap-6 xl:grid-cols-2">
      <Card><div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("settings.catalog.servicesTitle")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("settings.catalog.servicesHint")}</p></div><FolderTree className="size-5 text-primary" /></div><CardContent className="space-y-4 p-5">{isAdmin && <form onSubmit={createService} className="flex gap-2"><Label htmlFor="new-service" className="sr-only">{t("settings.catalog.newService")}</Label><Input id="new-service" value={newService} onChange={(event) => setNewService(event.target.value)} placeholder={t("settings.catalog.servicePlaceholder")} /><Button type="submit"><Plus className="mr-1.5 size-4" />{t("common.add")}</Button></form>}{loading ? <p className="text-sm text-muted-foreground">{t("common.loading")}</p> : <div className="divide-y divide-border/70">{serviceTypes.map((service) => <div key={service.id} className="flex items-center gap-3 py-3"><span className={`size-2 rounded-full ${service.active ? "bg-emerald-500" : "bg-muted-foreground/30"}`} /><span className={`flex-1 text-sm font-semibold ${service.active ? "text-foreground" : "text-muted-foreground line-through"}`}>{service.name}</span>{isAdmin && <><Button type="button" size="icon-xs" variant="ghost" disabled={busy} aria-label={t("settings.catalog.renameNamed", { name: service.name })} onClick={() => setPrompt({ kind: "rename", service })}><Edit3 className="size-3.5" /></Button><Button type="button" size="icon-xs" variant="ghost" disabled={busy} aria-label={t(service.active ? "settings.catalog.deactivateNamed" : "settings.catalog.activateNamed", { name: service.name })} onClick={() => toggleService(service)}>{service.active ? <X className="size-3.5 text-destructive" /> : <Check className="size-3.5 text-emerald-600" />}</Button></>}</div>)}</div>}</CardContent></Card>
      <Card><div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("settings.catalog.examTitle")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("settings.catalog.examHint")}</p></div><Stethoscope className="size-5 text-primary" /></div><CardContent className="space-y-4 p-5">{isAdmin && <form onSubmit={createSystem} className="flex gap-2"><Label htmlFor="new-system" className="sr-only">{t("settings.catalog.newSystem")}</Label><Input id="new-system" value={newSystem} onChange={(event) => setNewSystem(event.target.value)} placeholder={t("settings.catalog.systemPlaceholder")} /><Button type="submit"><Plus className="mr-1.5 size-4" />{t("common.add")}</Button></form>}<div className="space-y-3">{catalog.systems.map((system) => <div key={system.id} className="rounded-xl border border-border/70 p-3"><div className="flex items-center gap-2"><span className={`size-2 rounded-full ${system.active ? "bg-emerald-500" : "bg-muted-foreground/30"}`} /><p className={`flex-1 text-sm font-bold ${system.active ? "text-foreground" : "text-muted-foreground line-through"}`}>{system.name}</p>{isAdmin && <><Button type="button" size="icon-xs" variant="ghost" disabled={busy} aria-label={t("settings.catalog.addFindingTo", { name: system.name })} onClick={() => setPrompt({ kind: "finding", systemId: system.id })}><Plus className="size-3.5" /></Button><Button type="button" size="icon-xs" variant="ghost" disabled={busy} aria-label={t(system.active ? "settings.catalog.deactivateNamed" : "settings.catalog.activateNamed", { name: system.name })} onClick={() => toggleSystem(system.id, system.active)}>{system.active ? <X className="size-3.5 text-destructive" /> : <Check className="size-3.5 text-emerald-600" />}</Button></>}</div><div className="mt-2 flex flex-wrap gap-1.5">{system.findings.map((finding) => <button key={finding.id} type="button" disabled={!isAdmin || busy} aria-pressed={finding.active} onClick={() => toggleFinding(finding.id, finding.active)} className={`rounded-full border px-2 py-1 text-[11px] ${finding.active ? "border-border text-muted-foreground" : "border-transparent bg-muted text-muted-foreground/60 line-through"}`}>{finding.name}</button>)}</div></div>)}</div></CardContent></Card>
    </div>
    <PromptDialog
      open={prompt !== null}
      onOpenChange={(open) => { if (!open) setPrompt(null); }}
      title={t(prompt?.kind === "rename" ? "settings.catalog.renameTitle" : "settings.catalog.findingTitle")}
      label={t(prompt?.kind === "rename" ? "settings.catalog.renamePrompt" : "settings.catalog.findingPrompt")}
      initialValue={prompt?.kind === "rename" ? prompt.service.name : ""}
      confirmLabel={t("common.save")}
      cancelLabel={t("common.cancel")}
      pending={busy}
      maxLength={100}
      onConfirm={submitPrompt}
    />
  </div>;
}
