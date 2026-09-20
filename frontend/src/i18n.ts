import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./locales/ar.json";
import en from "./locales/en.json";

const saved = localStorage.getItem("sotooh_lang");
const initial = saved === "en" || saved === "ar" ? saved : "ar";

i18n.use(initReactI18next).init({
  resources: {
    ar: { translation: ar },
    en: { translation: en },
  },
  lng: initial,
  fallbackLng: "ar",
  interpolation: { escapeValue: false },
});

export function applyDirection(lang: string) {
  const dir = lang === "ar" ? "rtl" : "ltr";
  document.documentElement.setAttribute("dir", dir);
  document.documentElement.setAttribute("lang", lang);
  localStorage.setItem("sotooh_lang", lang);
}

applyDirection(i18n.language);
i18n.on("languageChanged", applyDirection);

export default i18n;
