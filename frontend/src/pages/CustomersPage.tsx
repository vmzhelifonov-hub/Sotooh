import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { customerApi, type Customer } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Field, Input, Select, Textarea } from "../components/ui/Field";
import { Card, EmptyState, Pagination, Spinner, StatusBadge } from "../components/ui/DataDisplay";
import { Dialog } from "../components/ui/Dialog";
import { useToast } from "../providers/ToastProvider";
import "./customers.css";

const EMPTY_FORM: Partial<Customer> = {
  name: "",
  phone: "",
  secondary_phone: "",
  email: "",
  city: "",
  address: "",
  source: "whatsapp",
  stage: "new",
  notes: "",
};

export default function CustomersPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [stageFilter, setStageFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState<Partial<Customer>>(EMPTY_FORM);
  const [followUpFor, setFollowUpFor] = useState<Customer | null>(null);
  const [followUpDate, setFollowUpDate] = useState("");
  const [followUpNote, setFollowUpNote] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["customers", page, search, stageFilter],
    queryFn: () => customerApi.list({ page, search: search || undefined, stage: stageFilter || undefined }),
  });

  const { data: meta } = useQuery({ queryKey: ["customer-meta"], queryFn: customerApi.meta });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["customers"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!form.name?.trim() || !form.phone?.trim()) throw { response: { data: { error: { message: t("common.required") } } } };
      if (editing) return customerApi.update(editing.id, form);
      return customerApi.create(form);
    },
    onSuccess: () => {
      setDialogOpen(false);
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => customerApi.remove(id),
    onSuccess: () => {
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const completeFollowUpMutation = useMutation({
    mutationFn: (id: string) => customerApi.completeFollowUp(id),
    onSuccess: () => {
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const scheduleFollowUpMutation = useMutation({
    mutationFn: () => {
      if (!followUpFor || !followUpDate) throw { response: { data: { error: { message: t("common.required") } } } };
      return customerApi.scheduleFollowUp({
        customer: followUpFor.id,
        scheduled_for: new Date(followUpDate).toISOString(),
        note: followUpNote,
      });
    },
    onSuccess: () => {
      setFollowUpFor(null);
      setFollowUpNote("");
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const openEdit = (c: Customer) => {
    setEditing(c);
    setForm(c);
    setDialogOpen(true);
  };

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setDialogOpen(true);
  };

  const nowIso = new Date().toISOString().slice(0, 16);
  const isOverdue = (c: Customer) => c.next_follow_up && c.next_follow_up < nowIso;

  return (
    <AppShell>
      <div className="page-header">
        <h1>{t("customers.title")}</h1>
        <Button onClick={openCreate}>{t("customers.add")}</Button>
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
          value={stageFilter}
          onChange={(e) => {
            setStageFilter(e.target.value);
            setPage(1);
          }}
          className="filters-select"
        >
          <option value="">{t("common.status")}</option>
          {(meta?.stages ?? []).map((s) => (
            <option key={s.value} value={s.value}>
              {t(`customers.stages.${s.value}`)}
            </option>
          ))}
        </Select>
      </div>

      <Card>
        {isLoading ? (
          <Spinner label={t("common.loading")} />
        ) : !data || data.results.length === 0 ? (
          <EmptyState
            title={t("customers.empty")}
            action={<Button onClick={openCreate}>{t("customers.add")}</Button>}
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t("customers.name")}</th>
                    <th>{t("customers.phone")}</th>
                    <th>{t("customers.city")}</th>
                    <th>{t("customers.stage")}</th>
                    <th>{t("customers.next_followup")}</th>
                    <th>{t("common.actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((c) => (
                    <tr key={c.id}>
                      <td className="cell-strong">{c.name}</td>
                      <td dir="ltr">{c.phone}</td>
                      <td>{c.city || "—"}</td>
                      <td>
                        <StatusBadge status={c.stage} label={t(`customers.stages.${c.stage}`)} />
                      </td>
                      <td>
                        {c.next_follow_up ? (
                          <span className={isOverdue(c) ? "followup-overdue" : "followup-ok"}>
                            {new Date(c.next_follow_up).toLocaleString("ar-IQ", { dateStyle: "short", timeStyle: "short" })}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        <div className="row-actions">
                          <Button size="sm" variant="secondary" onClick={() => openEdit(c)}>
                            {t("common.edit")}
                          </Button>
                          {c.next_follow_up && (
                            <Button size="sm" variant="ghost" onClick={() => completeFollowUpMutation.mutate(c.id)}>
                              ✓
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" onClick={() => setFollowUpFor(c)}>
                            ◷
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => {
                              if (window.confirm(t("common.confirm_delete"))) deleteMutation.mutate(c.id);
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

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} title={editing ? t("common.edit") : t("customers.add")} wide>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            saveMutation.mutate();
          }}
        >
          <div className="form-grid">
            <Field label={t("customers.name")} id="c-name" required>
              <Input id="c-name" value={form.name ?? ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
            <Field label={t("customers.phone")} id="c-phone" required>
              <Input id="c-phone" dir="ltr" value={form.phone ?? ""} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </Field>
            <Field label={t("customers.phone2")} id="c-phone2">
              <Input
                id="c-phone2"
                dir="ltr"
                value={form.secondary_phone ?? ""}
                onChange={(e) => setForm({ ...form, secondary_phone: e.target.value })}
              />
            </Field>
            <Field label={t("customers.city")} id="c-city">
              <Input id="c-city" value={form.city ?? ""} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            </Field>
            <Field label={t("customers.source")} id="c-source">
              <Select id="c-source" value={form.source ?? "whatsapp"} onChange={(e) => setForm({ ...form, source: e.target.value })}>
                {(meta?.sources ?? []).map((s) => (
                  <option key={s.value} value={s.value}>
                    {t(`customers.sources.${s.value}`)}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t("customers.stage")} id="c-stage">
              <Select id="c-stage" value={form.stage ?? "new"} onChange={(e) => setForm({ ...form, stage: e.target.value })}>
                {(meta?.stages ?? []).map((s) => (
                  <option key={s.value} value={s.value}>
                    {t(`customers.stages.${s.value}`)}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          {form.stage === "lost" && (
            <Field label={t("customers.lost_reason")} id="c-lost" required>
              <Input id="c-lost" value={form.lost_reason ?? ""} onChange={(e) => setForm({ ...form, lost_reason: e.target.value })} />
            </Field>
          )}
          <Field label={t("customers.address")} id="c-addr">
            <Input id="c-addr" value={form.address ?? ""} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>
          <Field label={t("customers.notes")} id="c-notes">
            <Textarea id="c-notes" value={form.notes ?? ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </Field>
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

      <Dialog open={followUpFor !== null} onClose={() => setFollowUpFor(null)} title={t("customers.schedule_followup")}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            scheduleFollowUpMutation.mutate();
          }}
        >
          <Field label={t("customers.next_followup")} id="fu-date" required>
            <Input id="fu-date" type="datetime-local" dir="ltr" value={followUpDate} onChange={(e) => setFollowUpDate(e.target.value)} />
          </Field>
          <Field label={t("customers.followup_note")} id="fu-note">
            <Textarea id="fu-note" value={followUpNote} onChange={(e) => setFollowUpNote(e.target.value)} />
          </Field>
          <div className="dialog-actions">
            <Button type="button" variant="secondary" onClick={() => setFollowUpFor(null)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" loading={scheduleFollowUpMutation.isPending}>
              {t("common.save")}
            </Button>
          </div>
        </form>
      </Dialog>
    </AppShell>
  );
}
