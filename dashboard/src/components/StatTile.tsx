import type { ReactNode } from "react";

interface StatTileProps {
  label: string;
  value: ReactNode;
  unit?: string;
  hint?: ReactNode;
  accent?: string;
  size?: "md" | "lg";
}

export function StatTile({ label, value, unit, hint, accent, size = "md" }: StatTileProps) {
  return (
    <div className="rounded-card border border-line bg-surface px-4 py-3.5">
      <div className="text-xs text-ink3">{label}</div>
      <div className={`mt-1 flex items-baseline gap-1 ${size === "lg" ? "text-3xl" : "text-2xl"} font-medium leading-none`}>
        <span style={accent ? { color: accent } : undefined}>{value}</span>
        {unit && <span className="text-sm font-normal text-ink3">{unit}</span>}
      </div>
      {hint && <div className="mt-1.5 text-xs text-ink2">{hint}</div>}
    </div>
  );
}

export function Readout({ label, value, unit, accent }: { label: string; value: ReactNode; unit?: string; accent?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5">
      <span className="text-sm text-ink2">{label}</span>
      <span className="tnum text-sm font-medium" style={accent ? { color: accent } : undefined}>
        {value}
        {unit && <span className="ml-1 font-normal text-ink3">{unit}</span>}
      </span>
    </div>
  );
}
