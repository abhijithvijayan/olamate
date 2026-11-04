import { Link } from "react-router-dom";
import { api } from "../api/client";
import { usePolling } from "../api/hooks";
import { Card, PageHeader } from "../components/Card";
import { SocGauge } from "../components/SocGauge";
import { Readout, StatTile } from "../components/StatTile";
import { CollectorBadge, EmptyState, ErrorState, LoadingState } from "../components/States";
import { DRIVE_MODE_COLORS, DRIVE_MODE_NAMES } from "../api/types";
import { fmtAgo, fmtDateTime, fmtDuration, fmtKm, fmtNum, socColor } from "../lib/format";

export function Overview() {
  const status = usePolling(() => api.status(), 2000);
  const rides = usePolling(() => api.sessions("ride", 1), 10000);
  const stats = usePolling(() => api.stats(), 30000);

  const s = status.data;
  const lastRide = rides.data?.[0];

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle="Current state of the scooter"
        action={s ? <CollectorBadge running={s.collector_running} ageSeconds={fmtAgo(s.age_seconds)} /> : undefined}
      />

      {status.error && <ErrorState error={status.error} onRetry={status.refresh} />}
      {!status.error && status.loading && !s && <LoadingState label="Reading latest telemetry" />}
      {!status.error && status.empty && !s && (
        <EmptyState title="No telemetry yet">
          Start the collector with the scooter on the same network and this page fills in within a few seconds.
        </EmptyState>
      )}

      {s && (
        <div className="grid gap-4 lg:grid-cols-[auto_1fr]">
          <Card className="flex flex-col items-center justify-center lg:w-72">
            <SocGauge soc={s.soc} caption={`${fmtNum(s.range_normal)} km range in Normal`} />
            <div className="mt-2 grid w-full grid-cols-3 gap-2 text-center text-xs text-ink2">
              <div>
                <div className="tnum text-base text-ink">{fmtNum(s.range_sport)}</div>
                Sport km
              </div>
              <div>
                <div className="tnum text-base text-ink">{fmtNum(s.range_normal)}</div>
                Normal km
              </div>
              <div>
                <div className="tnum text-base text-ink">{fmtNum(s.range_hyper)}</div>
                Hyper km
              </div>
            </div>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="Speed" value={fmtNum(s.speed, 0)} unit="km/h" size="lg" hint={`${fmtNum(s.motor_rpm)} rpm`} />
            <StatTile
              label="Mode"
              value={s.drive_mode !== null && s.drive_mode !== undefined ? (DRIVE_MODE_NAMES[s.drive_mode] ?? `Mode ${s.drive_mode}`) : "–"}
              size="lg"
              accent={s.drive_mode !== null && s.drive_mode !== undefined ? DRIVE_MODE_COLORS[DRIVE_MODE_NAMES[s.drive_mode] ?? ""] : undefined}
            />
            <StatTile label="Odometer" value={fmtNum((s.odometer ?? 0) / 1000, 1)} unit="km" size="lg" hint={s.side_stand ? "Side stand down" : "Side stand up"} />
            <StatTile
              label="Health"
              value={fmtNum(s.soh, 0)}
              unit="% SOH"
              size="lg"
              hint={<Link to="/battery" className="text-ink2 underline-offset-2 hover:underline">Battery details</Link>}
            />

            <Card title="Battery" className="sm:col-span-2 lg:col-span-2">
              <Readout label="Pack voltage" value={fmtNum(s.voltage, 2)} unit="V" />
              <Readout label="Current" value={fmtNum(s.current, 1)} unit="A" />
              <Readout label="Power" value={s.voltage !== null && s.current !== null ? fmtNum((s.voltage * s.current) / 1000, 2) : "–"} unit="kW" />
              <Readout label="Cell spread" value={fmtNum(s.cell_spread_mV, 0)} unit="mV" />
            </Card>

            <Card title="Temperatures" className="sm:col-span-2 lg:col-span-2">
              <div className="grid grid-cols-3 gap-3">
                <TempStat label="Battery" value={s.temp_effective} />
                <TempStat label="Motor" value={s.temp_motor} />
                <TempStat label="Controller" value={s.temp_mcu} />
              </div>
              <p className="mt-3 text-xs text-ink3">
                Pack sensors {fmtNum(s.temp_min, 1)}° to {fmtNum(s.temp_max, 1)}°. Regen {s.regen_availability ? "available" : "off"}, hill hold {s.hill_hold ? "on" : "off"}.
              </p>
            </Card>
          </div>
        </div>
      )}

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Last ride" action={lastRide ? <Link to={`/rides/${lastRide.id}`} className="text-xs text-ink2 hover:text-ink">Open</Link> : undefined}>
          {rides.error && <p className="text-sm text-ink2">Could not load rides.</p>}
          {!rides.error && !lastRide && <p className="text-sm text-ink2">No rides recorded yet. Rides are detected automatically when the scooter moves.</p>}
          {lastRide && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Mini label={lastRide.in_progress ? "Started" : "When"} value={fmtDateTime(lastRide.start_time)} />
              <Mini label="Distance" value={fmtKm(lastRide.distance_m)} />
              <Mini label="Duration" value={lastRide.in_progress ? "In progress" : fmtDuration(lastRide.duration_s)} />
              <Mini
                label="Battery"
                value={
                  lastRide.start_soc !== null && lastRide.end_soc !== null
                    ? `${fmtNum(lastRide.start_soc)}% → ${fmtNum(lastRide.end_soc)}%`
                    : "–"
                }
                accent={socColor(lastRide.end_soc)}
              />
            </div>
          )}
        </Card>

        <Card title="All time">
          {stats.data ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Mini label="Rides" value={fmtNum(stats.data.total_rides)} />
              <Mini label="Distance" value={fmtKm(stats.data.total_distance_m, 0)} />
              <Mini label="Charges" value={fmtNum(stats.data.total_charges)} />
              <Mini label="Efficiency" value={stats.data.avg_efficiency_wh_per_km ? `${fmtNum(stats.data.avg_efficiency_wh_per_km)} Wh/km` : "–"} />
            </div>
          ) : (
            <p className="text-sm text-ink2">{stats.error ? "Could not load stats." : "Loading"}</p>
          )}
        </Card>
      </div>
    </>
  );
}

function TempStat({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <div className="text-xs text-ink3">{label}</div>
      <div className="tnum mt-0.5 text-2xl font-medium text-temp">
        {fmtNum(value, 1)}
        <span className="ml-0.5 text-sm font-normal text-ink3">°C</span>
      </div>
    </div>
  );
}

function Mini({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div>
      <div className="text-xs text-ink3">{label}</div>
      <div className="tnum mt-0.5 text-sm font-medium" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
    </div>
  );
}
