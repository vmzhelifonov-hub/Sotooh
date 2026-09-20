import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { orgApi, authApi } from "../api/endpoints";
import { extractApiError } from "../api/client";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Field, Input, Select } from "../components/ui/Field";
import { Card, CardHeader, Spinner } from "../components/ui/DataDisplay";
import { useAuth } from "../providers/AuthProvider";
import { useToast } from "../providers/ToastProvider";
import "./settings.css";

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user, refetch } = useAuth();
  const { toast } = useToast();

  const { data: org, isLoading } = useQuery({ queryKey: ["org"], queryFn: orgApi.get });
  const { data: members } = useQuery({ queryKey: ["members"], queryFn: orgApi.members });
  const { data: subscription } = useQuery({ queryKey: ["subscription"], queryFn: orgApi.subscription });

  const [form, setForm] = useState<{ company_name?: string; company_name_ar?: string; phone?: string; email?: string; city?: string; address?: string; quote_prefix?: string }>({});
  const [pwd, setPwd] = useState({ current_password: "", new_password: "" });
  const [savingOrg, setSavingOrg] = useState(false);
  const [savingPwd, setSavingPwd] = useState(false);

  if (isLoading || !org) {
    return (
      <AppShell>
        <Spinner label={t("common.loading")} />
      </AppShell>
    );
  }

  const orgForm = { ...org, ...form };

  const saveOrg = async (e: FormEvent) => {
    e.preventDefault();
    setSavingOrg(true);
    try {
      await orgApi.update(form);
      toast({ kind: "success", message: t("settings.saved") });
      void refetch();
    } catch (err) {
      toast({ kind: "error", message: extractApiError(err).message });
    } finally {
      setSavingOrg(false);
    }
  };

  const savePassword = async (e: FormEvent) => {
    e.preventDefault();
    setSavingPwd(true);
    try {
      await authApi.changePassword(pwd);
      setPwd({ current_password: "", new_password: "" });
      toast({ kind: "success", message: t("settings.saved") });
    } catch (err) {
      toast({ kind: "error", message: extractApiError(err).message });
    } finally {
      setSavingPwd(false);
    }
  };

  const isOwner = user?.role === "owner";

  return (
    <AppShell>
      <div className="page-header">
        <h1>{t("settings.title")}</h1>
      </div>

      <div className="settings-grid">
        <Card>
          <CardHeader title={t("settings.organization")} />
          <form onSubmit={saveOrg}>
            <div className="form-grid">
              <Field label={t("auth.company_name")} id="s-company" required>
                <Input
                  id="s-company"
                  value={orgForm.company_name ?? ""}
                  disabled={!isOwner}
                  onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                />
              </Field>
              <Field label={t("products.name_ar")} id="s-company-ar">
                <Input
                  id="s-company-ar"
                  value={orgForm.company_name_ar ?? ""}
                  disabled={!isOwner}
                  onChange={(e) => setForm({ ...form, company_name_ar: e.target.value })}
                />
              </Field>
              <Field label={t("onboarding.phone")} id="s-phone">
                <Input id="s-phone" dir="ltr" value={orgForm.phone ?? ""} disabled={!isOwner} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </Field>
              <Field label={t("auth.email")} id="s-email">
                <Input id="s-email" type="email" dir="ltr" value={orgForm.email ?? ""} disabled={!isOwner} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </Field>
              <Field label={t("onboarding.city")} id="s-city">
                <Input id="s-city" value={orgForm.city ?? ""} disabled={!isOwner} onChange={(e) => setForm({ ...form, city: e.target.value })} />
              </Field>
              <Field label={t("customers.address")} id="s-address">
                <Input id="s-address" value={orgForm.address ?? ""} disabled={!isOwner} onChange={(e) => setForm({ ...form, address: e.target.value })} />
              </Field>
              <Field label={t("settings.quote_prefix")} id="s-prefix">
                <Input
                  id="s-prefix"
                  dir="ltr"
                  maxLength={12}
                  value={orgForm.quote_prefix ?? ""}
                  disabled={!isOwner}
                  onChange={(e) => setForm({ ...form, quote_prefix: e.target.value.toUpperCase() })}
                />
              </Field>
            </div>
            {isOwner && (
              <Button type="submit" loading={savingOrg}>
                {t("common.save")}
              </Button>
            )}
          </form>
        </Card>

        <div className="settings-col">
          <Card>
            <CardHeader title={t("settings.subscription")} />
            {subscription && (
              <div className="sub-info">
                <div className="sub-row">
                  <span>{t("settings.plan")}</span>
                  <strong>{subscription.plan_name ?? subscription.plan ?? "—"}</strong>
                </div>
                <div className="sub-row">
                  <span>{t("settings.status")}</span>
                  <strong>{subscription.status}</strong>
                </div>
                {subscription.ends_at && (
                  <div className="sub-row">
                    <span>{t("settings.expires")}</span>
                    <strong dir="ltr">{new Date(subscription.ends_at).toLocaleDateString("ar-IQ")}</strong>
                  </div>
                )}
              </div>
            )}
          </Card>

          <Card>
            <CardHeader title={t("settings.change_password")} />
            <form onSubmit={savePassword}>
              <Field label={t("auth.current_password")} id="s-pwd-cur" required>
                <Input
                  id="s-pwd-cur"
                  type="password"
                  dir="ltr"
                  autoComplete="current-password"
                  value={pwd.current_password}
                  onChange={(e) => setPwd({ ...pwd, current_password: e.target.value })}
                />
              </Field>
              <Field label={t("auth.new_password")} id="s-pwd-new" required>
                <Input
                  id="s-pwd-new"
                  type="password"
                  dir="ltr"
                  autoComplete="new-password"
                  value={pwd.new_password}
                  onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })}
                />
              </Field>
              <Button type="submit" loading={savingPwd}>
                {t("common.save")}
              </Button>
            </form>
          </Card>
        </div>
      </div>

      <Card className="settings-members">
        <CardHeader title={t("settings.members")} />
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t("auth.email")}</th>
                <th>{t("settings.role")}</th>
              </tr>
            </thead>
            <tbody>
              {(members ?? []).map((m) => (
                <tr key={m.id}>
                  <td dir="ltr">{m.user.email}</td>
                  <td>{t(`settings.roles.${m.role}`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="settings-lang">
        <CardHeader title={t("settings.language")} />
        <Select value={i18n.language} onChange={(e) => window.location.assign(e.target.value === "ar" ? "/" : "/?lang=en")}>
          <option value="ar">العربية</option>
          <option value="en">English</option>
        </Select>
      </Card>
    </AppShell>
  );
}
