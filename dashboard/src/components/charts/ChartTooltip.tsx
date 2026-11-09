import type { TooltipProps } from "recharts";
import { fmtNum } from "../../lib/format";

interface ChartTooltipProps extends TooltipProps<number, string> {
  labelFormatter?: (label: number) => string;
  unit?: string;
  digits?: number;
}

export function ChartTooltip({ active, payload, label, labelFormatter, unit, digits = 1 }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-line bg-raised px-3 py-2 text-xs shadow-lg">
      <div className="mb-1 text-ink3">{labelFormatter && typeof label === "number" ? labelFormatter(label) : label}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="text-ink2">{p.name}</span>
          <span className="tnum ml-auto pl-3 font-medium text-ink">
            {fmtNum(typeof p.value === "number" ? p.value : null, digits)}
            {unit ? ` ${unit}` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
