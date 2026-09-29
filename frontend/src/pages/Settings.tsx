import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Building2, Check, Clock3, Coins, Edit3, FolderTree, Plus, Stethoscope, X } from "lucide-react";

import { examCatalogApi } from "@/api/examCatalog";
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
  const isAdmin = user?.role === "admin";

  function load() {
    Promise.all([serviceTypesApi.list(), examCatalogApi.get()]).then(([serviceResponse, catalogResponse]) => {
      setServiceTypes(serviceResponse.data);
      setCatalog(catalogResponse.data);
    }).finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function createService(event: React.FormEvent) {
    event.preventDefault();
    if (!newService.trim()) return;
    await serviceTypesApi.create({ name: newService.trim(), sort_order: serviceTypes.length });
    setNewService("");
    load();
  }

  async function renameService(service: ServiceType) {
    const name = window.prompt(t("settings.catalog.renamePrompt"), service.name);
    if (!name?.trim()) return;
    await serviceTypesApi.update(service.id, { name: name.trim() });
    load();
  }

  async function createSystem(event: React.FormEvent) {
    event.preventDefault();
    if (!newSystem.trim()) return;
    await examCatalogApi.createSystem({ name: newSystem.trim(), sort_order: catalog.systems.length });
    setNewSystem("");
    load();
  }

  async function createFinding(systemId: number) {
    const name = window.prompt(t("settings.catalog.findingPrompt"));
    if (!name?.trim()) return;
    const system = catalog.systems.find((item) => item.id === systemId);
    await examCatalogApi.createFinding(systemId, { name: name.trim(), sort_order: system?.findings.length ?? 0 });
    load();
  }

  async function toggleService(service: ServiceType) {
    await serviceTypesApi.update(service.id, { active: !service.active });
    load();
  }

  async function toggleSystem(id: number, active: boolean) {
    await examCatalogApi.updateSystem(id, { active: !active });
    load();
  }

  async function toggleFinding(id: number, active: boolean) {
    await examCatalogApi.updateFinding(id, { active: !active });
    load();
  }

  const items = [
    { label: t("settings.clinic"), value: t("settings.clinicValue", { id: user?.clinic_id }), icon: Building2 },
    { label: t("settings.currency"), value: t("settings.currencyValue"), icon: Coins },
    { label: t("settings.timezone"), value: t("settings.timezoneValue"), icon: Clock3 },
  ];

  return <div className="page-enter space-y-6">
    <div><h2 className="text-2xl font-semibold tracking-tight text-foreground">{t("settings.title")}</h2><p className="mt-1 text-sm text-muted-foreground">{t("settings.subtitle")}</p></div>
    <Card className="max-w-3xl"><CardContent className="p-0">{items.map(({ label, value, icon: Icon }) => <div key={label} className="flex items-center gap-4 border-b border-border/70 px-5 py-5 last:border-0 sm:px-6"><span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground"><Icon className="size-4" /></span><div><p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold text-foreground">{value}</p></div></div>)}</CardContent></Card>
    <div className="grid gap-6 xl:grid-cols-2">
      <Card><div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("settings.catalog.servicesTitle")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("settings.catalog.servicesHint")}</p></div><FolderTree className="size-5 text-primary" /></div><CardContent className="space-y-4 p-5">{isAdmin && <form onSubmit={createService} className="flex gap-2"><Label className="sr-only">{t("settings.catalog.newService")}</Label><Input value={newService} onChange={(event) => setNewService(event.target.value)} placeholder={t("settings.catalog.servicePlaceholder")} /><Button type="submit"><Plus className="mr-1.5 size-4" />{t("common.add")}</Button></form>}{loading ? <p className="text-sm text-muted-foreground">{t("common.loading")}</p> : <div className="divide-y divide-border/70">{serviceTypes.map((service) => <div key={service.id} className="flex items-center gap-3 py-3"><span className={`size-2 rounded-full ${service.active ? "bg-emerald-500" : "bg-muted-foreground/30"}`} /><span className={`flex-1 text-sm font-semibold ${service.active ? "text-foreground" : "text-muted-foreground line-through"}`}>{service.name}</span>{isAdmin && <><Button type="button" size="icon-xs" variant="ghost" onClick={() => renameService(service)}><Edit3 className="size-3.5" /></Button><Button type="button" size="icon-xs" variant="ghost" onClick={() => toggleService(service)}>{service.active ? <X className="size-3.5 text-destructive" /> : <Check className="size-3.5 text-emerald-600" />}</Button></>}</div>)}</div>}</CardContent></Card>
      <Card><div className="flex items-center justify-between border-b border-border/70 px-5 py-4"><div><h3 className="font-bold text-foreground">{t("settings.catalog.examTitle")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("settings.catalog.examHint")}</p></div><Stethoscope className="size-5 text-primary" /></div><CardContent className="space-y-4 p-5">{isAdmin && <form onSubmit={createSystem} className="flex gap-2"><Label className="sr-only">{t("settings.catalog.newSystem")}</Label><Input value={newSystem} onChange={(event) => setNewSystem(event.target.value)} placeholder={t("settings.catalog.systemPlaceholder")} /><Button type="submit"><Plus className="mr-1.5 size-4" />{t("common.add")}</Button></form>}<div className="space-y-3">{catalog.systems.map((system) => <div key={system.id} className="rounded-xl border border-border/70 p-3"><div className="flex items-center gap-2"><span className={`size-2 rounded-full ${system.active ? "bg-emerald-500" : "bg-muted-foreground/30"}`} /><p className={`flex-1 text-sm font-bold ${system.active ? "text-foreground" : "text-muted-foreground line-through"}`}>{system.name}</p>{isAdmin && <><Button type="button" size="icon-xs" variant="ghost" onClick={() => createFinding(system.id)}><Plus className="size-3.5" /></Button><Button type="button" size="icon-xs" variant="ghost" onClick={() => toggleSystem(system.id, system.active)}>{system.active ? <X className="size-3.5 text-destructive" /> : <Check className="size-3.5 text-emerald-600" />}</Button></>}</div><div className="mt-2 flex flex-wrap gap-1.5">{system.findings.map((finding) => <button key={finding.id} type="button" disabled={!isAdmin} onClick={() => toggleFinding(finding.id, finding.active)} className={`rounded-full border px-2 py-1 text-[11px] ${finding.active ? "border-border text-muted-foreground" : "border-transparent bg-muted text-muted-foreground/60 line-through"}`}>{finding.name}</button>)}</div></div>)}</div></CardContent></Card>
    </div>
  </div>;
}
