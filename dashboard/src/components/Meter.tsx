import { fmtNum } from "../lib/format";

interface MeterProps {
  label: string;
  value: number | null;
  min: number;
  max: number;
  unit: string;
  digits?: number;
  color: string;
  center?: number;
}

export function Meter({ label, value, min, max, unit, digits = 1, color, center }: MeterProps) {
  const span = max - min;
  const clamp = (v: number) => Math.max(min, Math.min(max, v));
  const v = value === null ? null : clamp(value);
  const zero = center === undefined ? min : clamp(center);
  const left = v === null ? 0 : ((Math.min(v, zero) - min) / span) * 100;
  const width = v === null ? 0 : (Math.abs(v - zero) / span) * 100;

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-xs text-ink3">{label}</span>
        <span className="tnum text-xl font-medium">
          {fmtNum(value, digits)}
          <span className="ml-1 text-xs font-normal text-ink3">{unit}</span>
        </span>
      </div>
      <div className="relative mt-2 h-2 overflow-hidden rounded-full bg-raised" role="meter" aria-valuemin={min} aria-valuemax={max} aria-valuenow={value ?? undefined} aria-label={label}>
        <div
          className="absolute top-0 h-full rounded-full"
          style={{ left: `${left}%`, width: `${width}%`, background: color, transition: "left 300ms ease, width 300ms ease" }}
        />
        {center !== undefined && (
          <div className="absolute top-0 h-full w-px bg-ink3" style={{ left: `${((zero - min) / span) * 100}%` }} />
        )}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-ink3">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
