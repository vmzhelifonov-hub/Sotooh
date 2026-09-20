import {
  forwardRef,
  type InputHTMLAttributes,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import clsx from "clsx";

interface FieldProps {
  label?: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
  id?: string;
}

export function Field({ label, error, required, children, id }: FieldProps) {
  return (
    <div className={clsx("field", error && "field--error")}>
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
          {required && <span className="field__req" aria-hidden> *</span>}
        </label>
      )}
      {children}
      {error && (
        <div className="field__error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(props, ref) {
  return <input ref={ref} className="input" {...props} />;
});

type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(props, ref) {
  return <select ref={ref} className="input select" {...props} />;
});

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(props, ref) {
  return <textarea ref={ref} className="input textarea" rows={3} {...props} />;
});

export function MoneyInput({ value, onChange, ...rest }: InputProps) {
  return (
    <div className="money-input">
      <input
        {...rest}
        type="text"
        inputMode="decimal"
        className="input"
        value={value}
        onChange={(e) => {
          const v = e.target.value;
          if (/^\d*\.?\d{0,2}$/.test(v)) onChange?.(e);
        }}
        dir="ltr"
      />
      <span className="money-input__suffix">IQD</span>
    </div>
  );
}

export function formatDateAr(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString("ar-IQ", { year: "numeric", month: "2-digit", day: "2-digit" });
  } catch {
    return value.slice(0, 10);
  }
}

export function formatMoney(value: string | number | null | undefined, currency = "IQD"): string {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(num)) return String(value);
  return `${num.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency === "IQD" ? "د.ع" : currency}`;
}
