import { fmtNum, tempColor } from "../../lib/format";

interface TempHeatmapProps {
  temps: { label: string; value: number | null }[];
  columns?: number;
  min?: number;
  max?: number;
}

export function TempHeatmap({ temps, columns = 3, min = 20, max = 55 }: TempHeatmapProps) {
  return (
    <div>
      <div className="grid gap-0.5" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
        {temps.map((t) => (
          <div
            key={t.label}
            className="flex h-20 flex-col justify-between rounded-md p-2.5"
            style={{ background: t.value === null ? "#1c2229" : tempColor(t.value, min, max) }}
            title={`${t.label}: ${fmtNum(t.value, 1)} °C`}
          >
            <span className="text-[11px] text-white/70">{t.label}</span>
            <span className="tnum text-lg font-medium text-white">
              {fmtNum(t.value, 1)}
              <span className="ml-0.5 text-xs font-normal text-white/70">°C</span>
            </span>
          </div>
        ))}
      </div>
      <div className="mt-2 flex items-center gap-2 text-[10px] text-ink3">
        <span>{min}°</span>
        <div className="h-1.5 flex-1 rounded-full" style={{ background: `linear-gradient(90deg, ${tempColor(min, min, max)}, ${tempColor((min + max) / 2, min, max)}, ${tempColor(max, min, max)})` }} />
        <span>{max}°</span>
      </div>
    </div>
  );
}
