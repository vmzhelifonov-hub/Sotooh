import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { publicQuoteApi } from "../api/endpoints";
import { Card, EmptyState, Spinner } from "../components/ui/DataDisplay";
import { formatMoney } from "../components/ui/Field";
import "./publicQuote.css";

interface PublicQuoteData {
  quote_number: string;
  company_name: string;
  company_name_ar: string;
  company_logo: string | null;
  company_phone: string;
  company_email: string;
  company_city: string;
  customer_name: string;
  status: string;
  issue_date: string;
  valid_until: string | null;
  currency: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total: string;
  notes_ar: string;
  notes_en: string;
  payment_terms: string;
  delivery_terms: string;
  items: { description: string; brand_model: string; quantity: string; unit: string; unit_price: string; line_total: string }[];
}

export default function PublicQuotePage() {
  const { t } = useTranslation();
  const { token } = useParams<{ token: string }>();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["public-quote", token],
    queryFn: () => publicQuoteApi.get(token!) as unknown as Promise<PublicQuoteData>,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="public-page">
        <Spinner label={t("common.loading")} />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="public-page">
        <EmptyState title={t("public.not_found")} icon="вњ•" />
      </div>
    );
  }

  return (
    <div className="public-page">
      <Card className="public-doc">
        <header className="public-doc__header">
          <div className="public-doc__brand">
            {data.company_logo ? (
              <img src={data.company_logo} alt={data.company_name} />
            ) : (
              <span className="public-doc__company">{data.company_name_ar || data.company_name}</span>
            )}
          </div>
          <div className="public-doc__title">
            Ш№Ш±Ш¶ ШіШ№Ш±
            <span className="public-doc__subtitle">Commercial Offer</span>
          </div>
        </header>

        <table className="public-meta">
          <tbody>
            <tr>
              <td className="public-meta__label">{t("quotes.number")}</td>
              <td dir="ltr" className="public-meta__num">{data.quote_number}</td>
              <td className="public-meta__label">{t("quotes.issue_date")}</td>
              <td>{new Date(data.issue_date).toLocaleDateString("ar-IQ")}</td>
            </tr>
            <tr>
              <td className="public-meta__label">{t("public.prepared_for")}</td>
              <td className="public-meta__strong">{data.customer_name}</td>
              <td className="public-meta__label">{t("public.valid_until")}</td>
              <td>{data.valid_until ? new Date(data.valid_until).toLocaleDateString("ar-IQ") : "вЂ”"}</td>
            </tr>
          </tbody>
        </table>

        <table className="public-table">
          <thead>
            <tr>
              <th>#</th>
              <th>{t("quotes.description")}</th>
              <th>{t("quotes.brand_model")}</th>
              <th>{t("quotes.quantity")}</th>
              <th>{t("quotes.unit")}</th>
              <th>{t("quotes.unit_price")}</th>
              <th>{t("quotes.line_total")}</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td>{item.description}</td>
                <td dir="ltr">{item.brand_model || "вЂ”"}</td>
                <td dir="ltr">{item.quantity}</td>
                <td>{item.unit}</td>
                <td dir="ltr">{formatMoney(item.unit_price, data.currency)}</td>
                <td dir="ltr" className="public-table__strong">{formatMoney(item.line_total, data.currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="public-totals">
          <div className="public-totals__row">
            <span>{t("quotes.subtotal")}</span>
            <strong dir="ltr">{formatMoney(data.subtotal, data.currency)}</strong>
          </div>
          {Number(data.discount_amount) > 0 && (
            <div className="public-totals__row">
              <span>{t("quotes.discount")}</span>
              <strong dir="ltr">-{formatMoney(data.discount_amount, data.currency)}</strong>
            </div>
          )}
          {Number(data.tax_amount) > 0 && (
            <div className="public-totals__row">
              <span>{t("quotes.tax")}</span>
              <strong dir="ltr">{formatMoney(data.tax_amount, data.currency)}</strong>
            </div>
          )}
          <div className="public-totals__row public-totals__grand">
            <span>{t("quotes.total")}</span>
            <strong dir="ltr">{formatMoney(data.total, data.currency)}</strong>
          </div>
        </div>

        {(data.notes_ar || data.payment_terms) && (
          <div className="public-notes">
            {data.notes_ar && (
              <>
                <h4>{t("quotes.notes_ar")}</h4>
                <p>{data.notes_ar}</p>
              </>
            )}
            {data.payment_terms && (
              <>
                <h4>{t("quotes.payment_terms")}</h4>
                <p>{data.payment_terms}</p>
              </>
            )}
            {data.delivery_terms && (
              <>
                <h4>{t("quotes.delivery_terms")}</h4>
                <p>{data.delivery_terms}</p>
              </>
            )}
          </div>
        )}

        <footer className="public-footer">
          <div className="public-footer__contact">
            <h4>{t("public.contact")}</h4>
            <p dir="ltr">{data.company_phone}</p>
            {data.company_email && <p dir="ltr">{data.company_email}</p>}
            {data.company_city && <p>{data.company_city}</p>}
          </div>
          <div className="public-footer__brand">
            {t("public.powered_by")} <span className="brand-gold">Sotooh</span> В· ШіШ·Щ€Ш№
          </div>
        </footer>
      </Card>
    </div>
  );
}
