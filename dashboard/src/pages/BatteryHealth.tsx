import { useMemo } from "react";
import { api } from "../api/client";
import { usePolling } from "../api/hooks";
import { PACK_TEMP_KEYS } from "../api/types";
import { Card, PageHeader } from "../components/Card";
import { CellBarChart } from "../components/charts/CellBarChart";
import { TempHeatmap } from "../components/charts/TempHeatmap";
import { TimeSeriesChart } from "../components/charts/TimeSeriesChart";
import { StatTile } from "../components/StatTile";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { SERIES, STATUS, fmtDateTime, fmtDay, fmtNum, fmtTime } from "../lib/format";

export function BatteryHealth() {
  const health = usePolling(() => api.batteryHealth(30), 60000);
  const cells = usePolling(() => api.batteryCells(), 5000);
  const status = usePolling(() => api.status(), 5000);

  const trend = useMemo(() => health.data?.trend ?? [], [health.data]);
  const spansDays = trend.length > 1 && trend[trend.length - 1]!.timestamp - trend[0]!.timestamp > 86400;
  const xFormatter = spansDays ? fmtDay : fmtTime;

  const latest = health.data?.latest;
  const report = cells.data;
  const temps = status.data
    ? PACK_TEMP_KEYS.map((k, i) => ({ label: `Sensor ${i + 1}`, value: status.data![k] }))
    : [];

  if (health.error) return <ErrorState error={health.error} onRetry={health.refresh} />;
  if (health.loading && !health.data) return <LoadingState label="Loading battery history" />;

  const nothingYet = trend.length === 0 && !report;

  return (
    <>
      <PageHeader
        title="Battery health"
        subtitle={health.data?.source === "telemetry" ? "Built from live telemetry until the first 5 minute snapshot lands" : latest ? `Last snapshot ${fmtDateTime(latest.timestamp)}` : undefined}
      />

      {nothingYet && (
        <EmptyState title="No battery data yet">Health snapshots are written every five minutes while the collector runs.</EmptyState>
      )}

      {!nothingYet && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatTile label="State of health" value={fmtNum(latest?.soh ?? status.data?.soh, 0)} unit="%" />
            <StatTile label="Cell spread" value={fmtNum(report?.spread_mV ?? latest?.cell_spread_mV, 0)} unit="mV" accent={(report?.spread_mV ?? 0) > 40 ? STATUS.warning : undefined} />
            <StatTile label="Average cell" value={fmtNum(report?.avg, 3)} unit="V" />
            <StatTile label="Balance" value={report ? (report.balancing_needed ? "Uneven" : "Even") : "–"} accent={report?.balancing_needed ? STATUS.warning : STATUS.good} hint={report ? `${report.cells.filter((c) => c.state !== "ok").length} of 14 cells off by more than 20 mV` : undefined} />
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card title="State of health" subtitle="% reported by the BMS, per snapshot">
              {trend.length > 1 ? (
                <TimeSeriesChart data={trend} xKey="timestamp" xFormatter={xFormatter} unit="%" digits={1} series={[{ key: "soh", name: "SOH", color: SERIES.aqua }]} yDomain={["auto", 100]} />
              ) : (
                <p className="text-sm text-ink2">Need at least two snapshots to draw a trend.</p>
              )}
            </Card>

            <Card title="Cell spread" subtitle="mV between highest and lowest cell, per snapshot">
              {trend.length > 1 ? (
                <TimeSeriesChart data={trend} xKey="timestamp" xFormatter={xFormatter} unit="mV" digits={0} series={[{ key: "cell_spread_mV", name: "Spread", color: SERIES.blue }]} yDomain={[0, "auto"]} />
              ) : (
                <p className="text-sm text-ink2">Need at least two snapshots to draw a trend.</p>
              )}
            </Card>

            <Card title="Cell voltages" subtitle="Line marks the pack average. Amber bars sit more than 20 mV from it.">
              {report && report.cells.length > 0 ? (
                <>
                  <CellBarChart cells={report.cells} avg={report.avg} />
                  <ul className="mt-3 grid grid-cols-7 gap-1.5 sm:[grid-template-columns:repeat(14,minmax(0,1fr))]" aria-label="Cell balance">
                    {report.cells.map((c) => (
                      <li key={c.index} className="flex flex-col items-center gap-1 text-[10px] text-ink3" title={`Cell ${c.index}: ${c.state}`}>
                        <span
                          className="h-1.5 w-full rounded-full"
                          style={{ background: c.state === "ok" ? "#2b333c" : c.state === "missing" ? "transparent" : STATUS.warning }}
                        />
                        {c.index}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="text-sm text-ink2">No cell voltages in the latest telemetry row.</p>
              )}
            </Card>

            <Card title="Pack temperature" subtitle="Six sensors in the battery pack, latest reading">
              {temps.length > 0 ? <TempHeatmap temps={temps} /> : <p className="text-sm text-ink2">Waiting for telemetry.</p>}
            </Card>
          </div>
        </>
      )}
    </>
  );
}
