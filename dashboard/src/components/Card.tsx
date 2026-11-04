import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  padded?: boolean;
}

export function Card({ title, subtitle, action, children, className = "", padded = true }: CardProps) {
  return (
    <section className={`rounded-card border border-line bg-surface ${padded ? "p-4 md:p-5" : ""} ${className}`}>
      {(title || action) && (
        <header className={`flex items-start justify-between gap-3 ${padded ? "mb-4" : "px-4 pt-4 md:px-5 md:pt-5"}`}>
          <div>
            {title && <h2 className="text-sm font-medium text-ink">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-ink3">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink2">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
