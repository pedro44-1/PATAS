import { useEffect, useState } from "react";
import { invoicesApi, Invoice, InvoiceStatus } from "@/api/invoices";
import { ownersApi, Owner } from "@/api/owners";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { Plus, FileText, Check, X } from "lucide-react";

function statusConfig(status: InvoiceStatus, label: string) {
  if (status === "sent")
    return { label, bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" };
  if (status === "paid")
    return { label, bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" };
  if (status === "cancelled")
    return { label, bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
  return { label, bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
}

export default function Invoices() {
  const { t } = useTranslation();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  const [form, setForm] = useState({ owner_id: 0, amount: 0, description: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const statusOptions = ["", "draft", "sent", "paid", "cancelled"];

  function load() {
    setError("");
    Promise.all([
      invoicesApi.list(filterStatus ? { status: filterStatus } : undefined),
      ownersApi.list(),
    ])
      .then(([iRes, oRes]) => {
        setInvoices(iRes.data);
        setOwners(oRes.data);
      })
      .catch(() => setError(t("invoices.error")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [filterStatus]);

  const pendingTotal = invoices
    .filter((i) => i.status === "draft")
    .reduce((sum, i) => sum + i.amount, 0);

  function openCreate() {
    setForm({ owner_id: owners[0]?.id ?? 0, amount: 0, description: "" });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await invoicesApi.create({ ...form, amount: Number(form.amount) });
      setShowForm(false);
      load();
    } catch {
      setError(t("invoices.error"));
    } finally {
      setSaving(false);
    }
  }

  async function handleStatus(id: number, status: InvoiceStatus) {
    try {
      const reason = status === "cancelled" ? window.prompt(t("invoices.cancelReason")) ?? "" : undefined;
      if (status === "cancelled" && !reason?.trim()) return;
      await invoicesApi.update(id, { status, reason });
      load();
    } catch {
      setError(t("invoices.error"));
    }
  }

  async function handleSync(id: number) {
    try {
      await invoicesApi.sync(id);
      load();
    } catch {
      setError(t("invoices.error"));
    }
  }

  function getOwnerName(id: number) {
    return owners.find((o) => o.id === id)?.name ?? "—";
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">{t("invoices.title")}</h2>
          <p className="text-dark-400 text-sm mt-0.5">
            {t("invoices.count", { count: invoices.length })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <FormSelect
            value={filterStatus}
            onValueChange={setFilterStatus}
            options={statusOptions.map((value) => ({ value, label: t(`invoices.filter.${value || "all"}`) }))}
            className="w-auto min-w-36 border-dark-200 bg-white text-dark-700"
          />
          <Button
            onClick={openCreate}
            className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t("invoices.new")}
          </Button>
        </div>
      </div>

      {/* Pending alert */}
      {pendingTotal > 0 && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-amber-50 border border-amber-200">
          <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-base flex-shrink-0">
            📄
          </div>
          <div className="flex-1">
            <p className="text-amber-800 text-sm font-semibold">
              {t("invoices.pendingAlert.label")}
            </p>
            <p className="text-amber-600 text-xs">
              {t("invoices.pendingAlert.hint", {
                amount: pendingTotal.toLocaleString("pt-AO"),
                count: invoices.filter((i) => i.status === "draft").length,
              })}
            </p>
          </div>
          <span className="text-amber-800 font-extrabold text-lg">
            {pendingTotal.toLocaleString("pt-AO")} Kz
          </span>
        </div>
      )}

      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : invoices.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <FileText className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">{t("invoices.noResults")}</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5 w-16">{t("invoices.table.number")}</TableHead>
                  <TableHead>{t("invoices.table.owner")}</TableHead>
                  <TableHead>{t("invoices.table.value")}</TableHead>
                  <TableHead>{t("invoices.table.status")}</TableHead>
                  <TableHead>{t("invoices.table.description")}</TableHead>
                  <TableHead className="pr-5 w-48 text-right">{t("invoices.table.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((inv) => {
                  const cfg = statusConfig(inv.status, t(`invoices.status.${inv.status}`));
                  return (
                    <TableRow key={inv.id}>
                      <TableCell className="pl-5">
                        <span className="font-bold text-sm text-dark-500">#{inv.id}</span>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium text-sm text-dark-900">
                          {getOwnerName(inv.owner_id)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="font-bold text-sm text-dark-900">
                          {inv.amount.toLocaleString("pt-AO")} Kz
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold",
                            cfg.bg,
                            cfg.text
                          )}
                        >
                          <span className={cn("w-1.5 h-1.5 rounded-full", cfg.dot)} />
                          {cfg.label}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-dark-500 max-w-40 block truncate">
                          {inv.description ?? "—"}
                        </span>
                      </TableCell>
                      <TableCell className="pr-5">
                        {inv.status === "draft" || inv.status === "sent" ? (
                          <div className="flex justify-end gap-2">
                            {inv.status === "draft" && <button
                              onClick={() => handleSync(inv.id)}
                              className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold transition-colors"
                              title={t("invoices.actions.sendHint")}
                            >
                              {t("invoices.actions.send")}
                            </button>}
                            {inv.status === "draft" && <button
                              onClick={() => handleStatus(inv.id, "paid")}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors"
                              title={t("invoices.actions.markPaidHint")}
                            >
                              <Check className="w-3.5 h-3.5" />
                              {t("invoices.actions.markPaid")}
                            </button>}
                            <button
                              onClick={() => handleStatus(inv.id, "cancelled")}
                              className="p-1.5 rounded-lg bg-dark-100 text-dark-500 hover:bg-dark-200 transition-colors"
                              title={t("common.cancel")}
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <span className="text-dark-300 text-xs">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {showForm && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setShowForm(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="sticky top-0 bg-white border-b border-dark-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <div>
                <h2 className="font-bold text-dark-900">{t("invoices.new")}</h2>
                <p className="text-dark-400 text-xs mt-0.5">{t("invoices.createHint")}</p>
              </div>
              <button
                onClick={() => setShowForm(false)}
                className="w-8 h-8 rounded-xl bg-dark-100 flex items-center justify-center text-dark-400 hover:text-dark-700 hover:bg-dark-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("invoices.form.owner")} *</Label>
                <FormSelect
                  value={form.owner_id || null}
                  onValueChange={(value) => setForm({ ...form, owner_id: Number(value) })}
                  options={owners.map((owner) => ({ value: owner.id, label: owner.name }))}
                  placeholder={t("invoices.form.selectOwner")}
                  className="h-11 border-dark-200 bg-white"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("invoices.form.amount")} *</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.amount || ""}
                  onChange={(e) => setForm({ ...form, amount: Number(e.target.value) })}
                  placeholder={t("invoices.form.amountPlaceholder")}
                  required
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">{t("invoices.form.description")}</Label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder={t("invoices.form.descriptionPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-dark-100">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForm(false)}
                  className="rounded-xl h-11"
                >
                  {t("common.cancel")}
                </Button>
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-brand-600 hover:bg-brand-700 rounded-xl h-11 font-semibold"
                >
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      {t("invoices.issuing")}
                    </span>
                  ) : t("invoices.issue")}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
