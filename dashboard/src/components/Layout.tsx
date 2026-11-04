import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;

const NAV: NavItem[] = [
  {
    to: "/",
    label: "Overview",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <path d="M4 13a8 8 0 1 1 16 0" />
        <path d="M12 13l3.5-3.5" />
        <path d="M3 19h18" />
      </svg>
    ),
  },
  {
    to: "/rides",
    label: "Rides",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <circle cx="6" cy="16" r="3" />
        <circle cx="18" cy="16" r="3" />
        <path d="M6 16l3-7h5l4 7" />
        <path d="M11 9l-1-3h3" />
      </svg>
    ),
  },
  {
    to: "/charges",
    label: "Charges",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <path d="M13 3L5 13h6l-1 8 9-11h-6z" />
      </svg>
    ),
  },
  {
    to: "/battery",
    label: "Battery",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <rect x="3" y="7" width="16" height="10" rx="2" />
        <path d="M19 10h2v4h-2" />
        <path d="M7 11v2M11 11v2M15 11v2" />
      </svg>
    ),
  },
  {
    to: "/live",
    label: "Live",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <path d="M3 12h4l3-7 4 14 3-7h4" />
      </svg>
    ),
  },
  {
    to: "/diagnostics",
    label: "Diagnostics",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <rect x="4" y="4" width="16" height="16" rx="2" />
        <path d="M9 9h6M9 12h6M9 15h4" />
      </svg>
    ),
  },
  {
    to: "/controls",
    label: "Controls",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" {...stroke} aria-hidden>
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
      </svg>
    ),
  },
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full md:flex">
      <aside className="hidden md:flex md:w-56 md:flex-col md:border-r md:border-line md:bg-surface md:px-4 md:py-6 md:sticky md:top-0 md:h-screen">
        <Brand />
        <nav className="mt-8 flex flex-col gap-1" aria-label="Main">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-raised text-ink" : "text-ink2 hover:bg-raised/60 hover:text-ink"
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="mt-auto text-xs text-ink3">Ola S1 Pro Gen 1</p>
      </aside>

      <div className="flex min-h-full flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line px-4 py-3 md:hidden">
          <Brand compact />
        </header>
        <main className="flex-1 px-4 pb-24 pt-5 md:px-8 md:pb-10 md:pt-8">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
        <nav
          className="fixed inset-x-0 bottom-0 z-20 flex border-t border-line bg-surface/95 backdrop-blur md:hidden"
          style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
          aria-label="Main"
        >
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center gap-1 py-2 text-[11px] ${isActive ? "text-ink" : "text-ink3"}`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-raised text-soc-high">
        <svg viewBox="0 0 32 32" width="18" height="18" aria-hidden>
          <path d="M9 22V10h3l4 7 4-7h3v12h-3v-7l-4 7-4-7v7z" fill="currentColor" />
        </svg>
      </span>
      <div>
        <div className="text-base font-semibold leading-none">OlaMate</div>
        {!compact && <div className="mt-1 text-xs text-ink3">Telemetry</div>}
      </div>
    </div>
  );
}
