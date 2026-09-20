import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { dashboardApi } from "../api/endpoints";
import { AppShell } from "../components/layout/AppShell";
import { Card, CardHeader, EmptyState, Spinner, StatusBadge } from "../components/ui/DataDisplay";
import { formatMoney } from "../components/ui/Field";
import { Button } from "../components/ui/Button";
import "./dashboard.css";

export default function DashboardPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: dashboardApi.get });

  if (isLoading) return <AppShell><Spinner label={t("common.loading")} /></AppShell>;
  if (!data) return <AppShell><EmptyState title={t("common.error")} /></AppShell>;

  const stats = [
    { label: t("dashboard.leads_this_month"), value: String(data.leads_this_month) },
    { label: t("dashboard.quotes_this_month"), value: String(data.quotes_this_month) },
    { label: t("dashboard.quote_value"), value: formatMoney(data.quote_value_this_month) },
    { label: t("dashboard.won_value"), value: formatMoney(data.won_value) },
    { label: t("dashboard.won_deals"), value: String(data.won_deals) },
    { label: t("dashboard.conversion"), value: `${data.conversion_rate}%` },
    { label: t("dashboard.avg_quote"), value: formatMoney(data.average_quote_value) },
    { label: t("dashboard.overdue"), value: String(data.overdue_follow_ups), alert: data.overdue_follow_ups > 0 },
  ];

  const funnelMax = Math.max(data.funnel.new, data.funnel.quote_sent, data.funnel.won, 1);

  return (
    <AppShell>
      <div className="page-header">
        <h1>{t("dashboard.title")}</h1>
        <Link to="/app/quotes">
          <Button>{t("quotes.add")}</Button>
        </Link>
      </div>

      <div className="stats-grid">
        {stats.map((s) => (
          <Card key={s.label} className={s.alert ? "stat stat--alert" : "stat"}>
            <div className="stat__value">{s.value}</div>
            <div className="stat__label">{s.label}</div>
          </Card>
        ))}
      </div>

      <div className="dash-grid">
        <Card>
          <CardHeader title={t("dashboard.funnel")} />
          <div className="funnel">
            {(
              [
                ["funnel_new", data.funnel.new],
                ["funnel_sent", data.funnel.quote_sent],
                ["funnel_won", data.funnel.won],
              ] as const
            ).map(([key, value]) => (
              <div className="funnel__row" key={key}>
                <span className="funnel__label">{t(`dashboard.${key}`)}</span>
                <div className="funnel__bar-wrap">
                  <div className="funnel__bar" style={{ width: `${(value / funnelMax) * 100}%` }} />
                </div>
                <span className="funnel__value">{value}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title={t("dashboard.needs_attention")} />
          {data.needs_attention.length === 0 ? (
            <EmptyState title={t("dashboard.empty")} icon="✓" />
          ) : (
            <ul className="attention-list">
              {data.needs_attention.map((c) => (
                <li key={c.id}>
                  <Link to="/app/customers" className="attention-item">
                    <span className="attention-item__name">{c.name}</span>
                    <span className="attention-item__phone" dir="ltr">{c.phone}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card>
        <CardHeader title={t("dashboard.recent_quotes")} />
        {data.recent_quotes.length === 0 ? (
          <EmptyState title={t("quotes.empty")} />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>{t("quotes.number")}</th>
                  <th>{t("quotes.customer")}</th>
                  <th>{t("quotes.total")}</th>
                  <th>{t("common.status")}</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_quotes.map((q) => (
                  <tr key={q.id}>
                    <td>
                      <Link to={`/app/quotes/${q.id}`} className="quote-link" dir="ltr">
                        {q.quote_number}
                      </Link>
                    </td>
                    <td>{q.customer_name}</td>
                    <td dir="ltr">{formatMoney(q.total, q.currency)}</td>
                    <td>
                      <StatusBadge status={q.status} label={t(`quotes.statuses.${q.status}`)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </AppShell>
  );
}
