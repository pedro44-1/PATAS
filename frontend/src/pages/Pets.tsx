import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { petsApi, Pet, PetCreate } from "@/api/pets";
import { ownersApi, Owner } from "@/api/owners";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormSelect } from "@/components/ui/form-select";
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
import { clinicDateInput } from "@/lib/date";
import { Plus, Pencil, Archive, Search, PawPrint, ChevronRight, X } from "lucide-react";

const SPECIES_OPTIONS = [
  { value: "Cão", label: "Cão", breeds: ["SRD", "Pastor Alemão", "Labrador", "Bulldog", "Rottweiler", "Golden Retriever", "Pitbull", "Beagle", "Dálmata", "Husky", "Boxer", "Poodle", "Chihuahua", "Bulldog Francês", "Cocker Spaniel", "Doberman", "Outro"] },
  { value: "Gato", label: "Gato", breeds: ["SRD", "Persa", "Siamês", "British Shorthair", "Maine Coon", "Ragdoll", "Bengal", "Scottish Fold", "Sphynx", "Russo Azul", "Angorá", "Burmês", "Bombay", "Exótico", "Outro"] },
  { value: "Ave", label: "Ave", breeds: ["Papagaio", "Canário", "Periquito", "Cacatua", "Agapornis", "Diamante de Gould", "Ninfas", "Arara", "Jandaia", "Lorículo", "Outro"] },
  { value: "Roedor", label: "Roedor", breeds: ["Hamster", "Porquinho-da-Índia", "Gerbil", "Rato", "Chinchila", "Fura-flor", "Esquilo", "Outro"] },
  { value: "Coelho", label: "Coelho", breeds: ["Anão", "Mini Lop", "Holandês", "Flemish Giant", "Lionhead", "Rex", "Califórnia", "Novo Zelandês", "Outro"] },
  { value: "Réptil", label: "Réptil", breeds: ["Dragão Barbudo", "Gecko", "Iguana", "Serpente", "Tartaruga", "Cágado", "Camaleão", "Teju", "Outro"] },
  { value: "Outro", label: "Outro", breeds: [] },
];

function calculateAge(birthDate: string | null, translate: (key: string, options?: Record<string, unknown>) => string): string {
  if (!birthDate) return "—";
  const birth = new Date(birthDate);
  const today = new Date();
  const totalMonths = (today.getFullYear() - birth.getFullYear()) * 12 + (today.getMonth() - birth.getMonth());
  if (totalMonths < 1) return translate("pets.age.lessThanMonth");
  if (totalMonths < 12) return translate("pets.age.months", { count: totalMonths });
  const years = Math.floor(totalMonths / 12);
  return translate("pets.age.years", { count: years });
}

function speciesEmoji(species: string) {
  const map: Record<string, string> = {
    Cão: "🐶", Gato: "🐱", Ave: "🐦", Roedor: "🐹",
    Coelho: "🐰", Réptil: "🦎", Outro: "🐾",
  };
  return map[species] ?? "🐾";
}

