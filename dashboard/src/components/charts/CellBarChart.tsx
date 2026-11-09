import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CellReading } from "../../api/types";
import { SERIES, STATUS, fmtNum } from "../../lib/format";

interface CellBarChartProps {
  cells: CellReading[];
  avg: number | null;
  height?: number;
}

export function CellBarChart({ cells, avg, height = 220 }: CellBarChartProps) {
  const voltages = cells.map((c) => c.voltage).filter((v): v is number => v !== null);
  if (voltages.length === 0) return null;
  const lo = Math.min(...voltages) - 0.03;
  const hi = Math.max(...voltages) + 0.03;
  const data = cells.map((c) => ({ ...c, label: `${c.index}` }));

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }} barCategoryGap={2}>
          <XAxis dataKey="label" tickLine={false} interval={0} />
          <YAxis domain={[Number(lo.toFixed(2)), Number(hi.toFixed(2))]} tickLine={false} axisLine={false} width={48} tickFormatter={(v: number) => v.toFixed(2)} />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload as (CellReading & { label: string }) | undefined;
              if (!active || !p) return null;
              return (
                <div className="rounded-lg border border-line bg-raised px-3 py-2 text-xs shadow-lg">
                  <div className="text-ink3">Cell {p.index}</div>
                  <div className="tnum font-medium text-ink">{fmtNum(p.voltage, 3)} V</div>
                  <div className="tnum text-ink2">
                    {p.deviation_mV !== null ? `${p.deviation_mV > 0 ? "+" : ""}${fmtNum(p.deviation_mV, 1)} mV from average` : ""}
                  </div>
                </div>
              );
            }}
          />
          {avg !== null && <ReferenceLine y={avg} stroke="#6f7a86" strokeWidth={1} />}
          <Bar dataKey="voltage" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {data.map((c) => (
              <Cell key={c.index} fill={c.state === "ok" ? SERIES.blue : c.state === "missing" ? "#2b333c" : STATUS.warning} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
