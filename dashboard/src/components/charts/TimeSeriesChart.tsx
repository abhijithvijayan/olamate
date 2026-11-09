import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartTooltip } from "./ChartTooltip";

export interface SeriesDef {
  key: string;
  name: string;
  color: string;
}

interface TimeSeriesChartProps<T> {
  data: T[];
  xKey: keyof T & string;
  series: SeriesDef[];
  unit?: string;
  digits?: number;
  height?: number;
  xFormatter: (x: number) => string;
  yDomain?: [number | "auto", number | "auto"];
}

export function TimeSeriesChart<T extends object>({
  data,
  xKey,
  series,
  unit,
  digits = 1,
  height = 220,
  xFormatter,
  yDomain = ["auto", "auto"],
}: TimeSeriesChartProps<T>) {
  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey={xKey}
            type="number"
            domain={["dataMin", "dataMax"]}
            tickFormatter={xFormatter}
            minTickGap={40}
            tickLine={false}
          />
          <YAxis domain={yDomain} tickLine={false} axisLine={false} width={48} tickFormatter={(v: number) => `${v}`} />
          <Tooltip
            content={<ChartTooltip labelFormatter={xFormatter} unit={unit} digits={digits} />}
            cursor={{ stroke: "#3b4551", strokeWidth: 1 }}
          />
          {series.length > 1 && (
            <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: "#aab3bd", paddingTop: 8 }} />
          )}
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: "#151a20" }}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
