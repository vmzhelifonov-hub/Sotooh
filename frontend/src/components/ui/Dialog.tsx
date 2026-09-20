import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  wide?: boolean;
}

export function Dialog({ open, onClose, title, children, wide }: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="dialog-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={wide ? "dialog dialog--wide" : "dialog"} role="dialog" aria-modal="true" aria-label={title}>
        <div className="dialog__header">
          <h2>{title}</h2>
          <button className="dialog__close" onClick={onClose} aria-label="✕">
            ✕
          </button>
        </div>
        <div className="dialog__body">{children}</div>
      </div>
    </div>,
    document.body
  );
}
