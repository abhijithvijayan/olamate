import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { DIDEntry, DTCEntry, DTCResult, ECUInfo, ScooterConnection, ScooterInfo, UDSReadResult } from "../api/types";
import { Card, PageHeader } from "../components/Card";
import { ErrorState, LoadingState } from "../components/States";

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-line/50 py-2.5 last:border-0">
      <span className="text-sm text-ink2">{label}</span>
      <span className="tnum text-sm font-medium text-ink break-all text-right">{value ?? "–"}</span>
    </div>
  );
}

function ConnectionBadge({ conn }: { conn: ScooterConnection }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink2">
      <span className={`h-2 w-2 rounded-full ${conn.connected ? "bg-soc-high" : "bg-soc-low"}`} />
      {conn.connected ? `Connected (${conn.address})` : conn.error ?? "Disconnected"}
    </span>
  );
}

function UDSReadSection({ conn, ecus, dids }: { conn: ScooterConnection | null; ecus: ECUInfo[]; dids: DIDEntry[] }) {
  const [ecu, setEcu] = useState("vcu");
  const [didMode, setDidMode] = useState<"name" | "hex">("name");
  const [didName, setDidName] = useState("vin");
  const [didHex, setDidHex] = useState("");
  const [reading, setReading] = useState(false);
  const [result, setResult] = useState<UDSReadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filteredDids = dids.filter((d) => d.ecus.includes(ecu));

  const handleRead = async () => {
    setReading(true);
    setResult(null);
    setError(null);
    try {
      const opts = didMode === "name" ? { did_name: didName } : { did_hex: didHex };
      const r = await api.readDid(ecu, opts);
      setResult(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setReading(false);
    }
  };

  const disconnected = !conn?.connected;

  return (
    <Card title="UDS Read DID" subtitle="Read a Data Identifier from an ECU">
      <div className="flex flex-wrap gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink3">ECU</label>
          <select
            value={ecu}
            onChange={(e) => setEcu(e.target.value)}
            className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm text-ink"
          >
            {ecus.map((e) => (
              <option key={e.id} value={e.id}>{e.id.toUpperCase()} — {e.name}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink3">DID</label>
          <div className="flex gap-2">
            <select
              value={didMode}
              onChange={(e) => setDidMode(e.target.value as "name" | "hex")}
              className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm text-ink"
            >
              <option value="name">By name</option>
              <option value="hex">By hex</option>
            </select>
            {didMode === "name" ? (
              <select
                value={didName}
                onChange={(e) => setDidName(e.target.value)}
                className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm text-ink min-w-[180px]"
              >
                {filteredDids.map((d) => (
                  <option key={d.name} value={d.name}>{d.name} ({d.did_hex})</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={didHex}
                onChange={(e) => setDidHex(e.target.value)}
                placeholder="e.g. F190"
                className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm text-ink w-28"
              />
            )}
          </div>
        </div>

        <div className="flex items-end">
          <button
            onClick={handleRead}
            disabled={reading || disconnected}
            className="rounded-md bg-raised px-4 py-1.5 text-sm font-medium text-ink hover:bg-raised/70 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {reading ? "Reading…" : "Read"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-3 rounded-md border border-soc-low/40 bg-surface px-4 py-2 text-sm text-soc-low">
          {error}
        </div>
      )}

      {result && (
        <div className={`mt-3 rounded-md border px-4 py-3 text-sm ${
          result.success ? "border-soc-high/40" : "border-soc-low/40"
        }`}>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-ink2">
            <span>ECU: <span className="font-medium text-ink">{result.ecu.toUpperCase()}</span></span>
            <span>DID: <span className="font-medium text-ink">{result.did}</span></span>
          </div>
          {result.error && (
            <p className="mt-1 text-soc-low">{result.error}</p>
          )}
          {result.data_hex && (
            <div className="mt-2 space-y-1">
              <div className="text-ink2">Hex: <code className="rounded bg-raised px-1.5 py-0.5 font-mono text-xs text-ink">{result.data_hex}</code></div>
              {result.data_ascii && (
                <div className="text-ink2">ASCII: <code className="rounded bg-raised px-1.5 py-0.5 font-mono text-xs text-ink">{result.data_ascii}</code></div>
              )}
              {result.data_bytes && (
                <div className="text-ink2">Bytes: <code className="rounded bg-raised px-1.5 py-0.5 font-mono text-xs text-ink">[{result.data_bytes.join(", ")}]</code></div>
              )}
            </div>
          )}
          {result.raw_hex && (
            <div className="mt-1 text-xs text-ink3">Raw frame: {result.raw_hex}</div>
          )}
        </div>
      )}
    </Card>
  );
}

function DTCSection({ conn, ecus }: { conn: ScooterConnection | null; ecus: ECUInfo[] }) {
  const [ecu, setEcu] = useState("vcu");
  const [reading, setReading] = useState(false);
  const [result, setResult] = useState<DTCResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const disconnected = !conn?.connected;

  const handleRead = async () => {
    setReading(true);
    setResult(null);
    setError(null);
    try {
      const r = await api.readDtc(ecu);
      setResult(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setReading(false);
    }
  };

  return (
    <Card title="Fault Codes (DTC)" subtitle="Read Diagnostic Trouble Codes from ECUs">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink3">ECU</label>
          <select
            value={ecu}
            onChange={(e) => setEcu(e.target.value)}
            className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm text-ink"
          >
            {ecus.map((e) => (
              <option key={e.id} value={e.id}>{e.id.toUpperCase()} — {e.name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={handleRead}
          disabled={reading || disconnected}
          className="rounded-md bg-raised px-4 py-1.5 text-sm font-medium text-ink hover:bg-raised/70 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {reading ? "Reading…" : "Read DTCs"}
        </button>
      </div>

      {error && (
        <div className="mt-3 rounded-md border border-soc-low/40 bg-surface px-4 py-2 text-sm text-soc-low">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-3">
          {!result.success ? (
            <div className="rounded-md border border-soc-low/40 px-4 py-2 text-sm text-soc-low">
              {result.error}
            </div>
          ) : result.dtcs.length === 0 ? (
            <div className="rounded-md border border-soc-high/40 px-4 py-3 text-sm text-soc-high">
              No fault codes found on {ecu.toUpperCase()}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs text-ink3">
                    <th className="pb-2 pr-4">Code</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2 pr-4">Active</th>
                    <th className="pb-2">Stored</th>
                  </tr>
                </thead>
                <tbody>
                  {result.dtcs.map((dtc: DTCEntry, i: number) => (
                    <tr key={i} className="border-b border-line/50">
                      <td className="py-2 pr-4 font-mono text-ink">{dtc.code}</td>
                      <td className="py-2 pr-4 font-mono text-ink2">{dtc.status}</td>
                      <td className="py-2 pr-4">
                        <span className={`inline-block h-2 w-2 rounded-full ${dtc.active ? "bg-soc-low" : "bg-ink3/30"}`} />
                      </td>
                      <td className="py-2">
                        <span className={`inline-block h-2 w-2 rounded-full ${dtc.stored ? "bg-amber-400" : "bg-ink3/30"}`} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-xs text-ink3">{result.dtc_count} DTC(s) found</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export function Diagnostics() {
  const [conn, setConn] = useState<ScooterConnection | null>(null);
  const [info, setInfo] = useState<ScooterInfo | null>(null);
  const [ecus, setEcus] = useState<ECUInfo[]>([]);
  const [dids, setDids] = useState<DIDEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [c, e, d] = await Promise.all([
        api.scooterConnection(),
        api.scooterEcus(),
        api.scooterDids(),
      ]);
      setConn(c);
      setEcus(e);
      setDids(d);
      if (c.connected) {
        const i = await api.scooterInfo();
        setInfo(i);
      }
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (loading && !conn) return <LoadingState label="Checking scooter connection" />;

  return (
    <>
      <PageHeader
        title="Diagnostics"
        subtitle="UDS diagnostic reads, fault codes, and vehicle info"
        action={conn ? <ConnectionBadge conn={conn} /> : undefined}
      />

      {conn && !conn.connected && (
        <div className="mb-4 rounded-card border border-soc-low/40 bg-surface px-5 py-4">
          <p className="text-sm font-medium text-ink">Scooter not reachable</p>
          <p className="mt-1 text-sm text-ink2">
            {conn.error}. Set <code className="rounded bg-raised px-1.5 py-0.5 text-xs">SCOOTER_IP</code> and ensure the scooter is on the same network.
          </p>
          <button onClick={load} className="mt-3 rounded-md bg-raised px-3 py-1.5 text-sm text-ink hover:bg-raised/70">
            Retry
          </button>
        </div>
      )}

      <div className="grid gap-4">
        <UDSReadSection conn={conn} ecus={ecus} dids={dids} />
        <DTCSection conn={conn} ecus={ecus} />

        {info && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Software">
              <InfoRow label="SW Version" value={info.sw_version} />
              <InfoRow label="AOSP Version" value={info.aosp_version} />
              <InfoRow label="Certificates" value={info.certs_valid === null ? null : info.certs_valid ? "Valid" : "Invalid"} />
            </Card>

            <Card title="Operation Mode">
              <InfoRow label="Mode" value={info.operation_mode?.mode} />
              <InfoRow label="Modified By" value={info.operation_mode?.modified_by} />
              <InfoRow label="Modified" value={info.operation_mode?.modified_ts_str} />
            </Card>

            {info.sw_update_status && (
              <Card title="OTA Update Status">
                <InfoRow label="State" value={info.sw_update_status.state} />
                <InfoRow label="Message" value={info.sw_update_status.message} />
              </Card>
            )}

            {info.ecos_dyno && (
              <Card title="ECOS / Dyno Flags">
                <InfoRow label="ECOS 1" value={info.ecos_dyno.ecos1} />
                <InfoRow label="ECOS 2" value={info.ecos_dyno.ecos2} />
                <InfoRow label="Dyno" value={info.ecos_dyno.dyno} />
              </Card>
            )}

            {info.identifiers && (
              <Card title="Vehicle Identifiers" className="md:col-span-2">
                <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-ink2">
                  {(() => {
                    try {
                      return JSON.stringify(JSON.parse(info.identifiers), null, 2);
                    } catch {
                      return info.identifiers;
                    }
                  })()}
                </pre>
              </Card>
            )}
          </div>
        )}
      </div>
    </>
  );
}
