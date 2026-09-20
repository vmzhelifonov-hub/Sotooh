import { useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../providers/AuthProvider";
import { applyDirection } from "../../i18n";
import { Button } from "../ui/Button";
import "./appShell.css";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user?.organization_id) return;
    let cancelled = false;
    void fetch("/api/v1/organization/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((org) => {
        if (!cancelled && org && org.onboarding_completed === false && window.location.pathname !== "/app/onboarding") {
          navigate("/app/onboarding", { replace: true });
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [user?.organization_id, navigate]);

  const changeLang = (lang: string) => {
    applyDirection(lang);
    window.location.reload();
  };

  const navItems = [
    { to: "/app/dashboard", label: t("nav.dashboard") },
    { to: "/app/customers", label: t("nav.customers") },
    { to: "/app/products", label: t("nav.products") },
    { to: "/app/quotes", label: t("nav.quotes") },
    { to: "/app/settings", label: t("nav.settings") },
  ];

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__brand">
          <span className="brand-gold">Sotooh</span>
          <span className="brand-ar">سطوع</span>
        </div>
        <nav className="app-nav" aria-label="main">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "app-nav__link active" : "app-nav__link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="app-header__side">
          <button className="lang-btn" onClick={() => changeLang(t("nav.dashboard") === "Dashboard" ? "ar" : "en")}>
            {t("nav.dashboard") === "Dashboard" ? "عربي" : "EN"}
          </button>
          <span className="app-header__user">{user?.email}</span>
          <Button variant="secondary" size="sm" onClick={() => void logout()}>
            {t("nav.logout")}
          </Button>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
