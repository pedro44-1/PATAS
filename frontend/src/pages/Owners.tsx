import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { FormDialog } from "@/components/ui/form-dialog";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useToast } from "@/contexts/ToastContext";
import { ownersApi, Owner, OwnerCreate } from "@/api/owners";
import { apiErrorMessage } from "@/api/errors";
import { PAGE_SIZE, totalCount } from "@/api/pagination";
import { ListPagination } from "@/components/ListPagination";
import { useDebouncedValue } from "@/lib/use-debounced-value";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormError } from "@/components/ui/form-error";
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
import { Archive, Plus, Pencil, Phone, Mail, MapPin, Search } from "lucide-react";

export default function Owners() {
  const { t } = useTranslation();
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Owner | null>(null);
  const [form, setForm] = useState<OwnerCreate>({
    name: "",
    phone: "",
    email: "",
    address: "",
    nif: "",
    notes: "",
  });
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search.trim());
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [archiveTarget, setArchiveTarget] = useState<Owner | null>(null);
  const [archiving, setArchiving] = useState(false);
  const toast = useToast();

  function load() {
    setLoading(true);
    ownersApi.list({ q: debouncedSearch || undefined, skip: page * PAGE_SIZE, limit: PAGE_SIZE })
      .then((r) => {
        setOwners(r.data);
        setTotal(totalCount(r));
      })
      .catch((requestError: unknown) => setError(apiErrorMessage(requestError, t, "owners.error")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [debouncedSearch, page]);

  function openCreate() {
    setEditing(null);
    setForm({ name: "", phone: "", email: "", address: "", nif: "", notes: "" });
    setFormError("");
    setShowForm(true);
  }

  function openEdit(owner: Owner) {
    setEditing(owner);
    setForm({
      name: owner.name,
      phone: owner.phone ?? "",
      email: owner.email ?? "",
      address: owner.address ?? "",
      nif: owner.nif ?? "",
      notes: owner.notes ?? "",
    });
    setFormError("");
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      if (editing) {
        await ownersApi.update(editing.id, form);
      } else {
        await ownersApi.create(form);
      }
      setShowForm(false);
      toast.success(t(editing ? "owners.updated" : "owners.created"));
      load();
    } catch (requestError: unknown) {
      setFormError(apiErrorMessage(requestError, t, "owners.error"));
    } finally {
      setSaving(false);
    }
  }

  async function confirmArchive() {
    if (!archiveTarget) return;
    setArchiving(true);
    try {
      await ownersApi.delete(archiveTarget.id);
      toast.success(t("owners.archived", { name: archiveTarget.name }));
      setArchiveTarget(null);
      load();
    } catch (requestError: unknown) {
      toast.error(apiErrorMessage(requestError, t, "owners.error"));
    } finally {
      setArchiving(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">{t("owners.title")}</h2>
          <p className="text-dark-400 text-sm mt-0.5">{t("owners.count", { count: total })}</p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
        >
          <Plus className="w-4 h-4 mr-2" />
          {t("owners.new")}
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
        <Input
          placeholder={t("owners.search")}
          aria-label={t("owners.search")}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          className="pl-10 h-11 rounded-xl bg-white border-dark-200"
        />
      </div>
      {error && <div role="alert" className="rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : owners.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <p className="text-sm font-medium">{t("owners.noResults")}</p>
              {search && (
                <button
                  onClick={() => {
                    setSearch("");
                    setPage(0);
                  }}
                  className="mt-2 text-xs text-brand-600 hover:text-brand-700 font-semibold"
                >
                  {t("owners.clearSearch")}
                </button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5">{t("owners.table.name")}</TableHead>
                  <TableHead>{t("owners.table.phone")}</TableHead>
                  <TableHead>{t("owners.table.email")}</TableHead>
                  <TableHead>{t("owners.table.address")}</TableHead>
                  <TableHead className="pr-5 w-36 text-right">{t("owners.table.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {owners.map((o) => (
                  <TableRow key={o.id}>
                    <TableCell className="pl-5 font-semibold text-dark-900 text-sm">
                      {o.name}
                    </TableCell>
                    <TableCell>
                      {o.phone ? (
                        <span className="flex items-center gap-1.5 text-sm text-dark-600">
                          <Phone className="w-3.5 h-3.5 text-dark-400" />
                          {o.phone}
                        </span>
                      ) : (
                        <span className="text-dark-300 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {o.email ? (
                        <span className="flex items-center gap-1.5 text-sm text-dark-600">
                          <Mail className="w-3.5 h-3.5 text-dark-400" />
                          {o.email}
                        </span>
                      ) : (
                        <span className="text-dark-300 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {o.address ? (
                        <span className="flex items-center gap-1.5 text-sm text-dark-600">
                          <MapPin className="w-3.5 h-3.5 text-dark-400 flex-shrink-0" />
                          <span className="truncate max-w-40">{o.address}</span>
                        </span>
                      ) : (
                        <span className="text-dark-300 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell className="pr-5">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => openEdit(o)}
                          className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
                          aria-label={t("owners.editNamed", { name: o.name })}
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setArchiveTarget(o)}
                          className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                          aria-label={t("owners.archiveNamed", { name: o.name })}
                        >
                          <Archive className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <ListPagination page={page} total={total} onPageChange={setPage} />
        </CardContent>
      </Card>

      <FormDialog
        open={showForm}
        onOpenChange={setShowForm}
        title={t(editing ? "owners.edit" : "owners.new")}
        description={editing ? t("owners.editing", { name: editing.name }) : t("owners.createHint")}
      >
            {/* Modal body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <FormError message={formError} />
              <div className="space-y-1.5">
                <Label htmlFor="owner-name" className="text-xs font-semibold text-dark-600">{t("owners.form.name")} *</Label>
                <Input
                  id="owner-name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder={t("owners.form.name")}
                  required
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="owner-phone" className="text-xs font-semibold text-dark-600">{t("owners.form.phone")}</Label>
                <Input
                  id="owner-phone"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  placeholder={t("owners.form.phonePlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="owner-email" className="text-xs font-semibold text-dark-600">{t("owners.form.email")}</Label>
                <Input
                  id="owner-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder={t("owners.form.emailPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="owner-address" className="text-xs font-semibold text-dark-600">{t("owners.form.address")}</Label>
                <Input
                  id="owner-address"
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  placeholder={t("owners.form.addressPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="owner-nif" className="text-xs font-semibold text-dark-600">{t("owners.form.nif")}</Label>
                <Input
                  id="owner-nif"
                  value={form.nif}
                  onChange={(e) => setForm({ ...form, nif: e.target.value })}
                  placeholder={t("owners.form.nifPlaceholder")}
                  maxLength={30}
                  className="h-11 rounded-xl"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="owner-notes" className="text-xs font-semibold text-dark-600">{t("owners.form.notes")}</Label>
                <Input
                  id="owner-notes"
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder={t("owners.form.notesPlaceholder")}
                  className="h-11 rounded-xl"
                />
              </div>

              {/* Modal footer */}
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
                      {t("common.saving")}
                    </span>
                  ) : editing ? (
                    t("owners.saveChanges")
                  ) : (
                    t("owners.create")
                  )}
                </Button>
              </div>
            </form>
      </FormDialog>

      <ConfirmDialog
        open={archiveTarget !== null}
        onOpenChange={(open) => { if (!open) setArchiveTarget(null); }}
        title={t("owners.archiveTitle")}
        description={archiveTarget ? t("owners.archiveConfirm", { name: archiveTarget.name }) : undefined}
        confirmLabel={t("common.archive")}
        cancelLabel={t("common.cancel")}
        destructive
        pending={archiving}
        onConfirm={confirmArchive}
      />
    </div>
  );
}
