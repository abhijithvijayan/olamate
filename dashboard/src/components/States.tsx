import type { ReactNode } from "react";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-card border border-line bg-surface px-5 py-8 text-sm text-ink2">
      <span className="h-2 w-2 animate-pulse rounded-full bg-ink3" />
      {label}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-card border border-dashed border-line bg-surface/50 px-5 py-10 text-center">
      <p className="text-sm font-medium text-ink">{title}</p>
      {children && <div className="mx-auto mt-2 max-w-md text-sm text-ink2">{children}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="rounded-card border border-soc-low/40 bg-surface px-5 py-6">
      <p className="text-sm font-medium text-ink">Could not reach the API</p>
      <p className="mt-1 text-sm text-ink2">
        {error.message}. Start it with <code className="rounded bg-raised px-1.5 py-0.5 text-xs">cd api &amp;&amp; uvicorn main:app</code>
      </p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded-md bg-raised px-3 py-1.5 text-sm text-ink hover:bg-raised/70">
          Try again
        </button>
      )}
    </div>
  );
}

export function CollectorBadge({ running, ageSeconds }: { running: boolean; ageSeconds: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink2">
      <span className={`h-2 w-2 rounded-full ${running ? "bg-soc-high" : "bg-ink3"}`} />
      {running ? "Collector live" : `Last data ${ageSeconds}`}
    </span>
  );
}
