import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { customerApi, productApi, quoteApi } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Field, Input, MoneyInput, Select, Textarea, formatMoney } from "../components/ui/Field";
import { Card, EmptyState, Spinner, StatusBadge } from "../components/ui/DataDisplay";
import { useToast } from "../providers/ToastProvider";
import "./quoteDetail.css";

interface DraftItem {
  product: string | null;
  description: string;
  brand_model: string;
  quantity: string;
  unit: string;
  unit_price: string;
  discount_amount: string;
  display_order: number;
}

function newCustomItem(order: number): DraftItem {
  return {
    product: null,
    description: "",
    brand_model: "",
    quantity: "1",
    unit: "pcs",
    unit_price: "",
    discount_amount: "0",
    display_order: order,
  };
}

const EMPTY_DRAFT = {
  customer: "",
  valid_until: "",
  discount_amount: "0",
  discount_percent: "0",
  tax_percent: "0",
  notes_ar: "",
  payment_terms: "",
  delivery_terms: "",
};

/** Safe decimal math on strings — display only; backend is authoritative. */
function mul(a: string, b: string): number {
  const x = Number(a) || 0;
  const y = Number(b) || 0;
  return Math.round(x * y * 100) / 100;
}

export default function QuoteDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const isNew = id === "new";

  const [form, setForm] = useState({ ...EMPTY_DRAFT });
  const [items, setItems] = useState<DraftItem[]>(isNew ? [newCustomItem(0)] : []);
  const [shareUrl, setShareUrl] = useState("");
  const [pdfUrl, setPdfUrl] = useState("");

  const { data: existing, isLoading: isLoadingQuote } = useQuery({
    queryKey: ["quote", id],
    queryFn: () => quoteApi.get(id!),
    enabled: !isNew,
  });

  const { data: customers } = useQuery({
    queryKey: ["customers-all"],
    queryFn: () => customerApi.list({ page: 1, page_size: "100" } as never).then((r) => r.results),
  });

  const { data: products } = useQuery({
    queryKey: ["products-all"],
    queryFn: () => productApi.list({ page: 1 }).then((r) => r.results),
    enabled: isNew || existing?.status === "draft",
  });

  useEffect(() => {
    if (existing) {
      setForm({
        customer: existing.customer,
        valid_until: existing.valid_until ?? "",
        discount_amount: existing.discount_amount,
        discount_percent: existing.discount_percent,
        tax_percent: existing.tax_percent,
        notes_ar: existing.notes_ar,
        payment_terms: existing.payment_terms,
        delivery_terms: existing.delivery_terms,
      });
      setItems(
        existing.items.map((i) => ({
          product: i.product,
          description: i.description,
          brand_model: i.brand_model,
          quantity: i.quantity,
          unit: i.unit,
          unit_price: i.unit_price,
          discount_amount: i.discount_amount,
          display_order: i.display_order,
        }))
      );
      if (existing.share_enabled) setShareUrl(existing.share_url);
      if (existing.pdf_url) setPdfUrl(existing.pdf_url);
    }
  }, [existing]);

  const totals = useMemo(() => {
    const subtotal = items.reduce((acc, i) => acc + mul(i.quantity, i.unit_price) - (Number(i.discount_amount) || 0), 0);
    const roundedSubtotal = Math.max(0, Math.round(subtotal * 100) / 100);
    const discountPct = Number(form.discount_percent) || 0;
    const afterPct = roundedSubtotal * (1 - discountPct / 100);
    const tax = afterPct * ((Number(form.tax_percent) || 0) / 100);
    const total = afterPct + tax;
    return {
      subtotal: roundedSubtotal,
      total: Math.max(0, Math.round(total * 100) / 100),
    };
  }, [items, form.discount_percent, form.tax_percent]);

  const invalidate = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ["quotes"] });
    void queryClient.invalidateQueries({ queryKey: ["quote", id] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }, [queryClient, id]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        customer: form.customer,
        valid_until: form.valid_until || null,
        discount_amount: form.discount_amount,
        discount_percent: form.discount_percent,
        tax_percent: form.tax_percent,
        notes_ar: form.notes_ar,
        payment_terms: form.payment_terms,
        delivery_terms: form.delivery_terms,
        items: items.map((i, idx) => ({ ...i, display_order: idx })),
      };
      if (!payload.customer || items.length === 0) {
        throw { response: { data: { error: { message: t("common.required") } } } };
      }
      if (isNew) {
        return quoteApi.create(payload);
      }
      return quoteApi.update(id!, payload);
    },
    onSuccess: (saved) => {
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
      if (isNew) navigate(`/app/quotes/${saved.id}`, { replace: true });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const pdfMutation = useMutation({
    mutationFn: () => quoteApi.generatePdf(id!),
    onSuccess: (res) => {
      setPdfUrl(res.pdf_url);
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const shareMutation = useMutation({
    mutationFn: () => quoteApi.share(id!),
    onSuccess: (res) => {
      setShareUrl(res.share_url);
      invalidate();
      toast({ kind: "success", message: t("quotes.share_created") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const revokeMutation = useMutation({
    mutationFn: () => quoteApi.revokeShare(id!),
    onSuccess: () => {
      setShareUrl("");
      invalidate();
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const statusMutation = useMutation({
    mutationFn: ({ status, lost_reason }: { status: string; lost_reason?: string }) =>
      quoteApi.setStatus(id!, status, lost_reason),
    onSuccess: () => {
      invalidate();
      toast({ kind: "success", message: t("settings.saved") });
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const duplicateMutation = useMutation({
    mutationFn: () => quoteApi.duplicate(id!),
    onSuccess: (created) => {
      invalidate();
      navigate(`/app/quotes/${created.id}`);
    },
    onError: (err) => toast({ kind: "error", message: extractApiError(err).message }),
  });

  const setItem = (index: number, patch: Partial<DraftItem>) => {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  };

  const onProductSelect = (index: number, productId: string) => {
    const p = products?.find((x) => x.id === productId);
    if (!p) {
      setItem(index, { product: null });
      return;
    }
    setItem(index, {
      product: p.id,
      description: p.name_ar,
      brand_model: [p.brand, p.model].filter(Boolean).join(" "),
      unit: p.unit,
      unit_price: p.selling_price,
    });
  };

  const moveItem = (index: number, dir: -1 | 1) => {
    setItems((prev) => {
      const next = [...prev];
      const target = index + dir;
      if (target < 0 || target >= next.length) return prev;
      const tmp = next[index];
      next[index] = next[target]!;
      next[target] = tmp!;
      return next.map((it, i) => ({ ...it, display_order: i }));
    });
  };

  const whatsappHref = useMemo(() => {
    if (!existing || !shareUrl) return null;
    const message = `مرحباً ${existing.customer_name}،\n${existing.quote_number}\n${shareUrl}`;
    return `https://wa.me/${existing.customer_phone.replace(/[^\d]/g, "")}?text=${encodeURIComponent(message)}`;
  }, [existing, shareUrl]);

  if (!isNew && isLoadingQuote) {
    return (
      <AppShell>
        <Spinner label={t("common.loading")} />
      </AppShell>
    );
  }

  if (!isNew && !existing) {
    return (
      <AppShell>
        <EmptyState title={t("common.no_results")} />
      </AppShell>
    );
  }

  const isDraft = isNew || existing?.status === "draft";
  const status = existing?.status ?? "draft";

  return (
    <AppShell>
      <div className="page-header">
        <div className="quote-title-row">
          <h1 dir="ltr">{existing?.quote_number ?? t("quotes.add")}</h1>
          {!isNew && <StatusBadge status={status} label={t(`quotes.statuses.${status}`)} />}
        </div>
        <div className="quote-header-actions">
          {!isNew && isDraft && (
            <Button variant="secondary" onClick={() => statusMutation.mutate({ status: "sent" })} disabled={statusMutation.isPending}>
              {t("quotes.mark_sent")}
            </Button>
          )}
          {!isNew && (status === "sent" || status === "accepted") && (
            <>
              <Button variant="gold" onClick={() => statusMutation.mutate({ status: "won" })}>
                {t("quotes.mark_won")}
              </Button>
              <Button variant="danger" onClick={() => statusMutation.mutate({ status: "lost", lost_reason: "—" })}>
                {t("quotes.mark_lost")}
              </Button>
            </>
          )}
          {!isNew && !isDraft && (
            <Button variant="secondary" onClick={() => duplicateMutation.mutate()} disabled={duplicateMutation.isPending}>
              {t("quotes.duplicate")}
            </Button>
          )}
          {isDraft && (
            <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
              {t("quotes.save_draft")}
            </Button>
          )}
        </div>
      </div>

      {!isDraft && (
        <div className="frozen-note">🔒 {t("quotes.only_draft_editable")}</div>
      )}

      <div className="quote-layout">
        <Card className="quote-main">
          <div className="form-grid">
            <Field label={t("quotes.customer")} id="q-customer" required>
              <Select
                id="q-customer"
                value={form.customer}
                disabled={!isDraft}
                onChange={(e) => setForm({ ...form, customer: e.target.value })}
              >
                <option value="">{t("quotes.select_customer")}</option>
                {(customers ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} — {c.phone}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t("quotes.valid_until")} id="q-valid">
              <Input
                id="q-valid"
                type="date"
                dir="ltr"
                value={form.valid_until}
                disabled={!isDraft}
                onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
              />
            </Field>
          </div>

          <h3 className="items-heading">{t("quotes.items")}</h3>
          {items.map((item, idx) => (
            <div className="quote-item" key={idx}>
              <div className="quote-item__row">
                <div className="quote-item__product">
                  {isDraft && (
                    <Select value={item.product ?? ""} onChange={(e) => onProductSelect(idx, e.target.value)} aria-label={t("quotes.select_product")}>
                      <option value="">{t("quotes.add_item")}</option>
                      {(products ?? []).map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name_ar} ({formatMoney(p.selling_price)})
                        </option>
                      ))}
                    </Select>
                  )}
                  <Input
                    placeholder={t("quotes.description")}
                    value={item.description}
                    disabled={!isDraft}
                    onChange={(e) => setItem(idx, { description: e.target.value })}
                  />
                  <Input
                    placeholder={t("quotes.brand_model")}
                    value={item.brand_model}
                    disabled={!isDraft}
                    dir="ltr"
                    onChange={(e) => setItem(idx, { brand_model: e.target.value })}
                  />
                </div>
                <div className="quote-item__nums">
                  <Input
                    type="number"
                    min="0"
                    step="any"
                    aria-label={t("quotes.quantity")}
                    value={item.quantity}
                    disabled={!isDraft}
                    dir="ltr"
                    onChange={(e) => setItem(idx, { quantity: e.target.value })}
                  />
                  <Input
                    aria-label={t("quotes.unit")}
                    value={item.unit}
                    disabled={!isDraft}
                    onChange={(e) => setItem(idx, { unit: e.target.value })}
                  />
                  <MoneyInput
                    aria-label={t("quotes.unit_price")}
                    value={item.unit_price}
                    disabled={!isDraft}
                    onChange={(e) => setItem(idx, { unit_price: e.target.value })}
                  />
                  <div className="quote-item__total" dir="ltr">
                    {formatMoney(mul(item.quantity, item.unit_price) - (Number(item.discount_amount) || 0))}
                  </div>
                  {isDraft && (
                    <div className="quote-item__ops">
                      <Button size="sm" variant="ghost" onClick={() => moveItem(idx, -1)} aria-label="↑">↑</Button>
                      <Button size="sm" variant="ghost" onClick={() => moveItem(idx, 1)} aria-label="↓">↓</Button>
                      <Button size="sm" variant="danger" onClick={() => setItems(items.filter((_, i) => i !== idx))} aria-label="✕">✕</Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isDraft && (
            <Button variant="secondary" size="sm" onClick={() => setItems([...items, newCustomItem(items.length)])}>
              + {t("quotes.add_custom")}
            </Button>
          )}

          <div className="form-grid quote-terms">
            <Field label={t("quotes.notes_ar")} id="q-notes">
              <Textarea id="q-notes" value={form.notes_ar} disabled={!isDraft} onChange={(e) => setForm({ ...form, notes_ar: e.target.value })} />
            </Field>
            <Field label={t("quotes.payment_terms")} id="q-pay">
              <Textarea id="q-pay" value={form.payment_terms} disabled={!isDraft} onChange={(e) => setForm({ ...form, payment_terms: e.target.value })} />
            </Field>
            <Field label={t("quotes.delivery_terms")} id="q-del">
              <Textarea id="q-del" value={form.delivery_terms} disabled={!isDraft} onChange={(e) => setForm({ ...form, delivery_terms: e.target.value })} />
            </Field>
          </div>
        </Card>

        <div className="quote-side">
          <Card>
            <h3 className="totals-heading">{t("quotes.total")}</h3>
            <div className="totals-row">
              <span>{t("quotes.subtotal")}</span>
              <strong dir="ltr">{formatMoney(totals.subtotal)}</strong>
            </div>
            {isDraft && (
              <div className="totals-inputs">
                <Field label={t("quotes.discount")} id="q-disc">
                  <MoneyInput value={form.discount_amount} onChange={(e) => setForm({ ...form, discount_amount: e.target.value || "0" })} />
                </Field>
                <Field label={t("quotes.discount_percent")} id="q-discp">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    dir="ltr"
                    value={form.discount_percent}
                    onChange={(e) => setForm({ ...form, discount_percent: e.target.value })}
                  />
                </Field>
                <Field label={t("quotes.tax_percent")} id="q-tax">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    dir="ltr"
                    value={form.tax_percent}
                    onChange={(e) => setForm({ ...form, tax_percent: e.target.value })}
                  />
                </Field>
              </div>
            )}
            <div className="totals-row totals-grand">
              <span>{t("quotes.total")}</span>
              <strong dir="ltr">{formatMoney(totals.total)}</strong>
            </div>
          </Card>

          {!isNew && (
            <Card>
              <h3 className="totals-heading">{t("quotes.share")}</h3>
              {shareUrl ? (
                <>
                  <div className="share-url" dir="ltr">{shareUrl}</div>
                  <div className="share-actions">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => {
                        void navigator.clipboard.writeText(shareUrl);
                        toast({ kind: "success", message: t("quotes.link_copied") });
                      }}
                    >
                      {t("quotes.copy_link")}
                    </Button>
                    <a href={shareUrl} target="_blank" rel="noreferrer">
                      <Button size="sm" variant="ghost">{t("quotes.open_public")}</Button>
                    </a>
                    <Button size="sm" variant="danger" onClick={() => revokeMutation.mutate()}>
                      {t("quotes.revoke_link")}
                    </Button>
                  </div>
                  {whatsappHref && (
                    <a href={whatsappHref} target="_blank" rel="noreferrer" className="wa-btn">
                      <Button variant="gold" size="md">{t("quotes.share_whatsapp")} ✆</Button>
                    </a>
                  )}
                  {existing && existing.view_count > 0 && (
                    <div className="views-meta">
                      👁 {existing.view_count} {t("quotes.views")}
                      {existing.first_viewed_at && (
                        <div>
                          {t("quotes.first_viewed")}: {new Date(existing.first_viewed_at).toLocaleString("ar-IQ")}
                        </div>
                      )}
                      {existing.last_viewed_at && (
                        <div>
                          {t("quotes.last_viewed")}: {new Date(existing.last_viewed_at).toLocaleString("ar-IQ")}
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <Button onClick={() => shareMutation.mutate()} loading={shareMutation.isPending}>
                  {t("quotes.share")}
                </Button>
              )}
            </Card>
          )}

          {!isNew && (
            <Card>
              <h3 className="totals-heading">PDF</h3>
              {pdfUrl ? (
                <a href={pdfUrl} target="_blank" rel="noreferrer">
                  <Button variant="secondary">{t("quotes.download_pdf")} ⎙</Button>
                </a>
              ) : (
                <Button onClick={() => pdfMutation.mutate()} loading={pdfMutation.isPending}>
                  {t("quotes.generate_pdf")}
                </Button>
              )}
            </Card>
          )}
        </div>
      </div>
    </AppShell>
  );
}