export default function Pets() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [pets, setPets] = useState<Pet[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Pet | null>(null);
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Form state
  const [form, setForm] = useState({
    owner_id: 0,
    name: "",
    species: "Cão",
    breed: "",
    birth_date: "",
    weight: "" as string | undefined,
  });

  function load() {
    setError("");
    Promise.all([petsApi.list(), ownersApi.list()])
      .then(([petsRes, ownersRes]) => {
        setPets(petsRes.data);
        setOwners(ownersRes.data);
      })
      .catch(() => setError(t("pets.error")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  const filtered = pets.filter((p) =>
    search === "" ||
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.species.toLowerCase().includes(search.toLowerCase()) ||
    (p.breed ?? "").toLowerCase().includes(search.toLowerCase())
  );

  const currentSpecies = SPECIES_OPTIONS.find((s) => s.value === form.species);
  const breedOptions = currentSpecies?.breeds ?? [];

  function openCreate() {
    setEditing(null);
    setForm({
      owner_id: owners[0]?.id ?? 0,
      name: "",
      species: "Cão",
      breed: "",
      birth_date: "",
      weight: undefined,
    });
    setShowForm(true);
  }

  function openEdit(pet: Pet) {
    setEditing(pet);
    setForm({
      owner_id: pet.owner_id,
      name: pet.name,
      species: pet.species,
      breed: pet.breed ?? "",
      birth_date: pet.birth_date ?? "",
      weight: pet.weight !== null ? String(pet.weight) : undefined,
    });
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload: PetCreate = {
        owner_id: form.owner_id,
        name: form.name,
        species: form.species,
        breed: form.breed || undefined,
        birth_date: form.birth_date || undefined,
        weight: form.weight ? Number(form.weight) : undefined,
      };
      if (editing) {
        await petsApi.update(editing.id, payload);
      } else {
        await petsApi.create(payload);
      }
      setShowForm(false);
      load();
    } catch {
      setError(t("pets.error"));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm(t("pets.archiveConfirm"))) return;
    try {
      await petsApi.delete(id);
      load();
    } catch {
      setError(t("pets.error"));
    }
  }

  function getOwnerName(id: number) {
    return owners.find((o) => o.id === id)?.name ?? "—";
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-dark-900">{t("pets.title")}</h2>
          <p className="text-dark-400 text-sm mt-0.5">
            {t("pets.count", { count: pets.length })}
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-brand-600 hover:bg-brand-700 font-semibold rounded-xl shadow-lg shadow-brand-600/20"
        >
          <Plus className="w-4 h-4 mr-2" />
          {t("pets.new")}
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
        <Input
          placeholder={t("pets.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10 h-11 rounded-xl bg-white border-dark-200"
        />
      </div>

      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-600/30 border-t-brand-600 rounded-full animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center py-16 text-dark-400">
              <PawPrint className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">{t("pets.noResults")}</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-b border-dark-100">
                  <TableHead className="pl-5">{t("pets.table.animal")}</TableHead>
                  <TableHead>{t("pets.table.speciesBreed")}</TableHead>
                  <TableHead>{t("pets.table.age")}</TableHead>
                  <TableHead>{t("pets.table.weight")}</TableHead>
                  <TableHead className="pr-5 w-48 text-right">{t("pets.table.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((p) => (
                  <TableRow
                    key={p.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/pets/${p.id}`)}
                  >
                    <TableCell className="pl-5">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center text-lg">
                          {speciesEmoji(p.species)}
                        </div>
                        <div>
                          <div className="font-semibold text-dark-900 text-sm">{p.name}</div>
                          <div className="text-dark-400 text-xs">{getOwnerName(p.owner_id)}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-sm text-dark-700">{p.species}</div>
                      <div className="text-dark-400 text-xs">{p.breed ?? "—"}</div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-dark-600">{calculateAge(p.birth_date, t)}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-dark-500">{p.weight ? `${p.weight} kg` : "—"}</span>
                    </TableCell>
                    <TableCell className="pr-5" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => navigate(`/pets/${p.id}`)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-semibold transition-colors"
                          title={t("pets.history")}
                        >
                          {t("pets.table.view")}
                          <ChevronRight className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => openEdit(p)}
                          title={t("common.edit")}
                          className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(p.id)}
                          title={t("common.archive")}
                          className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
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
        </CardContent>
      </Card>

      {/* Modal */}
      {showForm && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setShowForm(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="sticky top-0 bg-white border-b border-dark-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <div>
                <h2 className="font-bold text-dark-900">
                  {editing ? t("pets.edit") : t("pets.new")}
                </h2>
                <p className="text-dark-400 text-xs mt-0.5">
                  {editing ? t("pets.editing", { name: editing.name }) : t("pets.createHint")}
                </p>
              </div>
              <button
                onClick={() => setShowForm(false)}
                className="w-8 h-8 rounded-xl bg-dark-100 flex items-center justify-center text-dark-400 hover:text-dark-700 hover:bg-dark-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Owner */}
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">
                  {t("pets.form.owner")} *
                </Label>
                <FormSelect
                  value={form.owner_id || null}
                  onValueChange={(value) => setForm({ ...form, owner_id: Number(value) })}
                  options={owners.map((owner) => ({ value: owner.id, label: owner.name }))}
                  placeholder={t("pets.form.selectOwner")}
                  className="h-11 border-dark-200 bg-white"
                  required
                />
              </div>

              {/* Name + Species */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("pets.form.name")} *</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder={t("pets.form.namePlaceholder")}
                    required
                    className="h-11 rounded-xl"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("pets.form.species")} *</Label>
                  <FormSelect
                    value={form.species}
                    onValueChange={(value) => setForm({ ...form, species: value, breed: "" })}
                    options={SPECIES_OPTIONS.map(({ value }) => ({ value, label: t(`pets.species.${value}`) }))}
                    className="h-11 border-dark-200 bg-white"
                    required
                  />
                </div>
              </div>

              {/* Breed */}
              <div className="space-y-1.5">
                <Label className="text-xs font-semibold text-dark-600">
                  {t("pets.form.breed")} {breedOptions.length > 0 && `— ${t("pets.form.breedOptions", { count: breedOptions.length })}`}
                </Label>
                {breedOptions.length > 0 ? (
                  <FormSelect
                    value={form.breed}
                    onValueChange={(value) => setForm({ ...form, breed: value })}
                    options={[
                      { value: "", label: t("pets.form.selectBreed") },
                      ...breedOptions.map((breed) => ({ value: breed, label: breed })),
                    ]}
                    placeholder={t("pets.form.selectBreed")}
                    className="h-11 border-dark-200 bg-white"
                  />
                ) : (
                  <Input
                    value={form.breed}
                    onChange={(e) => setForm({ ...form, breed: e.target.value })}
                    placeholder={t("pets.form.breedPlaceholder")}
                    className="h-11 rounded-xl"
                  />
                )}
              </div>

              {/* Birth date + Weight */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">
                    {t("pets.form.birthDate")}
                  </Label>
                  <input
                    type="date"
                    value={form.birth_date}
                    max={clinicDateInput()}
                    onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
                    className="flex h-11 w-full rounded-xl border border-dark-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs font-semibold text-dark-600">{t("pets.form.weight")}</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    value={form.weight ?? ""}
                    onChange={(e) =>
                      setForm({ ...form, weight: e.target.value || undefined })
                    }
                    placeholder={t("pets.form.weightPlaceholder")}
                    className="h-11 rounded-xl"
                  />
                </div>
              </div>

              {/* Age display */}
              {form.birth_date && (
                <div className="bg-brand-50 border border-brand-200 rounded-xl px-4 py-3">
                  <p className="text-brand-700 text-sm font-semibold">
                    {t("pets.form.ageDisplay", { age: calculateAge(form.birth_date, t) })}
                  </p>
                  <p className="text-brand-600 text-xs mt-0.5">
                    {new Date(form.birth_date).toLocaleDateString("pt-AO", { year: "numeric", month: "long", day: "numeric" })}
                  </p>
                </div>
              )}

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
                    t("pets.saveChanges")
                  ) : (
                    t("pets.create")
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
