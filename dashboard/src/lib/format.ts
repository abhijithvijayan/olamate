export function fmtNum(v: number | null | undefined, digits = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function fmtKm(meters: number | null | undefined, digits = 1): string {
  if (meters === null || meters === undefined) return "–";
  return `${fmtNum(meters / 1000, digits)} km`;
}

export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "–";
  const s = Math.round(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

export function fmtAgo(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "–";
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)} h ago`;
  return `${Math.round(seconds / 86400)} d ago`;
}

const dateTime = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

const timeOnly = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" });
const dayOnly = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short" });

export function fmtDateTime(ts: number | null | undefined): string {
  if (!ts) return "–";
  return dateTime.format(new Date(ts * 1000));
}

export function fmtTime(ts: number): string {
  return timeOnly.format(new Date(ts * 1000));
}

export function fmtDay(ts: number): string {
  return dayOnly.format(new Date(ts * 1000));
}

export function fmtElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m >= 60) return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}h`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export type SocBand = "high" | "mid" | "low";

export function socBand(soc: number | null | undefined): SocBand {
  if (soc === null || soc === undefined) return "mid";
  if (soc >= 50) return "high";
  if (soc >= 20) return "mid";
  return "low";
}

export const SOC_COLORS: Record<SocBand, string> = {
  high: "#3ecf6a",
  mid: "#f2b43a",
  low: "#e5484d",
};

export function socColor(soc: number | null | undefined): string {
  return SOC_COLORS[socBand(soc)];
}

export const SERIES = {
  blue: "#3987e5",
  orange: "#d95926",
  aqua: "#199e70",
  yellow: "#c98500",
  violet: "#9085e9",
  magenta: "#d55181",
} as const;

export const STATUS = {
  good: "#3ecf6a",
  warning: "#f2b43a",
  critical: "#e5484d",
} as const;

export function tempColor(temp: number, min = 20, max = 55): string {
  const t = Math.min(1, Math.max(0, (temp - min) / (max - min)));
  const stops: [number, string][] = [
    [0, "#184f95"],
    [0.5, "#2a78d6"],
    [1, "#86b6ef"],
  ];
  for (let i = 1; i < stops.length; i++) {
    const [p1, c1] = stops[i - 1]!;
    const [p2, c2] = stops[i]!;
    if (t <= p2) return mix(c1, c2, (t - p1) / (p2 - p1));
  }
  return stops[stops.length - 1]![1];
}

function mix(a: string, b: string, t: number): string {
  const pa = hex(a);
  const pb = hex(b);
  const c = pa.map((v, i) => Math.round(v + (pb[i]! - v) * t));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

function hex(h: string): number[] {
  return [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
}
