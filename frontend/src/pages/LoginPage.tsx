import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { useAuth } from "../providers/AuthProvider";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Field";
import "./auth.css";

export default function LoginPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { refetch } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError(t("common.required"));
      return;
    }
    setLoading(true);
    try {
      await authApi.login({ email: email.trim().toLowerCase(), password });
      await refetch();
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from ?? "/app/dashboard", { replace: true });
    } catch (err) {
      setError(extractApiError(err).message || t("auth.invalid_credentials"));
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
        <h1>{t("auth.login")}</h1>
        {error && <div className="auth-error" role="alert">{error}</div>}
        <Field label={t("auth.email")} id="email" required>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            dir="ltr"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label={t("auth.password")} id="password" required>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            dir="ltr"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" loading={loading} disabled={loading} className="auth-submit">
          {t("auth.login")}
        </Button>
        <div className="auth-links">
          <Link to="/forgot-password">{t("auth.forgot_password")}</Link>
          <span>
            {t("auth.no_account")} <Link to="/register">{t("auth.register")}</Link>
          </span>
        </div>
      </form>
    </div>
  );
}
