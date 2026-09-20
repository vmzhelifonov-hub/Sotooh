import type { ReactNode } from "react";
import clsx from "clsx";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("card", className)}>{children}</div>;
}

export function CardHeader({ title, action }: { title: ReactNode; action?: ReactNode }) {
  return (
    <div className="card__header">
      <h3 className="card__title">{title}</h3>
      {action}
    </div>
  );
}

type BadgeKind = "neutral" | "gold" | "success" | "danger" | "dark";

const statusKind: Record<string, BadgeKind> = {
  draft: "neutral",
  sent: "gold",
  accepted: "success",
  rejected: "danger",
  expired: "neutral",
  won: "success",
  lost: "danger",
  new: "neutral",
  contacted: "gold",
  quote_sent: "gold",
  follow_up: "gold",
};

export function Badge({ kind = "neutral", children }: { kind?: BadgeKind; children: ReactNode }) {
  return <span className={clsx("badge", `badge--${kind}`)}>{children}</span>;
}

export function StatusBadge({ status, label }: { status: string; label: string }) {
  return <Badge kind={statusKind[status] ?? "neutral"}>{label}</Badge>;
}

export function EmptyState({
  title,
  action,
  icon = "◻",
}: {
  title: string;
  action?: ReactNode;
  icon?: string;
}) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon" aria-hidden>{icon}</div>
      <p>{title}</p>
      {action}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="spinner-wrap" role="status">
      <div className="spinner" aria-hidden />
      {label && <span>{label}</span>}
    </div>
  );
}

export function Pagination({
  page,
  count,
  pageSize,
  onChange,
  labels,
}: {
  page: number;
  count: number;
  pageSize: number;
  onChange: (page: number) => void;
  labels: { prev: string; next: string; page: string };
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button className="btn btn--ghost btn--sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        {labels.prev}
      </button>
      <span>
        {labels.page} {page} / {totalPages}
      </span>
      <button className="btn btn--ghost btn--sm" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        {labels.next}
      </button>
    </div>
  );
}
