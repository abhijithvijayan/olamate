import { Link } from "react-router-dom";
import type { Session } from "../api/types";
import { DRIVE_MODE_COLORS } from "../api/types";
import { fmtDateTime, fmtDuration, fmtKm, fmtNum, socColor } from "../lib/format";

interface SessionListProps {
  sessions: Session[];
  basePath: "/rides" | "/charges";
}

export function SessionList({ sessions, basePath }: SessionListProps) {
  const isRide = basePath === "/rides";
  return (
    <ul className="divide-y divide-line rounded-card border border-line bg-surface">
      {sessions.map((s) => (
        <li key={s.id}>
          <Link
            to={`${basePath}/${s.id}`}
            className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 px-4 py-3.5 hover:bg-raised/50 md:grid-cols-[1.6fr_1fr_1fr_1fr_1fr_auto]"
          >
            <div>
              <div className="flex items-center gap-2 text-sm font-medium">
                {fmtDateTime(s.start_time)}
                {isRide && s.drive_mode_name && s.drive_mode_name !== "Parked" && (
                  <span
                    className="inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white"
                    style={{ background: DRIVE_MODE_COLORS[s.drive_mode_name] ?? "#6b7280" }}
                  >
                    {s.drive_mode_name}
                  </span>
                )}
              </div>
              <div className="text-xs text-ink3">
                {s.in_progress ? "In progress" : fmtDuration(s.duration_s)}
              </div>
            </div>
            <Cell label={isRide ? "Distance" : "Energy"} value={isRide ? fmtKm(s.distance_m) : s.energy_wh !== null ? `${fmtNum(s.energy_wh)} Wh` : "–"} />
            <SocCell session={s} />
            <Cell label={isRide ? "Avg speed" : "Start"} value={isRide ? `${fmtNum(s.avg_speed, 1)} km/h` : `${fmtNum(s.start_soc)}%`} />
            <Cell label={isRide ? "Max speed" : "End"} value={isRide ? `${fmtNum(s.max_speed, 1)} km/h` : `${fmtNum(s.end_soc)}%`} />
            <svg viewBox="0 0 24 24" width="16" height="16" className="hidden text-ink3 md:block" aria-hidden>
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div className="hidden md:block">
      <div className="text-[11px] text-ink3">{label}</div>
      <div className="tnum text-sm">{value}</div>
    </div>
  );
}

function SocCell({ session }: { session: Session }) {
  const delta = session.soc_delta;
  const label = session.type === "ride" ? "Used" : "Gained";
  const text = delta === null ? "–" : `${delta > 0 ? "+" : ""}${fmtNum(delta, 1)}%`;
  return (
    <div className="text-right md:text-left">
      <div className="text-[11px] text-ink3">{label}</div>
      <div className="tnum text-sm">
        <span className="mr-1.5 inline-block h-2 w-2 rounded-full align-middle" style={{ background: socColor(session.end_soc) }} />
        {text}
      </div>
    </div>
  );
}
