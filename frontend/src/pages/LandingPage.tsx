import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { applyDirection } from "../i18n";
import "./landing.css";

export default function LandingPage() {
  const { t, i18n } = useTranslation();
  const isAr = i18n.language === "ar";

  const features = [
    { key: "feature_quotes", icon: "▣" },
    { key: "feature_pdf", icon: "⎙" },
    { key: "feature_whatsapp", icon: "✆" },
    { key: "feature_crm", icon: "◷" },
    { key: "feature_dashboard", icon: "▤" },
    { key: "feature_team", icon: "⚃" },
  ];

  const steps = ["how_1", "how_2", "how_3", "how_4"];
  const problems = ["problem_1", "problem_2", "problem_3"];
  const faqs = ["faq_q1", "faq_q2", "faq_q3", "faq_q4"];

  return (
    <div className="landing">
      <header className="landing-header">
        <div className="landing-header__brand">
          <span className="brand-gold">Sotooh</span>
          <span className="brand-ar">سطوع</span>
        </div>
        <nav className="landing-header__nav">
          <button className="lang-btn" onClick={() => applyDirection(isAr ? "en" : "ar")}>
            {isAr ? "English" : "عربي"}
          </button>
          <Link to="/login" className="landing-link">
            {t("nav.login")}
          </Link>
          <Link to="/register">
            <Button size="sm">{t("nav.register")}</Button>
          </Link>
        </nav>
      </header>

      <section className="hero">
        <div className="hero__mark" aria-hidden>سطوع</div>
        <h1>{t("landing.hero_title")}</h1>
        <p>{t("landing.hero_subtitle")}</p>
        <div className="hero__cta">
          <Link to="/register">
            <Button variant="gold" size="lg">{t("landing.cta_start")}</Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary" size="lg">{t("landing.cta_login")}</Button>
          </Link>
        </div>
      </section>

      <section className="landing-section landing-section--dark">
        <h2>{t("landing.problem_title")}</h2>
        <div className="grid-3">
          {problems.map((p, i) => (
            <div className="problem-card" key={p}>
              <span className="problem-card__num">{i + 1}</span>
              <p>{t(`landing.${p}`)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section">
        <h2>{t("landing.how_title")}</h2>
        <ol className="steps">
          {steps.map((s, i) => (
            <li key={s}>
              <span className="steps__num">{i + 1}</span>
              {t(`landing.${s}`)}
            </li>
          ))}
        </ol>
      </section>

      <section className="landing-section landing-section--dark">
        <h2>{t("landing.features_title")}</h2>
        <div className="grid-3">
          {features.map((f) => (
            <div className="feature-card" key={f.key}>
              <span className="feature-card__icon" aria-hidden>{f.icon}</span>
              <p>{t(`landing.${f.key}`)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section">
        <h2>{t("landing.faq_title")}</h2>
        <div className="faq">
          {faqs.map((q) => (
            <details key={q}>
              <summary>{t(`landing.${q}`)}</summary>
              <p>{t(`landing.${q.replace("q", "a")}`)}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="landing-cta">
        <h2>{t("landing.cta_start")}</h2>
        <p>{t("landing.hero_subtitle")}</p>
        <Link to="/register">
          <Button variant="gold" size="lg">{t("landing.cta_start")}</Button>
        </Link>
      </section>

      <footer className="landing-footer">
        <span>
          © {new Date().getFullYear()} Sotooh · سطوع — {t("landing.footer_rights")}
        </span>
      </footer>
    </div>
  );
}
