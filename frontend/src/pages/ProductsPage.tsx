import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { productApi, type Product } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Field, Input, MoneyInput, Select } from "../components/ui/Field";
import { Card, EmptyState, Pagination, Spinner } from "../components/ui/DataDisplay";
import { Dialog } from "../components/ui/Dialog";
import { useToast } from "../providers/ToastProvider";
import "./products.css";

const CATEGORIES = [
  "solar_panel",
  "inverter",
  "battery",
  "mounting",
  "protection",
  "cable",
  "accessory",
  "installation",
  "service",
  "other",
];

const EMPTY: Partial<Product> = {
  name_ar: "",
  name_en: "",
  category: "solar_panel",
  brand: "",
  model: "",
  sku: "",
  cost_price: "0",
  selling_price: "",
  unit: "pcs",
  type: "product",
  active: true,
};

export default function ProductsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState<Partial<Product>>(EMPTY);

  const { data, isLoading } = useQuery({
    queryKey: ["products", page, search, categoryFilter],
    queryFn: () => productApi.list({ page, search: search || undefined, category: categoryFilter || undefined }),
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!form.name_ar?.trim() || !form.selling_price) {
        throw { response: { data: { error: { message: t("common.required") } } } };
      }
      const payload = { ...form, selling_price: form.selling_price ?? "0" };
      if (editing) return productApi.update(editing.id, payload);
      return productApi.create(payload as never);
    },
    onSuccess: () => {
      setDialogOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["products"] });
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["products"] });
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  return (
    <AppShell>
      <div className="page-header">
        <h1>{t("products.title")}</h1>
        <Button
          onClick={() => {
            setEditing(null);
            setForm(EMPTY);
            setDialogOpen(true);
          }}
        >
          {t("products.add")}
        </Button>
      </div>

      <div className="filters-row">
        <Input
          placeholder={t("common.search")}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="filters-search"
        />
        <Select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(1);
          }}
          className="filters-select"
        >
          <option value="">{t("products.category")}</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {t(`products.categories.${c}`)}
            </option>
          ))}
        </Select>
      </div>

      <Card>
        {isLoading ? (
          <Spinner label={t("common.loading")} />
        ) : !data || data.results.length === 0 ? (
          <EmptyState
            title={t("products.empty")}
            action={
              <Button
                onClick={() => {
                  setEditing(null);
                  setForm(EMPTY);
                  setDialogOpen(true);
                }}
              >
                {t("products.add")}
              </Button>
            }
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t("products.name_ar")}</th>
                    <th>{t("products.category")}</th>
                    <th>{t("products.brand")}</th>
                    <th>{t("products.cost")}</th>
                    <th>{t("products.price")}</th>
                    <th>{t("common.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((p) => (
                    <tr key={p.id}>
                      <td className="cell-strong">{p.name_ar}</td>
                      <td>{t(`products.categories.${p.category}`)}</td>
                      <td>{[p.brand, p.model].filter(Boolean).join(" ") || "—"}</td>
                      <td dir="ltr">{Number(p.cost_price).toLocaleString("en-US")}</td>
                      <td dir="ltr">{Number(p.selling_price).toLocaleString("en-US")}</td>
                      <td>
                        <div className="row-actions">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              setEditing(p);
                              setForm(p);
                              setDialogOpen(true);
                            }}
                          >
                            {t("common.edit")}
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => {
                              if (window.confirm(t("common.confirm_delete"))) deleteMutation.mutate(p.id);
                            }}
                          >
                            ✕
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={page}
              count={data.count}
              pageSize={data.page_size}
              onChange={setPage}
              labels={{ prev: t("common.prev"), next: t("common.next"), page: t("common.page") }}
            />
          </>
        )}
      </Card>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        title={editing ? t("common.edit") : t("products.add")}
        wide
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            saveMutation.mutate();
          }}
        >
          <div className="form-grid">
            <Field label={t("products.name_ar")} id="p-name-ar" required>
              <Input id="p-name-ar" value={form.name_ar ?? ""} onChange={(e) => setForm({ ...form, name_ar: e.target.value })} />
            </Field>
            <Field label={t("products.name_en")} id="p-name-en">
              <Input id="p-name-en" dir="ltr" value={form.name_en ?? ""} onChange={(e) => setForm({ ...form, name_en: e.target.value })} />
            </Field>
            <Field label={t("products.category")} id="p-cat">
              <Select id="p-cat" value={form.category ?? "solar_panel"} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {t(`products.categories.${c}`)}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t("products.type")} id="p-type">
              <Select id="p-type" value={form.type ?? "product"} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <option value="product">{t("products.types.product")}</option>
                <option value="service">{t("products.types.service")}</option>
              </Select>
            </Field>
            <Field label={t("products.brand")} id="p-brand">
              <Input id="p-brand" dir="ltr" value={form.brand ?? ""} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
            </Field>
            <Field label={t("products.model")} id="p-model">
              <Input id="p-model" dir="ltr" value={form.model ?? ""} onChange={(e) => setForm({ ...form, model: e.target.value })} />
            </Field>
            <Field label={t("products.sku")} id="p-sku">
              <Input id="p-sku" dir="ltr" value={form.sku ?? ""} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
            </Field>
            <Field label={t("products.unit")} id="p-unit">
              <Input id="p-unit" dir="ltr" value={form.unit ?? "pcs"} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
            </Field>
            <Field label={t("products.cost")} id="p-cost">
              <MoneyInput id="p-cost" value={form.cost_price ?? "0"} onChange={(e) => setForm({ ...form, cost_price: e.target.value })} />
            </Field>
            <Field label={t("products.price")} id="p-price" required>
              <MoneyInput
                id="p-price"
                value={form.selling_price ?? ""}
                onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
              />
            </Field>
            <Field label={t("products.warranty")} id="p-warranty">
              <Input
                id="p-warranty"
                type="number"
                min={0}
                dir="ltr"
                value={form.warranty_months ?? 0}
                onChange={(e) => setForm({ ...form, warranty_months: Number(e.target.value) })}
              />
            </Field>
          </div>
          <div className="dialog-actions">
            <Button type="button" variant="secondary" onClick={() => setDialogOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" loading={saveMutation.isPending}>
              {t("common.save")}
            </Button>
          </div>
        </form>
      </Dialog>
    </AppShell>
  );
}
