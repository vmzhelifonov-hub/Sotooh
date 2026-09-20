import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { authApi } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Field";
import "./auth.css";

export default function ResetPasswordPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!password || password.length < 8) {
      setError(t("common.required") + " (8+)");
      return;
    }
    setLoading(true);
    try {
      await authApi.confirmPasswordReset({ uid, token, password });
      setDone(true);
    } catch (err) {
      setError(extractApiError(err).message);
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
        <h1>{t("auth.reset_password")}</h1>
        {done ? (
          <p className="auth-success">
            ✓ <Link to="/login">{t("auth.login")}</Link>
          </p>
        ) : (
          <>
            {error && <div className="auth-error" role="alert">{error}</div>}
            <Field label={t("auth.new_password")} id="password" required>
              <Input
                id="password"
                type="password"
                dir="ltr"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <Button type="submit" loading={loading} disabled={loading || !uid || !token} className="auth-submit">
              {t("auth.reset_password")}
            </Button>
          </>
        )}
      </form>
    </div>
  );
}
