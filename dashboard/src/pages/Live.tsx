import { api } from "../api/client";
import { usePolling } from "../api/hooks";
import { CELL_KEYS, DRIVE_MODE_COLORS, DRIVE_MODE_NAMES, PACK_TEMP_KEYS } from "../api/types";
import type { CellReading } from "../api/types";
import { Card, PageHeader } from "../components/Card";
import { CellBarChart } from "../components/charts/CellBarChart";
import { TempHeatmap } from "../components/charts/TempHeatmap";
import { Meter } from "../components/Meter";
import { StatTile } from "../components/StatTile";
import { CollectorBadge, EmptyState, ErrorState, LoadingState } from "../components/States";
import { SERIES, fmtAgo, fmtNum, socColor } from "../lib/format";

const BALANCE_THRESHOLD_MV = 20;

export function Live() {
  const status = usePolling(() => api.status(), 1000);
  const s = status.data;

  if (status.error) return <ErrorState error={status.error} onRetry={status.refresh} />;
  if (status.loading && !s) return <LoadingState label="Connecting" />;
  if (!s) {
    return (
      <>
        <PageHeader title="Live" />
        <EmptyState title="Nothing to show yet">This page updates every second once the collector is writing telemetry.</EmptyState>
      </>
    );
  }

  const voltages = CELL_KEYS.map((k) => s[k]);
  const valid = voltages.filter((v): v is number => v !== null && v > 0);
  const avg = valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null;
  const cells: CellReading[] = voltages.map((v, i) => {
    if (v === null || v <= 0 || avg === null) return { index: i + 1, voltage: null, deviation_mV: null, state: "missing" };
    const dev = (v - avg) * 1000;
    const state = Math.abs(dev) > BALANCE_THRESHOLD_MV ? (dev > 0 ? "high" : "low") : "ok";
    return { index: i + 1, voltage: v, deviation_mV: Math.round(dev * 10) / 10, state };
  });
  const power = s.voltage !== null && s.current !== null ? (s.voltage * s.current) / 1000 : null;

  const temps = [
    ...PACK_TEMP_KEYS.map((k, i) => ({ label: `Pack ${i + 1}`, value: s[k] })),
    { label: "Controller", value: s.temp_mcu },
    { label: "Motor", value: s.temp_motor },
  ];

  return (
    <>
      <PageHeader title="Live" subtitle="Refreshes every second" action={<CollectorBadge running={s.collector_running} ageSeconds={fmtAgo(s.age_seconds)} />} />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatTile label="Speed" value={fmtNum(s.speed, 0)} unit="km/h" size="lg" />
        <StatTile
          label="Mode"
          value={s.drive_mode !== null && s.drive_mode !== undefined ? (DRIVE_MODE_NAMES[s.drive_mode] ?? `Mode ${s.drive_mode}`) : "–"}
          size="lg"
          accent={s.drive_mode !== null && s.drive_mode !== undefined ? DRIVE_MODE_COLORS[DRIVE_MODE_NAMES[s.drive_mode] ?? ""] : undefined}
        />
        <StatTile label="Motor" value={fmtNum(s.motor_rpm)} unit="rpm" size="lg" />
        <StatTile label="Charge" value={fmtNum(s.soc, 1)} unit="%" size="lg" accent={socColor(s.soc)} />
        <StatTile label="Power" value={fmtNum(power, 2)} unit="kW" size="lg" hint={power !== null ? (s.current !== null && s.current > 0 ? "Charging" : power < 0 ? "Regen" : undefined) : undefined} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card title="Cell voltages" subtitle={avg !== null ? `Average ${fmtNum(avg, 3)} V, spread ${fmtNum(s.cell_spread_mV, 0)} mV` : undefined}>
          {valid.length > 0 ? <CellBarChart cells={cells} avg={avg} height={240} /> : <p className="text-sm text-ink2">No cell voltages in the latest row.</p>}
        </Card>

        <Card title="Pack">
          <div className="flex flex-col gap-5">
            <Meter label="Voltage" value={s.voltage} min={42} max={59} unit="V" digits={2} color={SERIES.violet} />
            <Meter label="Current" value={s.current} min={-30} max={90} unit="A" digits={1} color={SERIES.orange} center={0} />
            <div className="grid grid-cols-2 gap-3 text-xs text-ink2">
              <div>
                <div className="text-ink3">Discharge limit</div>
                <div className="tnum text-sm text-ink">{fmtNum(s.discharge_power_limit)} W</div>
              </div>
              <div>
                <div className="text-ink3">Regen limit</div>
                <div className="tnum text-sm text-ink">{fmtNum(s.regen_power_limit)} W</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="mt-4">
        <Card title="Temperatures" subtitle="Six pack sensors plus controller and motor">
          <TempHeatmap temps={temps} columns={4} max={80} />
        </Card>
      </div>
    </>
  );
}
