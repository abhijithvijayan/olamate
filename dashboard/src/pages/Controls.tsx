import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { CommandCategory, CommandResult, ScooterConnection, ScooterCommand } from "../api/types";
import { Card, PageHeader } from "../components/Card";
import { ErrorState, LoadingState } from "../components/States";

function ConnectionBadge({ conn }: { conn: ScooterConnection }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink2">
      <span className={`h-2 w-2 rounded-full ${conn.connected ? "bg-soc-high" : "bg-soc-low"}`} />
      {conn.connected ? "Connected" : "Disconnected"}
    </span>
  );
}

function CommandButton({
  cmd,
  disabled,
  onSend,
}: {
  cmd: ScooterCommand;
  disabled: boolean;
  onSend: (id: string) => void;
}) {
  return (
    <button
      onClick={() => onSend(cmd.id)}
      disabled={disabled || cmd.blocked}
      className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
        cmd.blocked
          ? "cursor-not-allowed border-line/50 bg-surface/50 text-ink3"
          : disabled
            ? "cursor-wait border-line bg-surface text-ink2"
            : "border-line bg-surface text-ink hover:border-ink3 hover:bg-raised active:bg-raised/80"
      }`}
      title={cmd.blocked ? `Blocked: ${cmd.name} is dangerous` : cmd.name}
    >
      <div className="flex items-center justify-between gap-2">
        <span>{cmd.name}</span>
        <span className="text-xs text-ink3">{cmd.hex}</span>
      </div>
    </button>
  );
}

export function Controls() {
  const [conn, setConn] = useState<ScooterConnection | null>(null);
  const [categories, setCategories] = useState<CommandCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [sending, setSending] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<CommandResult | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [c, cmds] = await Promise.all([
        api.scooterConnection(),
        api.scooterCommands(),
      ]);
      setConn(c);
      setCategories(cmds);
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSend = async (commandId: string) => {
    setSending(commandId);
    setLastResult(null);
    setLastError(null);
    try {
      const result = await api.sendCommand(commandId);
      setLastResult(result);
    } catch (e) {
      if (e instanceof ApiError) {
        setLastError(e.message);
      } else {
        setLastError(String(e));
      }
    } finally {
      setSending(null);
    }
  };

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (loading && !conn) return <LoadingState label="Loading commands" />;

  const disconnected = !conn?.connected;

  return (
    <>
      <PageHeader
        title="Controls"
        subtitle="Send CommandFromHMI commands via CAN 0x6BC"
        action={conn ? <ConnectionBadge conn={conn} /> : undefined}
      />

      {disconnected && (
        <div className="mb-4 rounded-card border border-soc-low/40 bg-surface px-5 py-4">
          <p className="text-sm font-medium text-ink">Scooter not reachable</p>
          <p className="mt-1 text-sm text-ink2">
            Commands require a live connection. Set <code className="rounded bg-raised px-1.5 py-0.5 text-xs">SCOOTER_IP</code> and ensure the scooter is on the same network.
          </p>
        </div>
      )}

      {(lastResult || lastError) && (
        <div className={`mb-4 rounded-card border px-5 py-3 text-sm ${
          lastError
            ? "border-soc-low/40 bg-surface text-soc-low"
            : "border-soc-high/40 bg-surface text-soc-high"
        }`}>
          {lastError
            ? lastError
            : `${lastResult!.name} sent ${lastResult!.sent}x`}
        </div>
      )}

      <div className="grid gap-4">
        {categories.map((cat) => (
          <Card key={cat.name} title={cat.name}>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4">
              {cat.commands.map((cmd) => (
                <CommandButton
                  key={cmd.id}
                  cmd={cmd}
                  disabled={disconnected || sending !== null}
                  onSend={handleSend}
                />
              ))}
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
