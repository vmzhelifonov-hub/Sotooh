import { useToast } from "../../providers/ToastProvider";
import { useTranslation } from "react-i18next";

export function Toasts() {
  const { toasts, dismiss } = useToast();
  const { t } = useTranslation();
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast toast--${toast.kind}`}
          onClick={() => dismiss(toast.id)}
          role="status"
        >
          {toast.message === "ok" ? t("settings.saved") : toast.message}
        </div>
      ))}
    </div>
  );
}
