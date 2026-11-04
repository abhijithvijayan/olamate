export type CellKey =
  | "cell_1" | "cell_2" | "cell_3" | "cell_4" | "cell_5" | "cell_6" | "cell_7"
  | "cell_8" | "cell_9" | "cell_10" | "cell_11" | "cell_12" | "cell_13" | "cell_14";

export type PackTempKey =
  | "temp_pack_1" | "temp_pack_2" | "temp_pack_3"
  | "temp_pack_4" | "temp_pack_5" | "temp_pack_6";

export const CELL_KEYS: CellKey[] = [
  "cell_1", "cell_2", "cell_3", "cell_4", "cell_5", "cell_6", "cell_7",
  "cell_8", "cell_9", "cell_10", "cell_11", "cell_12", "cell_13", "cell_14",
];

export const PACK_TEMP_KEYS: PackTempKey[] = [
  "temp_pack_1", "temp_pack_2", "temp_pack_3",
  "temp_pack_4", "temp_pack_5", "temp_pack_6",
];

export interface Telemetry extends Record<CellKey, number | null>, Record<PackTempKey, number | null> {
  id: number;
  timestamp: number;
  session_id: number | null;
  soc: number | null;
  soh: number | null;
  voltage: number | null;
  current: number | null;
  regen_power_limit: number | null;
  discharge_power_limit: number | null;
  cell_min: number | null;
  cell_max: number | null;
  cell_spread_mV: number | null;
  temp_effective: number | null;
  temp_min: number | null;
  temp_max: number | null;
  temp_mcu: number | null;
  temp_motor: number | null;
  speed: number | null;
  motor_rpm: number | null;
  odometer: number | null;
  range_normal: number | null;
  range_sport: number | null;
  range_hyper: number | null;
  side_stand: number | null;
  regen_availability: number | null;
  hill_hold: number | null;
  drive_mode: number | null;
}

export interface Status extends Telemetry {
  age_seconds: number;
  collector_running: boolean;
}

export type SessionType = "ride" | "charge";

export interface Session {
  id: number;
  type: SessionType;
  start_time: number;
  end_time: number | null;
  start_soc: number | null;
  end_soc: number | null;
  start_odometer: number | null;
  end_odometer: number | null;
  distance_m: number | null;
  energy_wh: number | null;
  avg_speed: number | null;
  max_speed: number | null;
  avg_temp: number | null;
  max_temp: number | null;
  in_progress: boolean;
  duration_s: number;
  soc_delta: number | null;
  efficiency_wh_per_km: number | null;
  drive_mode: number | null;
  drive_mode_name: string | null;
}

export const DRIVE_MODE_NAMES: Record<number, string> = {
  0: "Parked",
  2: "Normal",
  3: "Sport",
  4: "Custom",
  5: "Reverse",
  6: "Eco",
  7: "Hyper",
};

export const DRIVE_MODE_COLORS: Record<string, string> = {
  Eco: "#22c55e",
  Normal: "#3b82f6",
  Sport: "#f97316",
  Hyper: "#ef4444",
  Custom: "#a855f7",
  Reverse: "#6b7280",
  Parked: "#6b7280",
};

export interface SessionPoint {
  timestamp: number;
  soc: number | null;
  voltage: number | null;
  current: number | null;
  speed: number | null;
  motor_rpm: number | null;
  odometer: number | null;
  temp_effective: number | null;
  temp_motor: number | null;
  temp_mcu: number | null;
  cell_spread_mV: number | null;
  drive_mode: number | null;
}

export interface SessionDetail {
  session: Session;
  telemetry: SessionPoint[];
}

export interface Snapshot {
  id?: number;
  timestamp: number;
  soc: number | null;
  soh: number | null;
  voltage: number | null;
  cell_spread_mV: number | null;
  odometer: number | null;
  temp_effective: number | null;
  cells: number[];
}

export interface BatteryHealth {
  latest: Snapshot | null;
  trend: Snapshot[];
  source: "snapshots" | "telemetry";
}

export type CellState = "ok" | "high" | "low" | "missing";

export interface CellReading {
  index: number;
  voltage: number | null;
  deviation_mV: number | null;
  state: CellState;
}

export interface CellReport {
  timestamp: number | null;
  cells: CellReading[];
  min: number | null;
  max: number | null;
  avg: number | null;
  spread_mV: number | null;
  balancing_needed: boolean;
}

export interface Stats {
  total_rides: number;
  total_charges: number;
  total_distance_m: number;
  total_energy_wh: number;
  total_ride_time_s: number;
  avg_efficiency_wh_per_km: number | null;
  avg_ride_distance_m: number | null;
  longest_ride_m: number | null;
  odometer_m: number | null;
  soh: number | null;
  first_seen: number | null;
  last_seen: number | null;
  telemetry_rows: number;
}

// --- Diagnostics / Scooter types ---

export interface ScooterConnection {
  connected: boolean;
  address: string | null;
  error?: string;
}

export interface OperationMode {
  mode: string;
  mode_value: number;
  modified_ts: number | null;
  modified_ts_str: string | null;
  modified_by: string | null;
}

export interface SwUpdateStatus {
  state: string;
  state_value: number;
  message: string | null;
}

export interface EcosDyno {
  ecos1: string | null;
  ecos2: string | null;
  dyno: string | null;
}

export interface ScooterInfo {
  sw_version: string | null;
  aosp_version: string | null;
  operation_mode: OperationMode | null;
  identifiers: string | null;
  ecos_dyno: EcosDyno | null;
  certs_valid: boolean | null;
  sw_update_status: SwUpdateStatus | null;
}

export interface ScooterCommand {
  id: string;
  name: string;
  hex: string;
  blocked: boolean;
}

export interface CommandCategory {
  name: string;
  commands: ScooterCommand[];
}

export interface CommandResult {
  ok: boolean;
  command: string;
  name: string;
  hex: string;
  sent: number;
  target: number;
  error?: string;
}

// --- UDS Diagnostics types ---

export interface ECUInfo {
  id: string;
  name: string;
  request_can_id: string;
  response_can_id: string;
}

export interface DIDEntry {
  name: string;
  did_hex: string;
  did: number;
  description: string;
  ecus: string[];
  category: string;
  category_label: string;
}

export interface UDSReadResult {
  success: boolean;
  ecu: string;
  did: string;
  description?: string;
  error?: string;
  raw_hex?: string;
  data_hex?: string;
  data_ascii?: string;
  data_bytes?: number[];
  nrc?: number;
  nrc_name?: string;
  service?: string;
}

export interface DTCEntry {
  code: string;
  status: string;
  active: boolean;
  stored: boolean;
}

export interface DTCResult {
  success: boolean;
  ecu: string;
  ecu_name?: string;
  error?: string;
  raw_hex?: string;
  dtc_count?: number;
  dtcs: DTCEntry[];
}
