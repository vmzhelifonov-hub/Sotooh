import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { quoteApi } from "../api/endpoints";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Input, Select } from "../components/ui/Field";
import { Card, EmptyState, Pagination, Spinner, StatusBadge } from "../components/ui/DataDisplay";
import { formatMoney } from "../components/ui/Field";
import { useAuth } from "../providers/AuthProvider";
import "./customers.css";

const STATUSES = ["draft", "sent", "accepted", "rejected", "expired", "won", "lost"];

export default function QuotesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["quotes", page, search, statusFilter],
    queryFn: () => quoteApi.list({ page, search: search || undefined, status: statusFilter || undefined }),
  });

  const canCreate = user?.role === "owner" || user?.role === "member";

  return (
    <AppShell>
      <div className="page-header">
        <h1>{t("quotes.title")}</h1>
        {canCreate && <Button onClick={() => navigate("/app/quotes/new")}>{t("quotes.add")}</Button>}
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
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="filters-select"
        >
          <option value="">{t("common.status")}</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {t(`quotes.statuses.${s}`)}
            </option>
          ))}
        </Select>
      </div>

      <Card>
        {isLoading ? (
          <Spinner label={t("common.loading")} />
        ) : !data || data.results.length === 0 ? (
          <EmptyState
            title={t("quotes.empty")}
            action={<Button onClick={() => navigate("/app/quotes/new")}>{t("quotes.add")}</Button>}
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t("quotes.number")}</th>
                    <th>{t("quotes.customer")}</th>
                    <th>{t("quotes.total")}</th>
                    <th>{t("common.status")}</th>
                    <th>{t("quotes.share")}</th>
                    <th>{t("common.date")}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((q) => (
                    <tr key={q.id}>
                      <td>
                        <Link to={`/app/quotes/${q.id}`} className="quote-link" dir="ltr">
                          {q.quote_number}
                        </Link>
                      </td>
                      <td className="cell-strong">{q.customer_name}</td>
                      <td dir="ltr">{formatMoney(q.total, q.currency)}</td>
                      <td>
                        <StatusBadge status={q.status} label={t(`quotes.statuses.${q.status}`)} />
                      </td>
                      <td>
                        {q.share_enabled ? (
                          <span className="views-info">
                            {q.view_count} {t("quotes.views")}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>{new Date(q.created_at).toLocaleDateString("ar-IQ")}</td>
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
    </AppShell>
  );
}
