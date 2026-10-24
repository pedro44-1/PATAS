import { useEffect, useMemo, useState } from "react";
import { FormError } from "@/components/ui/form-error";
import { useTranslation } from "react-i18next";
import { FormDialog } from "@/components/ui/form-dialog";
import { PromptDialog } from "@/components/ui/prompt-dialog";
import { useToast } from "@/contexts/ToastContext";
import { parseApiDate } from "@/lib/date";
import { formatKz } from "@/lib/format";
import { useRemoteOptions } from "@/lib/use-remote-options";
import { AlertTriangle, Calculator, CheckCircle2, ExternalLink, FileText, Plus, RotateCw, Search, Send, Trash2, X } from "lucide-react";

import { appointmentsApi, Appointment } from "@/api/appointments";
import { apiErrorMessage } from "@/api/errors";
import { OPTIONS_LIMIT, PAGE_SIZE, totalCount } from "@/api/pagination";
import { ListPagination } from "@/components/ListPagination";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useDebouncedValue } from "@/lib/use-debounced-value";
import { Invoice, invoicesApi, InvoiceStatus, PaymentMethod } from "@/api/invoices";
import { Owner, ownersApi } from "@/api/owners";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FormSelect } from "@/components/ui/form-select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type DraftLine = { description: string; code?: string; vat_profile_code?: string; kind: "SERVICE" | "PRODUCT"; unit: string; quantity: number; unit_price: number; tax_rate: number };
type InvoiceForm = { owner_id: number; appointment_id: number | null; document_type: "FT" | "FR"; payment_method: PaymentMethod; items: DraftLine[] };

const emptyLine = (): DraftLine => ({ description: "", kind: "SERVICE", unit: "UN", quantity: 1, unit_price: 0, tax_rate: 0 });
const emptyForm = (): InvoiceForm => ({ owner_id: 0, appointment_id: null, document_type: "FT", payment_method: "tpa", items: [emptyLine()] });

