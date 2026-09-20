import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { useAuth } from "../providers/AuthProvider";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Field";
import "./auth.css";

export default function RegisterPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { refetch } = useAuth();
  const navigate = useNavigate();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password || !companyName.trim()) {
      setError(t("common.required"));
      return;
    }
    if (password.length < 8) {
      setError(t("common.required") + " (8+)");
      return;
    }
    setLoading(true);
    try {
      await authApi.register({
        email: email.trim().toLowerCase(),
        password,
        company_name: companyName.trim(),
      });
      await refetch();
      navigate("/app/onboarding", { replace: true });
    } catch (err) {
      const apiError = extractApiError(err);
      const details = apiError.details;
      if (details && typeof details === "object" && !Array.isArray(details)) {
        const first = Object.values(details)[0];
        setError(Array.isArray(first) ? first[0] ?? apiError.message : String(first));
      } else {
        setError(apiError.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <Link to="/" className="auth-brand">
        <span className="brand-gold">Sotooh</span> <span className="brand-ar">سطوع</span>
      </Link>
      <form className="auth-card" onSubmit={onSubmit} noValidate>
        <h1>{t("auth.register")}</h1>
        {error && <div className="auth-error" role="alert">{error}</div>}
        <Field label={t("auth.company_name")} id="company" required>
          <Input id="company" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
        </Field>
        <Field label={t("auth.email")} id="email" required>
          <Input id="email" type="email" dir="ltr" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label={t("auth.password")} id="password" required>
          <Input
            id="password"
            type="password"
            dir="ltr"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" loading={loading} disabled={loading} className="auth-submit">
          {t("auth.register")}
        </Button>
        <div className="auth-links">
          <span>
            {t("auth.have_account")} <Link to="/login">{t("auth.login")}</Link>
          </span>
        </div>
      </form>
    </div>
  );
}
