import { fmtNum, socColor } from "../lib/format";

interface SocGaugeProps {
  soc: number | null;
  size?: number;
  caption?: string;
}

export function SocGauge({ soc, size = 240, caption }: SocGaugeProps) {
  const r = 44;
  const startAngle = 135;
  const sweep = 270;
  const pct = soc === null ? 0 : Math.max(0, Math.min(100, soc)) / 100;
  const color = socColor(soc);
  const c = 2 * Math.PI * r;
  const trackLen = c * (sweep / 360);
  const fillLen = trackLen * pct;

  return (
    <figure className="flex flex-col items-center" style={{ width: size }}>
      <svg viewBox="0 0 100 100" width={size} height={size} role="img" aria-label={`State of charge ${fmtNum(soc)} percent`}>
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke="#232a32"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${trackLen} ${c}`}
          transform={`rotate(${startAngle} 50 50)`}
        />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${fillLen} ${c}`}
          transform={`rotate(${startAngle} 50 50)`}
          style={{ transition: "stroke-dasharray 600ms ease, stroke 600ms ease" }}
        />
        <text x="50" y="52" textAnchor="middle" fontSize="26" fontWeight="500" fill="#eef1f4">
          {soc === null ? "–" : fmtNum(soc)}
        </text>
        <text x="50" y="64" textAnchor="middle" fontSize="7" fill="#6f7a86">
          % charge
        </text>
      </svg>
      {caption && <figcaption className="-mt-4 text-xs text-ink3">{caption}</figcaption>}
    </figure>
  );
}
