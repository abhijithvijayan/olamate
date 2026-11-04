import type {
  BatteryHealth,
  CellReport,
  Session,
  SessionDetail,
  SessionType,
  Stats,
  Status,
  Telemetry,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NoDataError extends ApiError {
  constructor(message = "No data recorded yet") {
    super(message, 404);
    this.name = "NoDataError";
  }
}

const BASE = import.meta.env.VITE_API_URL ?? "";

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (res.status === 404) {
    let detail = "Not found";
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    throw new NoDataError(detail);
  }
  if (!res.ok) throw new ApiError(`${res.status} ${res.statusText}`, res.status);
  return (await res.json()) as T;
}

export const api = {
  status: () => get<Status>("/api/status"),
  telemetry: (opts: { from?: number; to?: number; limit?: number } = {}) =>
    get<Telemetry[]>("/api/telemetry", opts),
  sessions: (type?: SessionType, limit = 20) => get<Session[]>("/api/sessions", { type, limit }),
  session: (id: number, points = 600) => get<SessionDetail>(`/api/sessions/${id}`, { points }),
  batteryHealth: (limit = 30) => get<BatteryHealth>("/api/battery/health", { limit }),
  batteryCells: () => get<CellReport>("/api/battery/cells"),
  stats: () => get<Stats>("/api/stats"),
};
