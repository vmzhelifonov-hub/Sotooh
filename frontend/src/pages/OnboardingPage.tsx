import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { customerApi, orgApi, productApi, quoteApi, type Organization } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { Button } from "../components/ui/Button";
import { Field, Input, MoneyInput, Select, Textarea } from "../components/ui/Field";
import { useToast } from "../providers/ToastProvider";
import { AppShell } from "../components/layout/AppShell";
import "./onboarding.css";

const STEPS = ["company", "products", "customer", "quote"] as const;

export default function OnboardingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [step, setStep] = useState(0);
  const [org, setOrg] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(false);

  // company step state
  const [companyName, setCompanyName] = useState("");
  const [companyNameAr, setCompanyNameAr] = useState("");
  const [city, setCity] = useState("");
  const [phone, setPhone] = useState("");

  // product step state
  const [productName, setProductName] = useState("");
  const [productCategory, setProductCategory] = useState("solar_panel");
  const [productPrice, setProductPrice] = useState("");

  // customer step state
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");

  // quote step state
  const [quoteCustomerId, setQuoteCustomerId] = useState("");
  const [quoteDescription, setQuoteDescription] = useState("");
  const [quoteQty, setQuoteQty] = useState("1");
  const [quotePrice, setQuotePrice] = useState("");
  const [customers, setCustomers] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    void orgApi
      .get()
      .then((data) => {
        setOrg(data);
        setCompanyName(data.company_name);
        setCompanyNameAr(data.company_name_ar);
        setCity(data.city);
        setPhone(data.phone);
      })
      .catch(() => undefined);
    void customerApi
      .list({ page: 1 })
      .then((res) => setCustomers(res.results.map((c) => ({ id: c.id, name: c.name }))))
      .catch(() => undefined);
  }, []);

  const finish = () => {
    void orgApi
      .update({ onboarding_completed: true })
      .then(() => navigate("/app/dashboard", { replace: true }))
      .catch((err) => toast({ kind: "error", message: extractApiError(err).message }));
  };

  const saveCompany = async () => {
    if (!companyName.trim()) {
      toast({ kind: "error", message: t("common.required") });
      return;
    }
    setLoading(true);
    try {
      await orgApi.update({ company_name: companyName.trim(), company_name_ar: companyNameAr.trim(), city, phone });
      setStep(1);
    } catch (err) {
      toast({ kind: "error", message: extractApiError(err).message });
    } finally {
      setLoading(false);
    }
  };

  const saveProduct = async (skip: boolean) => {
    if (skip) {
      setStep(2);
      return;
    }
    if (!productName.trim() || !productPrice) {
      toast({ kind: "error", message: t("common.required") });
      return;
    }
    setLoading(true);
    try {
      await productApi.create({ name_ar: productName.trim(), category: productCategory, selling_price: productPrice });
      setStep(2);
    } catch (err) {
      toast({ kind: "error", message: extractApiError(err).message });
    } finally {
      setLoading(false);
    }
  };

  const saveCustomer = async (skip: boolean) => {
    if (skip) {
      setStep(3);
      return;
    }
    if (!customerName.trim() || !customerPhone.trim()) {
      toast({ kind: "error", message: t("common.required") });
      return;
    }
    setLoading(true);
    try {
      const created = await customerApi.create({ name: customerName.trim(), phone: customerPhone.trim() });
      setQuoteCustomerId(created.id);
      setStep(3);
    } catch (err) {
      toast({ kind: "error", message: extractApiError(err).message });
    } finally {
      setLoading(false);
    }
  };

  const saveQuote = async (skip: boolean) => {
    if (skip) {
      void finish();
      return;
    }
    if (!quoteCustomerId || !quoteDescription.trim() || !quotePrice) {
      toast({ kind: "error", message: t("common.required") });
      return;
    }
    setLoading(true);
    try {
      await quoteApi.create({
        customer: quoteCustomerId,
        items: [
          {
            description: quoteDescription.trim(),
            quantity: quoteQty,
            unit_price: quotePrice,
            discount_amount: "0",
            display_order: 0,
          },
        ],
      });
      await finish();
    } catch (err) {
      toast({ kind: "error", message: extractApiError(err).message });
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="onboarding">
        <h1>{t("onboarding.title")}</h1>
        <div className="onboarding__progress" aria-hidden>
          {STEPS.map((s, i) => (
            <span key={s} className={i <= step ? "onboarding__dot active" : "onboarding__dot"} />
          ))}
        </div>
        <div className="onboarding__step-label">
          {t("onboarding.step")} {step + 1} {t("onboarding.of")} 4 — {t(`onboarding.${STEPS[step]}`)}
        </div>

        {step === 0 && (
          <div className="onboarding__card">
            <p className="onboarding__hint">{t("onboarding.company_hint")}</p>
            <Field label={t("auth.company_name")} id="ob-company" required>
              <Input id="ob-company" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
            </Field>
            <Field label={t("products.name_ar") + " (الشركة)"} id="ob-company-ar">
              <Input id="ob-company-ar" value={companyNameAr} onChange={(e) => setCompanyNameAr(e.target.value)} />
            </Field>
            <Field label={t("onboarding.city")} id="ob-city">
              <Input id="ob-city" value={city} onChange={(e) => setCity(e.target.value)} />
            </Field>
            <Field label={t("onboarding.phone")} id="ob-phone">
              <Input id="ob-phone" dir="ltr" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </Field>
            <Button loading={loading} disabled={loading} onClick={() => void saveCompany()}>
              {t("onboarding.next")}
            </Button>
          </div>
        )}

        {step === 1 && (
          <div className="onboarding__card">
            <p className="onboarding__hint">{t("onboarding.products_hint")}</p>
            <Field label={t("products.name_ar")} id="ob-pname" required>
              <Input id="ob-pname" value={productName} onChange={(e) => setProductName(e.target.value)} />
            </Field>
            <Field label={t("products.category")} id="ob-pcat">
              <Select id="ob-pcat" value={productCategory} onChange={(e) => setProductCategory(e.target.value)}>
                {["solar_panel", "inverter", "battery", "mounting", "protection", "cable", "accessory", "installation", "service", "other"].map(
                  (c) => (
                    <option key={c} value={c}>
                      {t(`products.categories.${c}`)}
                    </option>
                  )
                )}
              </Select>
            </Field>
            <Field label={t("products.price")} id="ob-pprice" required>
              <MoneyInput id="ob-pprice" value={productPrice} onChange={(e) => setProductPrice(e.target.value)} />
            </Field>
            <div className="onboarding__actions">
              <Button variant="ghost" onClick={() => void saveProduct(true)}>
                {t("onboarding.skip")}
              </Button>
              <Button loading={loading} disabled={loading} onClick={() => void saveProduct(false)}>
                {t("onboarding.next")}
              </Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="onboarding__card">
            <p className="onboarding__hint">{t("onboarding.customer_hint")}</p>
            <Field label={t("customers.name")} id="ob-cname" required>
              <Input id="ob-cname" value={customerName} onChange={(e) => setCustomerName(e.target.value)} />
            </Field>
            <Field label={t("customers.phone")} id="ob-cphone" required>
              <Input id="ob-cphone" dir="ltr" value={customerPhone} onChange={(e) => setCustomerPhone(e.target.value)} />
            </Field>
            <div className="onboarding__actions">
              <Button variant="ghost" onClick={() => void saveCustomer(true)}>
                {t("onboarding.skip")}
              </Button>
              <Button loading={loading} disabled={loading} onClick={() => void saveCustomer(false)}>
                {t("onboarding.next")}
              </Button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="onboarding__card">
            <p className="onboarding__hint">{t("onboarding.quote_hint")}</p>
            <Field label={t("quotes.customer")} id="ob-qcust" required>
              <Select id="ob-qcust" value={quoteCustomerId} onChange={(e) => setQuoteCustomerId(e.target.value)}>
                <option value="">{t("quotes.select_customer")}</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t("quotes.description")} id="ob-qdesc" required>
              <Textarea id="ob-qdesc" value={quoteDescription} onChange={(e) => setQuoteDescription(e.target.value)} />
            </Field>
            <Field label={t("quotes.quantity")} id="ob-qqty" required>
              <Input id="ob-qqty" dir="ltr" value={quoteQty} onChange={(e) => setQuoteQty(e.target.value)} />
            </Field>
            <Field label={t("quotes.unit_price")} id="ob-qprice" required>
              <MoneyInput id="ob-qprice" value={quotePrice} onChange={(e) => setQuotePrice(e.target.value)} />
            </Field>
            <div className="onboarding__actions">
              <Button variant="ghost" onClick={() => void saveQuote(true)}>
                {t("onboarding.skip")}
              </Button>
              <Button variant="gold" loading={loading} disabled={loading} onClick={() => void saveQuote(false)}>
                {t("onboarding.finish")}
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
