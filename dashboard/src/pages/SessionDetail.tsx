import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { usePolling } from "../api/hooks";
import type { SessionPoint, SessionType } from "../api/types";
import { DRIVE_MODE_COLORS } from "../api/types";
import { Card, PageHeader } from "../components/Card";
import { TimeSeriesChart } from "../components/charts/TimeSeriesChart";
import { StatTile } from "../components/StatTile";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { SERIES, fmtDateTime, fmtDuration, fmtElapsed, fmtKm, fmtNum, socColor } from "../lib/format";

type Point = SessionPoint & { t: number };

export function SessionDetail({ type }: { type: SessionType }) {
  const { id } = useParams();
  const sessionId = Number(id);
  const detail = usePolling(() => api.session(sessionId, 800), null, [sessionId]);
  const inProgress = detail.data?.session.in_progress ?? false;
  const live = usePolling(() => api.session(sessionId, 800), inProgress ? 5000 : null, [sessionId, inProgress]);
  const data = live.data ?? detail.data;

  const points = useMemo<Point[]>(() => {
    if (!data) return [];
    const t0 = data.session.start_time;
    return data.telemetry.map((p) => ({ ...p, t: p.timestamp - t0 }));
  }, [data]);

  const isRide = (data?.session.type ?? type) === "ride";
  const backPath = isRide ? "/rides" : "/charges";
  const backLabel = isRide ? "All rides" : "All charges";

  if (detail.error) return <ErrorState error={detail.error} onRetry={detail.refresh} />;
  if (detail.loading && !data) return <LoadingState label="Loading session" />;
  if (!data) {
    return (
      <EmptyState title="Session not found">
        <Link to={backPath} className="underline">{backLabel}</Link>
      </EmptyState>
    );
  }

  const s = data.session;
  const socRange = s.start_soc !== null && s.end_soc !== null ? `${fmtNum(s.start_soc)}% → ${fmtNum(s.end_soc)}%` : "–";

  return (
    <>
      <Link to={backPath} className="mb-3 inline-flex items-center gap-1 text-sm text-ink2 hover:text-ink">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
        {backLabel}
      </Link>
      <PageHeader
        title={
          <>
            {`${isRide ? "Ride" : "Charge"} on ${fmtDateTime(s.start_time)}`}
            {isRide && s.drive_mode_name && s.drive_mode_name !== "Parked" && (
              <span
                className="ml-2 inline-block translate-y-[-2px] rounded px-2 py-0.5 align-middle text-xs font-semibold leading-none text-white"
                style={{ background: DRIVE_MODE_COLORS[s.drive_mode_name] ?? "#6b7280" }}
              >
                {s.drive_mode_name}
              </span>
            )}
          </>
        }
        subtitle={s.in_progress ? "Still in progress, updating every few seconds" : `Ended ${fmtDateTime(s.end_time)}`}
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile label="Duration" value={fmtDuration(s.duration_s)} />
        {isRide ? (
          <StatTile label="Distance" value={fmtNum((s.distance_m ?? 0) / 1000, 2)} unit="km" />
        ) : (
          <StatTile label="Energy added" value={fmtNum(s.energy_wh)} unit="Wh" />
        )}
        <StatTile label="Battery" value={socRange} accent={socColor(s.end_soc)} hint={s.soc_delta !== null ? `${s.soc_delta > 0 ? "+" : ""}${fmtNum(s.soc_delta, 1)} points` : undefined} />
        {isRide ? (
          <StatTile label="Average / top speed" value={`${fmtNum(s.avg_speed, 0)} / ${fmtNum(s.max_speed, 0)}`} unit="km/h" hint={s.efficiency_wh_per_km ? `${fmtNum(s.efficiency_wh_per_km)} Wh/km` : undefined} />
        ) : (
          <StatTile label="Average / peak pack temperature" value={`${fmtNum(s.avg_temp, 0)} / ${fmtNum(s.max_temp, 0)}`} unit="°C" />
        )}
      </div>

      {points.length === 0 ? (
        <div className="mt-4">
          <EmptyState title="No telemetry stored for this session">The session was recorded but no per-second rows reference it.</EmptyState>
        </div>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {isRide ? (
            <Card title="Speed" subtitle="km/h over elapsed time">
              <TimeSeriesChart data={points} xKey="t" xFormatter={fmtElapsed} unit="km/h" digits={0} series={[{ key: "speed", name: "Speed", color: SERIES.blue }]} yDomain={[0, "auto"]} />
            </Card>
          ) : (
            <Card title="State of charge" subtitle="% over elapsed time">
              <TimeSeriesChart data={points} xKey="t" xFormatter={fmtElapsed} unit="%" series={[{ key: "soc", name: "SOC", color: SERIES.aqua }]} />
            </Card>
          )}
          {isRide ? (
            <Card title="Battery drain" subtitle="% state of charge">
              <TimeSeriesChart data={points} xKey="t" xFormatter={fmtElapsed} unit="%" series={[{ key: "soc", name: "SOC", color: SERIES.aqua }]} />
            </Card>
          ) : (
            <Card title="Pack voltage" subtitle="V">
              <TimeSeriesChart data={points} xKey="t" xFormatter={fmtElapsed} unit="V" digits={2} series={[{ key: "voltage", name: "Voltage", color: SERIES.violet }]} />
            </Card>
          )}
          <Card title="Temperatures" subtitle="°C">
            <TimeSeriesChart
              data={points}
              xKey="t"
              xFormatter={fmtElapsed}
              unit="°C"
              series={
                isRide
                  ? [
                      { key: "temp_effective", name: "Battery", color: SERIES.blue },
                      { key: "temp_motor", name: "Motor", color: SERIES.orange },
                      { key: "temp_mcu", name: "Controller", color: SERIES.aqua },
                    ]
                  : [{ key: "temp_effective", name: "Battery", color: SERIES.blue }]
              }
            />
          </Card>
          {isRide ? (
            <Card title="Route" subtitle="GPS logging is not wired up yet">
              <div className="grid h-[220px] place-items-center rounded-lg border border-dashed border-line bg-page/60 text-center text-sm text-ink3">
                <div>
                  Map appears here once the collector records position.
                  <div className="mt-1 text-xs">{fmtKm(s.distance_m)} ridden according to the odometer.</div>
                </div>
              </div>
            </Card>
          ) : (
            <Card title="Charge current" subtitle="A, positive means charging into the pack">
              <TimeSeriesChart data={points} xKey="t" xFormatter={fmtElapsed} unit="A" series={[{ key: "current", name: "Current", color: SERIES.orange }]} />
            </Card>
          )}
        </div>
      )}
    </>
  );
}
