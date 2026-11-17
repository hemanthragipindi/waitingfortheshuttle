import {
  AlertCircle,
  ArrowDown,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  LoaderCircle,
  Search,
  X,
} from "lucide-react";
import { useEffect } from "react";

export function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-heading__description">{description}</p>}
      </div>
      {action && <div className="page-heading__action">{action}</div>}
    </div>
  );
}

export function Button({ children, variant = "primary", icon: Icon, className = "", ...props }) {
  return (
    <button type="button" className={`button button--${variant} ${className}`.trim()} {...props}>
      {Icon && <Icon size={16} aria-hidden="true" />}
      {children}
    </button>
  );
}

export function Panel({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`panel ${className}`.trim()}>
      {(title || action) && (
        <div className="panel__heading">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatCard({ label, value, detail, icon: Icon, tone = "green" }) {
  return (
    <article className="stat-card">
      <span className={`stat-card__icon stat-card__icon--${tone}`}>
        <Icon size={19} aria-hidden="true" />
      </span>
      <div>
        <p>{label}</p>
        <strong>{value ?? "—"}</strong>
        {detail && <span>{detail}</span>}
      </div>
    </article>
  );
}

const statusLabels = {
  ON_TIME: "On time",
  DELAYED: "Delayed",
  UNAVAILABLE: "Out of service",
  NOT_UPDATED: "Not updated",
  PENDING: "Pending",
  IN_REVIEW: "In review",
  RESOLVED: "Resolved",
  DISMISSED: "Dismissed",
};

export function StatusBadge({ status }) {
  return (
    <span className={`status-badge status-badge--${String(status || "").toLowerCase()}`}>
      <span className="status-badge__dot" />
      {statusLabels[status] || status || "Unknown"}
    </span>
  );
}

export function Loading({ label = "Loading information" }) {
  return (
    <div className="state-box" role="status">
      <LoaderCircle className="spin" size={21} aria-hidden="true" />
      <span>{label}…</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-box state-box--error" role="alert">
      <AlertCircle size={20} aria-hidden="true" />
      <span>{message}</span>
      {onRetry && <button className="inline-button" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", description, action }) {
  return (
    <div className="empty-state">
      <span className="empty-state__mark"><Search size={20} aria-hidden="true" /></span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}

export function SearchField({ value, onChange, placeholder = "Search" }) {
  return (
    <label className="search-field">
      <Search size={16} aria-hidden="true" />
      <span className="sr-only">{placeholder}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
      />
      {value && (
        <button type="button" aria-label="Clear search" onClick={() => onChange("")}>
          <X size={15} />
        </button>
      )}
    </label>
  );
}

export function Pagination({ page, limit, total, onPageChange }) {
  const pages = Math.max(1, Math.ceil(total / limit));
  if (pages <= 1) return null;
  return (
    <div className="pagination">
      <span>{total ? `${(page - 1) * limit + 1}–${Math.min(page * limit, total)} of ${total}` : "0 results"}</span>
      <div>
        <button disabled={page <= 1} onClick={() => onPageChange(page - 1)} aria-label="Previous page">
          <ChevronLeft size={17} />
        </button>
        <span>Page {page} of {pages}</span>
        <button disabled={page >= pages} onClick={() => onPageChange(page + 1)} aria-label="Next page">
          <ChevronRight size={17} />
        </button>
      </div>
    </div>
  );
}

export function Modal({ title, onClose, children, wide = false }) {
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className={`modal ${wide ? "modal--wide" : ""}`} role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <header className="modal__heading">
          <h2 id="modal-title">{title}</h2>
          <button type="button" className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={19} /></button>
        </header>
        {children}
      </section>
    </div>
  );
}

export function FormField({ label, hint, error, className = "", ...props }) {
  const id = props.id || props.name;
  const isTextArea = props.as === "textarea";
  const Input = isTextArea ? "textarea" : "input";
  const inputProps = { ...props };
  delete inputProps.as;
  delete inputProps.error;
  delete inputProps.hint;
  if (isTextArea) {
    delete inputProps.type;
    delete inputProps.min;
    delete inputProps.max;
    delete inputProps.step;
  }
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  return (
    <div className={`form-field ${className}`.trim()}>
      <label htmlFor={id}>{label}{props.required && <span aria-hidden="true"> *</span>}</label>
      <Input id={id} aria-invalid={Boolean(error)} aria-describedby={error ? errorId : hint ? hintId : undefined} {...inputProps} />
      {error && <span className="field-error" id={errorId}>{error}</span>}
      {!error && hint && <span className="field-hint" id={hintId}>{hint}</span>}
    </div>
  );
}

export function formatDate(value, options = {}) {
  if (!value) return "Not updated";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    ...options,
  }).format(date);
}

export function SortControl({ direction, onToggle, label = "Sort by latest" }) {
  const Icon = direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <button type="button" className="sort-control" onClick={onToggle}>
      {label}<Icon size={14} aria-hidden="true" />
    </button>
  );
}