const quoteExpiryTime = (value: string) => new Date(/[zZ]|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`).getTime();

const hasValidQuote = (invoice: Invoice) => Boolean(
  invoice.quote_id
  && invoice.quote_expires_at
  && quoteExpiryTime(invoice.quote_expires_at) > Date.now(),
);

const hasPendingEmission = (invoice: Invoice) => invoice.sync_attempts > 0 && Boolean(invoice.idempotency_key);

export default function Invoices() {
  const { t } = useTranslation();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  const [form, setForm] = useState<InvoiceForm>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search.trim());
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [pendingInvoices, setPendingInvoices] = useState<Invoice[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [emitTarget, setEmitTarget] = useState<Invoice | null>(null);
  const [cancelTarget, setCancelTarget] = useState<Invoice | null>(null);
  const [nifDraft, setNifDraft] = useState("");
  const [savingNif, setSavingNif] = useState(false);
  const ownerSearch = useRemoteOptions((query) => ownersApi.list({ q: query, limit: 50 }).then((response) => response.data));
  const toast = useToast();

  function load() {
    setLoading(true);
    setError("");
    Promise.all([
      invoicesApi.list({ status: filterStatus || undefined, q: debouncedSearch || undefined, skip: page * PAGE_SIZE, limit: PAGE_SIZE }),
      invoicesApi.list({ status: "sent", limit: OPTIONS_LIMIT }),
    ]).then(([invoiceResponse, pendingResponse]) => {
      setInvoices(invoiceResponse.data);
      setTotal(totalCount(invoiceResponse));
      setPendingInvoices(pendingResponse.data);
      setPendingCount(totalCount(pendingResponse));
    }).catch((requestError: unknown) => setError(apiErrorMessage(requestError, t, "invoices.error")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [filterStatus, debouncedSearch, page]);

  useEffect(() => {
    ownersApi.list({ limit: OPTIONS_LIMIT })
      .then((response) => setOwners(response.data))
      .catch((requestError: unknown) => setError(apiErrorMessage(requestError, t, "invoices.error")));
  }, []);

  useEffect(() => {
    if (!showForm || !form.owner_id) {
      setAppointments([]);
      return;
    }
    appointmentsApi.list({ ownerId: form.owner_id, order: "desc", limit: 50 })
      .then((response) => setAppointments(response.data))
      .catch((requestError: unknown) => setFormError(apiErrorMessage(requestError, t, "invoices.error")));
  }, [showForm, form.owner_id]);

  const ownerOptions = ownerSearch.withFound(owners);
  const owner = ownerOptions.find((item) => item.id === form.owner_id);
  const ownerAppointments = appointments.filter((item) => item.status !== "cancelled" && item.status !== "no-show");
  const subtotal = useMemo(
    () => form.items.reduce((result, item) => result + item.quantity * item.unit_price, 0),
    [form.items],
  );
  const pendingTotal = pendingInvoices.reduce((sum, item) => sum + Math.round(Number(item.quote_payable ?? item.amount) * 100), 0) / 100;

  function openCreate() {
    setForm(emptyForm());
    setFormError("");
    setNifDraft("");
    setShowForm(true);
  }

  function updateLine(index: number, patch: Partial<DraftLine>) {
    setForm((current) => ({ ...current, items: current.items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item) }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.owner_id) {
      setFormError(t("invoices.form.ownerRequired"));
      return;
    }
    setSaving(true);
    setFormError("");
    try {
      await invoicesApi.create({
        owner_id: form.owner_id,
        appointment_id: form.appointment_id ?? undefined,
        document_type: form.document_type,
        payment_method: form.document_type === "FR" ? form.payment_method : undefined,
        items: form.items,
      });
      setShowForm(false);
      toast.success(t("invoices.draftSaved"));
      load();
    } catch (requestError: unknown) {
      setFormError(apiErrorMessage(requestError, t, "invoices.error"));
    } finally {
      setSaving(false);
    }
  }

  async function runRowAction(id: number, action: () => Promise<unknown>, errorKey = "invoices.error") {
    setBusyId(id);
    try {
      await action();
    } catch (requestError: unknown) {
      toast.error(apiErrorMessage(requestError, t, errorKey));
    } finally {
      setBusyId(null);
      load();
    }
  }

  async function confirmCancel(reason: string) {
    if (!cancelTarget) return;
    const target = cancelTarget;
    await runRowAction(target.id, () => invoicesApi.update(target.id, { status: "cancelled" as InvoiceStatus, reason }));
    setCancelTarget(null);
  }

  async function saveOwnerNif() {
    if (!owner || !nifDraft.trim()) return;
    setSavingNif(true);
    setFormError("");
    try {
      const response = await ownersApi.update(owner.id, { nif: nifDraft.trim() });
      setOwners((current) => current.some((item) => item.id === owner.id)
        ? current.map((item) => item.id === owner.id ? response.data : item)
        : [response.data, ...current]);
      setNifDraft("");
      toast.success(t("invoices.form.nifSaved"));
    } catch (requestError: unknown) {
      setFormError(apiErrorMessage(requestError, t, "owners.error"));
    } finally {
      setSavingNif(false);
    }
  }

  async function confirmEmission() {
    if (!emitTarget) return;
    const target = emitTarget;
    await runRowAction(target.id, () => invoicesApi.sync(target.id));
    setEmitTarget(null);
  }

  function handlePreview(id: number) {
    return runRowAction(id, () => invoicesApi.preview(id), "invoices.previewError");
  }

  return <div className="space-y-6 animate-fade-in">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div><h2 className="text-2xl font-extrabold text-dark-900">{t("invoices.title")}</h2><p className="mt-0.5 text-sm text-dark-400">{t("invoices.count", { count: total })}</p></div>
      <div className="flex items-center gap-3">
        <FormSelect ariaLabel={t("invoices.table.status")} value={filterStatus} onValueChange={(value) => { setFilterStatus(value); setPage(0); }} options={["", "draft", "sent", "paid", "cancelled"].map((value) => ({ value, label: t(`invoices.filter.${value || "all"}`) }))} className="min-w-36" />
        <Button onClick={openCreate}><Plus className="mr-2 size-4" />{t("invoices.new")}</Button>
      </div>
    </div>

    <div className="rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">{t("invoices.trainingNotice")}</div>
    {pendingTotal > 0 && <div className="flex items-center justify-between rounded-2xl border border-amber-200 bg-amber-50 p-4"><div><p className="text-sm font-semibold text-amber-800">{t("invoices.pendingAlert.label")}</p><p className="text-xs text-amber-600">{t("invoices.pendingAlert.hint", { amount: formatKz(pendingTotal), count: pendingCount })}</p></div><span className="text-lg font-extrabold tabular-nums text-amber-800">{formatKz(pendingTotal)}</span></div>}
    <div className="relative"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-dark-400" /><Input aria-label={t("invoices.search")} placeholder={t("invoices.search")} value={search} onChange={(event) => { setSearch(event.target.value); setPage(0); }} className="h-11 rounded-xl bg-white pl-10" /></div>
    {error && <div role="alert" className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

    <Card><CardContent className="p-0">{loading ? <div className="flex justify-center py-16"><div className="size-6 animate-spin rounded-full border-2 border-brand-600/30 border-t-brand-600" /></div> : invoices.length === 0 ? <div className="flex flex-col items-center py-16 text-dark-400"><FileText className="mb-3 size-10 opacity-30" /><p className="text-sm font-medium">{t("invoices.noResults")}</p></div> : <Table>
      <TableHeader><TableRow><TableHead className="pl-5">{t("invoices.table.number")}</TableHead><TableHead>{t("invoices.table.owner")}</TableHead><TableHead>{t("invoices.table.value")}</TableHead><TableHead>{t("invoices.table.status")}</TableHead><TableHead>{t("invoices.table.description")}</TableHead><TableHead className="pr-5 text-right">{t("invoices.table.actions")}</TableHead></TableRow></TableHeader>
      <TableBody>{invoices.map((invoice) => <TableRow key={invoice.id}>
        <TableCell className="pl-5 font-bold text-dark-700">{invoice.document_number ?? `#${invoice.id}`}</TableCell>
        <TableCell className="font-medium">{invoice.customer_name ?? owners.find((item) => item.id === invoice.owner_id)?.name ?? "-"}</TableCell>
        <TableCell className="font-bold tabular-nums"><span>{formatKz(invoice.quote_payable ?? invoice.amount)}</span>{invoice.quote_payable != null && <span className="block text-[10px] font-medium text-brand-600">{t("invoices.quote.providerTotal")}</span>}</TableCell>
        <TableCell><div className="flex flex-wrap items-center gap-1.5"><Badge variant="secondary">{t(`invoices.status.${invoice.status}`)}</Badge>{invoice.sync_status === "failed" && <Badge variant="destructive" title={invoice.last_sync_error ?? undefined}><AlertTriangle className="mr-1 size-3" />{t("invoices.sync.failed")}</Badge>}</div>{invoice.sync_status === "failed" && invoice.last_sync_error && <p className="mt-1 max-w-56 text-[11px] text-destructive">{invoice.last_sync_error}</p>}</TableCell>
        <TableCell className="max-w-52 truncate">{invoice.items?.[0]?.description ?? invoice.description ?? "-"}</TableCell>
        <TableCell className="pr-5"><div className="flex justify-end gap-2">
          {invoice.status === "draft" && hasPendingEmission(invoice) && <Button size="sm" variant="outline" disabled={busyId === invoice.id} onClick={() => setEmitTarget(invoice)}><RotateCw className="mr-1 size-3.5" />{t("invoices.actions.retry")}</Button>}
          {invoice.status === "draft" && !hasPendingEmission(invoice) && !hasValidQuote(invoice) && <Button size="sm" variant="outline" disabled={busyId === invoice.id} onClick={() => handlePreview(invoice.id)}><Calculator className="mr-1 size-3.5" />{t("invoices.actions.preview")}</Button>}
          {invoice.status === "draft" && !hasPendingEmission(invoice) && hasValidQuote(invoice) && <Button size="sm" variant="outline" disabled={busyId === invoice.id} onClick={() => setEmitTarget(invoice)}><Send className="mr-1 size-3.5" />{t("invoices.actions.send")}</Button>}
          {invoice.status === "draft" && !hasPendingEmission(invoice) && <Button size="icon-sm" variant="ghost" disabled={busyId === invoice.id} onClick={() => setCancelTarget(invoice)} aria-label={t("invoices.actions.cancel")}><X className="size-4" /></Button>}
          {invoice.status === "sent" && invoice.external_reference && <Button size="sm" variant="outline" disabled={busyId === invoice.id} onClick={() => runRowAction(invoice.id, () => invoicesApi.reconcile(invoice.id), "invoices.reconcileError")}><CheckCircle2 className="mr-1 size-3.5" />{t("invoices.actions.checkPayment")}</Button>}
          {invoice.document_url && <a href={invoice.document_url} target="_blank" rel="noreferrer" aria-label={t("invoices.actions.openDocument")} className="inline-flex size-7 items-center justify-center rounded-lg text-dark-500 hover:bg-dark-100"><ExternalLink className="size-4" /></a>}
        </div></TableCell>
      </TableRow>)}</TableBody>
    </Table>}<ListPagination page={page} total={total} onPageChange={setPage} /></CardContent></Card>

    <ConfirmDialog
      open={emitTarget !== null}
      onOpenChange={(open) => { if (!open) setEmitTarget(null); }}
      title={t(emitTarget && hasPendingEmission(emitTarget) ? "invoices.emit.retryTitle" : "invoices.emit.title")}
      description={t("invoices.emit.description")}
      confirmLabel={t(emitTarget && hasPendingEmission(emitTarget) ? "invoices.actions.retry" : "invoices.actions.send")}
      cancelLabel={t("common.cancel")}
      pending={emitTarget !== null && busyId === emitTarget.id}
      onConfirm={confirmEmission}
    >
      {emitTarget && <dl className="grid grid-cols-2 gap-2 rounded-xl bg-muted/50 p-3 text-sm">
        <dt className="text-muted-foreground">{t("invoices.table.owner")}</dt><dd className="text-right font-medium">{emitTarget.customer_name ?? "-"}</dd>
        <dt className="text-muted-foreground">{t("invoices.form.documentType")}</dt><dd className="text-right font-medium">{emitTarget.document_type}</dd>
        <dt className="text-muted-foreground">{t("invoices.quote.providerTotal")}</dt><dd className="text-right font-bold tabular-nums">{formatKz(emitTarget.quote_payable ?? emitTarget.amount)}</dd>
      </dl>}
    </ConfirmDialog>

    <FormDialog open={showForm} onOpenChange={setShowForm} size="2xl" title={t("invoices.new")} description={t("invoices.createHint")}>
      <form onSubmit={handleSubmit} className="space-y-6 p-6">
        <FormError message={formError} />
        <div className="grid gap-4 md:grid-cols-4">
          <div className="space-y-1.5 md:col-span-2"><Label htmlFor="invoice-owner">{t("invoices.form.owner")} *</Label><FormSelect id="invoice-owner" ariaLabel={t("invoices.form.owner")} value={form.owner_id || null} onValueChange={(value) => { setNifDraft(""); setForm((current) => ({ ...current, owner_id: Number(value), appointment_id: null })); }} onSearchChange={ownerSearch.onSearchChange} options={ownerOptions.map((item) => ({ value: item.id, label: item.nif ? `${item.name} · ${item.nif}` : item.name }))} placeholder={t("invoices.form.selectOwner")} required /></div>
          <div className="space-y-1.5"><Label htmlFor="invoice-appointment">{t("invoices.form.appointment")}</Label><FormSelect id="invoice-appointment" ariaLabel={t("invoices.form.appointment")} value={form.appointment_id} onValueChange={(value) => setForm((current) => ({ ...current, appointment_id: value ? Number(value) : null }))} options={[{ value: "", label: t("invoices.form.noAppointment") }, ...ownerAppointments.map((item) => ({ value: item.id, label: [parseApiDate(item.scheduled_at).toLocaleDateString("pt-AO", { timeZone: "Africa/Luanda" }), item.pet_name, item.reason].filter(Boolean).join(" · ") }))]} /></div>
          <div className="space-y-1.5"><Label htmlFor="invoice-document-type">{t("invoices.form.documentType")}</Label><FormSelect id="invoice-document-type" ariaLabel={t("invoices.form.documentType")} value={form.document_type} onValueChange={(value) => setForm((current) => ({ ...current, document_type: value as "FT" | "FR" }))} options={[{ value: "FT", label: t("invoices.documentType.FT") }, { value: "FR", label: t("invoices.documentType.FR") }]} /></div>
          {form.document_type === "FR" && <div className="space-y-1.5"><Label htmlFor="invoice-payment-method">{t("invoices.form.paymentMethod")}</Label><FormSelect id="invoice-payment-method" ariaLabel={t("invoices.form.paymentMethod")} value={form.payment_method} onValueChange={(value) => setForm((current) => ({ ...current, payment_method: value as PaymentMethod }))} options={(["cash", "bank-transfer", "tpa"] as PaymentMethod[]).map((value) => ({ value, label: t(`invoices.paymentMethod.${value}`) }))} />{form.payment_method === "cash" && <p className="text-xs text-amber-700">{t("invoices.form.cashSessionHint")}</p>}</div>}
        </div>
        {owner && !owner.nif && <div className="space-y-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"><p>{t("invoices.form.missingNif")}</p><div className="flex flex-wrap items-end gap-2"><div className="min-w-48 flex-1 space-y-1"><Label htmlFor="invoice-owner-nif" className="text-xs">{t("owners.form.nif")}</Label><Input id="invoice-owner-nif" value={nifDraft} maxLength={30} onChange={(event) => setNifDraft(event.target.value)} className="bg-white" /></div><Button type="button" variant="outline" disabled={savingNif || !nifDraft.trim()} onClick={saveOwnerNif}>{savingNif ? t("common.saving") : t("invoices.form.saveNif")}</Button></div></div>}
        <div className="space-y-3">
          <div className="flex items-center justify-between"><div><h3 className="font-bold text-dark-900">{t("invoices.form.items")}</h3><p className="text-xs text-dark-400">{t("invoices.form.itemsHint")}</p></div><Button type="button" size="sm" variant="outline" onClick={() => setForm((current) => ({ ...current, items: [...current.items, emptyLine()] }))}><Plus className="mr-1 size-3.5" />{t("invoices.form.addItem")}</Button></div>
          {form.items.map((item, index) => <div key={index} className="grid gap-3 rounded-xl border border-dark-100 bg-dark-50/50 p-4 md:grid-cols-2 lg:grid-cols-[110px_minmax(0,2fr)_80px_120px_140px_40px]">
            <div className="space-y-1"><Label htmlFor={`invoice-line-${index}-kind`}>{t("invoices.form.kind")}</Label><FormSelect id={`invoice-line-${index}-kind`} ariaLabel={t("invoices.form.kind")} value={item.kind} onValueChange={(value) => updateLine(index, { kind: value as "SERVICE" | "PRODUCT" })} options={[{ value: "SERVICE", label: t("invoices.lineKind.SERVICE") }, { value: "PRODUCT", label: t("invoices.lineKind.PRODUCT") }]} /></div>
            <div className="space-y-1"><Label htmlFor={`invoice-line-${index}-description`}>{t("invoices.form.description")}</Label><Input id={`invoice-line-${index}-description`} value={item.description} onChange={(event) => updateLine(index, { description: event.target.value })} required /></div>
            <div className="space-y-1"><Label htmlFor={`invoice-line-${index}-quantity`}>{t("invoices.form.quantity")}</Label><Input id={`invoice-line-${index}-quantity`} type="number" min="0.001" step="0.001" value={item.quantity} onChange={(event) => updateLine(index, { quantity: Number(event.target.value) })} required /></div>
            <div className="space-y-1"><Label htmlFor={`invoice-line-${index}-unit-price`}>{t("invoices.form.unitPrice")}</Label><Input id={`invoice-line-${index}-unit-price`} type="number" min="0" step="0.01" value={item.unit_price || ""} onChange={(event) => updateLine(index, { unit_price: Number(event.target.value) })} required /></div>
            <div className="space-y-1"><Label htmlFor={`invoice-line-${index}-vat-profile`}>{t("invoices.form.vatProfile")}</Label><Input id={`invoice-line-${index}-vat-profile`} value={item.vat_profile_code ?? ""} onChange={(event) => updateLine(index, { vat_profile_code: event.target.value || undefined })} placeholder={t("invoices.form.vatProfileDefault")} /></div>
            <Button type="button" size="icon-sm" variant="ghost" className="mt-6" aria-label={t("invoices.form.removeItem")} disabled={form.items.length === 1} onClick={() => setForm((current) => ({ ...current, items: current.items.filter((_, itemIndex) => itemIndex !== index) }))}><Trash2 className="size-4" /></Button>
          </div>)}
        </div>
        <div className="ml-auto w-full max-w-sm space-y-2 rounded-xl bg-dark-50 p-4 text-sm tabular-nums"><div className="flex justify-between text-lg"><span>{t("invoices.summary.commercialSubtotal")}</span><strong>{formatKz(subtotal)}</strong></div><p className="text-xs text-dark-500">{t("invoices.summary.providerTotalHint")}</p></div>
        <div className="flex justify-end gap-3 border-t border-dark-100 pt-4"><Button type="button" variant="outline" onClick={() => setShowForm(false)}>{t("common.cancel")}</Button><Button type="submit" disabled={saving || !owner?.nif || subtotal < 0}>{saving ? t("invoices.savingDraft") : t("invoices.saveDraft")}</Button></div>
      </form>
    </FormDialog>

    <PromptDialog
      open={cancelTarget !== null}
      onOpenChange={(open) => { if (!open) setCancelTarget(null); }}
      title={t("invoices.cancelTitle")}
      label={t("invoices.cancelReason")}
      confirmLabel={t("invoices.actions.cancel")}
      cancelLabel={t("common.back")}
      destructive
      pending={cancelTarget !== null && busyId === cancelTarget.id}
      onConfirm={confirmCancel}
    />
  </div>;
}
