import { useEffect, useState } from "react";
import { invoicesApi, Invoice, InvoiceStatus } from "@/api/invoices";
import { ownersApi, Owner } from "@/api/owners";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

const STATUS_OPTIONS = [
  { value: "", label: "Todas" },
  { value: "draft", label: "Rascunho" },
  { value: "paid", label: "Pagas" },
  { value: "cancelled", label: "Canceladas" },
];

function statusConfig(status: InvoiceStatus) {
  if (status === "paid")
    return { label: "Paga", bg: "bg-brand-50", text: "text-brand-700", dot: "bg-brand-500" };
  if (status === "cancelled")
    return { label: "Cancelada", bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
  return { label: "Rascunho", bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
}

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  const [form, setForm] = useState({ owner_id: 0, amount: 0, description: "" });
  const [saving, setSaving] = useState(false);

  function load() {
    Promise.all([
      invoicesApi.list(filterStatus ? { status: filterStatus } : undefined),
      ownersApi.list(),
    ])
      .then(([iRes, oRes]) => {
        setInvoices(iRes.data);
        setOwners(oRes.data);
      })
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
    try {
      await invoicesApi.create({ ...form, amount: Number(form.amount) });
      setShowForm(false);
      load();
    } catch {} finally {
      setSaving(false);
    }
  }

  async function handleStatus(id: number, status: InvoiceStatus) {
    try {
      await invoicesApi.update(id, { status });
      load();
    } catch {}
  }

  async function handleDelete(id: number) {
    if (!confirm("Eliminar esta fatura?")) return;
    await invoicesApi.delete(id);
    load();
  }

  function getOwnerName(id: number) {
    return owners.find((o) => o.id === id)?.name ?? "—";
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">Faturas</h2>
          <p className="text-dark-400 text-sm mt-0.5">
            {invoices.length} factura{invoices.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="h-10 rounded-xl border border-dark-200 bg-white px-3 text-sm text-dark-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {STATUS_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <Button
            onClick={openCreate}
            className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
          >
            <Plus className="w-4 h-4 mr-2" />
            Nova Fatura
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
              Total pendente de cobrança
            </p>
            <p className="text-amber-600 text-xs">
              {pendingTotal.toLocaleString("pt-AO")} Kz em{" "}
              {invoices.filter((i) => i.status === "draft").length} factura
              {invoices.filter((i) => i.status === "draft").length !== 1 ? "s" : ""}{" "}
              não paga
            </p>
          </div>
          <span className="text-amber-800 font-extrabold text-lg">
            {pendingTotal.toLocaleString("pt-AO")} Kz
          </span>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : invoices.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <FileText className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">Nenhuma factura</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5 w-16">Nº</TableHead>
                  <TableHead>Dono</TableHead>
                  <TableHead>Valor</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Descrição</TableHead>
                  <TableHead className="pr-5 w-48 text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((inv) => {
                  const cfg = statusConfig(inv.status);
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
                        {inv.status === "draft" ? (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleStatus(inv.id, "paid")}
                              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors"
                              title="Marcar como paga"
                            >
                              <Check className="w-3.5 h-3.5" />
                              Paga
                            </button>
                            <button
                              onClick={() => handleStatus(inv.id, "cancelled")}
                              className="p-1.5 rounded-lg bg-dark-100 text-dark-500 hover:bg-dark-200 transition-colors"
                              title="Cancelar"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDelete(inv.id)}
                              className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                              title="Eliminar"
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
                <h2 className="font-bold text-dark-900">Nova Fatura</h2>
                <p className="text-dark-400 text-xs mt-0.5">Emitir uma nova fatura</p>
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
                <Label className="text-xs font-semibold text-dark-600">Dono *</Label>
                <select
                  value={form.owner_id}
                  onChange={(e) => setForm({ ...form, owner_id: Number(e.target.value) })}
                  className="flex h-11 w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  required
                >
                  <option value={0}>Selecionar dono</option>
                  {owners.map((o) => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Valor (Kz) *</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.amount || ""}
                  onChange={(e) => setForm({ ...form, amount: Number(e.target.value) })}
                  placeholder="2500"
                  required
                  className="h-11 rounded-xl"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">Descrição</Label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Descrição da factura"
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
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={saving}
                  className="bg-brand-600 hover:bg-brand-700 rounded-xl h-11 font-semibold"
                >
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      A emitir...
                    </span>
                  ) : "Emitir Fatura"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
