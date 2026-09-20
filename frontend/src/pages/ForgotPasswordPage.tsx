import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Field";
import "./auth.css";

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    try {
      await authApi.requestPasswordReset(email.trim().toLowerCase());
    } catch (err) {
      extractApiError(err); // always show success to avoid account enumeration
    } finally {
      setSent(true);
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <Link to="/" className="auth-brand">
        <span className="brand-gold">Sotooh</span> <span className="brand-ar">سطوع</span>
      </Link>
      <form className="auth-card" onSubmit={onSubmit} noValidate>
        <h1>{t("auth.reset_password")}</h1>
        {sent ? (
          <p className="auth-success">{t("auth.reset_sent")}</p>
        ) : (
          <>
            <Field label={t("auth.email")} id="email" required>
              <Input id="email" type="email" dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} />
            </Field>
            <Button type="submit" loading={loading} disabled={loading} className="auth-submit">
              {t("auth.send_reset_link")}
            </Button>
          </>
        )}
        <div className="auth-links">
          <Link to="/login">{t("auth.login")}</Link>
        </div>
      </form>
    </div>
  );
}
