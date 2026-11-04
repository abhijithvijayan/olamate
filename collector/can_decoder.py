"""
CAN frame decoder for Ola S1 Pro Gen 1.

Decodes raw CAN bus frames into named signals with physical values.
Signal definitions from the community CAN database (226 messages, 1260 signals).
This module covers the most important signals for telemetry logging.

All signals use Intel (little-endian) byte order.
Formula: physical_value = raw_value * scaling + offset
"""

import struct
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Signal:
    name: str
    start_bit: int
    bit_length: int
    scaling: float = 1.0
    offset: float = 0.0
    unit: str = ""
    signed: bool = False


@dataclass
class DecodedFrame:
    can_id: int
    name: str
    signals: dict = field(default_factory=dict)
    timestamp: float = 0.0


def extract_signal(data: bytes, signal: Signal) -> float:
    """Extract a signal value from CAN frame data bytes (Intel/little-endian)."""
    start_byte = signal.start_bit // 8
    start_bit_in_byte = signal.start_bit % 8

    # Read enough bytes to cover the signal
    num_bytes = (start_bit_in_byte + signal.bit_length + 7) // 8
    if start_byte + num_bytes > len(data):
        return 0.0

    raw = 0
    for i in range(num_bytes):
        raw |= data[start_byte + i] << (i * 8)

    raw >>= start_bit_in_byte
    mask = (1 << signal.bit_length) - 1
    raw &= mask

    if signal.signed and raw >= (1 << (signal.bit_length - 1)):
        raw -= 1 << signal.bit_length

    return round(raw * signal.scaling + signal.offset, 4)


# ---------------------------------------------------------------------------
# Signal definitions for key CAN messages
# ---------------------------------------------------------------------------

MESSAGES = {
    # Battery pack overview
    0x120: {
        "name": "Overall_Battery_Status_Info",
        "signals": [
            Signal("battery_current_A", 0, 16, 0.01, -300, "A"),
            Signal("soc_percent", 16, 16, 0.01, 0, "%"),
            Signal("charge_voltage_limit_V", 32, 16, 0.001, 0, "V"),
            Signal("charger_mode_request", 48, 3),
        ],
    },
    0x140: {
        "name": "BMS_Parameter_Limit",
        "signals": [
            Signal("regen_power_limit_W", 0, 16, 1, 0, "W"),
            Signal("discharge_power_limit_W", 16, 16, 1, -50000, "W"),
            Signal("battery_current_A", 32, 16, 0.01, -300, "A"),
        ],
    },
    0x150: {
        "name": "BMS_Parameter_3",
        "signals": [
            Signal("bus_voltage_V", 0, 16, 0.001, 0, "V"),
            Signal("delta_voltage_V", 16, 16, 0.001, 0, "V"),
            Signal("available_capacity_percent", 32, 8, 1, 0, "%"),
            Signal("pack_soh_percent", 40, 8, 1, 0, "%"),
        ],
    },
    0x160: {
        "name": "BMS_Parameter_4",
        "signals": [
            Signal("balancing_active", 0, 1),
            Signal("effective_temp_C", 8, 16, 0.1, -50, "°C"),
            Signal("temp_min_C", 24, 16, 0.1, -50, "°C"),
            Signal("temp_max_C", 40, 16, 0.1, -50, "°C"),
        ],
    },
    0x170: {
        "name": "BMS_Cell_Balancing_Status",
        "signals": [
            *[Signal(f"cell_{i+1}_balancing", i, 1) for i in range(14)],
            Signal("cell_min_voltage_V", 16, 16, 0.001, 0, "V"),
            Signal("cell_max_voltage_V", 32, 16, 0.001, 0, "V"),
        ],
    },

    # Individual cell voltages (14S pack)
    0x1A5: {
        "name": "Cell_Voltage_1_4",
        "signals": [
            Signal("cell_1_V", 0, 16, 0.001, 0, "V"),
            Signal("cell_2_V", 16, 16, 0.001, 0, "V"),
            Signal("cell_3_V", 32, 16, 0.001, 0, "V"),
            Signal("cell_4_V", 48, 16, 0.001, 0, "V"),
        ],
    },
    0x1A6: {
        "name": "Cell_Voltage_5_8",
        "signals": [
            Signal("cell_5_V", 0, 16, 0.001, 0, "V"),
            Signal("cell_6_V", 16, 16, 0.001, 0, "V"),
            Signal("cell_7_V", 32, 16, 0.001, 0, "V"),
            Signal("cell_8_V", 48, 16, 0.001, 0, "V"),
        ],
    },
    0x1A9: {
        "name": "Cell_Voltage_9_12",
        "signals": [
            Signal("cell_9_V", 0, 16, 0.001, 0, "V"),
            Signal("cell_10_V", 16, 16, 0.001, 0, "V"),
            Signal("cell_11_V", 32, 16, 0.001, 0, "V"),
            Signal("cell_12_V", 48, 16, 0.001, 0, "V"),
        ],
    },
    0x1AA: {
        "name": "Cell_Voltage_13_14",
        "signals": [
            Signal("cell_13_V", 0, 16, 0.001, 0, "V"),
            Signal("cell_14_V", 16, 16, 0.001, 0, "V"),
            Signal("cell_avg_V", 32, 16, 0.001, 0, "V"),
        ],
    },

    # Pack temperatures
    0x1A4: {
        "name": "Pack_Temp_1_4",
        "signals": [
            Signal("pack_temp_1_C", 0, 16, 0.1, -50, "°C"),
            Signal("pack_temp_2_C", 16, 16, 0.1, -50, "°C"),
            Signal("pack_temp_3_C", 32, 16, 0.1, -50, "°C"),
            Signal("pack_temp_4_C", 48, 16, 0.1, -50, "°C"),
        ],
    },
    0x1A7: {
        "name": "Pack_Temp_5_6",
        "signals": [
            Signal("pack_temp_5_C", 0, 16, 0.1, -50, "°C"),
            Signal("pack_temp_6_C", 16, 16, 0.1, -50, "°C"),
            Signal("pdu_delta_temp_C", 32, 16, 0.5, -50, "°C"),
            Signal("battery_temp_display_C", 48, 8, 1, -50, "°C"),
        ],
    },
    0x1A8: {
        "name": "PDU_Temp",
        "signals": [
            Signal("pdu_temp_1_C", 0, 11, 0.1, -40, "°C"),
            Signal("pdu_temp_2_C", 16, 11, 0.1, -40, "°C"),
            Signal("pack_voltage_measured_V", 32, 16, 0.001, 0, "V"),
            Signal("cell_balancing_temp_C", 48, 16, 0.01, -40, "°C"),
        ],
    },

    # MCU extended — drive mode lives here
    0x113: {
        "name": "MCU_Data_2",
        "signals": [
            Signal("vehicle_discharge_mode", 41, 4),
        ],
    },

    # Motor and speed
    0x313: {
        "name": "MCU_Data",
        "signals": [
            Signal("speed_kmph", 0, 16, 0.1, 0, "km/h"),
            Signal("mcu_temp_C", 16, 16, 0.01, 0, "°C"),
            Signal("motor_temp_C", 32, 16, 0.01, 0, "°C"),
            Signal("motor_rpm", 48, 16, 1, 0, "rpm"),
        ],
    },

    # Display info
    0x352: {
        "name": "Display_Info_4",
        "signals": [
            Signal("display_soc_percent", 0, 16, 1, 0, "%"),
            Signal("soh_display_percent", 16, 8, 1, 0, "%"),
        ],
    },
    0x353: {
        "name": "Display_Info",
        "signals": [
            Signal("side_stand", 0, 2),
            Signal("seat_lock", 2, 1),
            Signal("cruise_control", 3, 1),
            Signal("vehicle_range_km", 24, 16, 1, 0, "km"),
            Signal("right_indicator", 40, 1),
            Signal("left_indicator", 41, 1),
            Signal("high_beam", 42, 1),
            Signal("service_indicator", 43, 1),
            Signal("error_indicator", 44, 2),
            Signal("charge_indicator", 46, 2),
            Signal("position_lamp", 48, 1),
            Signal("brake_pad_worn", 49, 1),
            Signal("low_beam", 50, 1),
            Signal("low_battery_alert", 51, 1),
            Signal("ambient_brightness_percent", 56, 8, 1, 0, "%"),
        ],
    },
    0x356: {
        "name": "Display_Info_5",
        "signals": [
            Signal("odometer_m", 0, 32, 1, 0, "m"),
        ],
    },

    # Range per mode
    0x6F4: {
        "name": "Vehicle_Range",
        "signals": [
            Signal("range_limp_km", 0, 16, 1, 0, "km"),
            Signal("range_sport_km", 16, 16, 1, 0, "km"),
            Signal("range_normal_km", 32, 16, 1, 0, "km"),
            Signal("range_hyper_km", 48, 16, 1, 0, "km"),
        ],
    },

    # Charger connection
    0x62D: {
        "name": "Charger_Connection_Status",
        "signals": [
            Signal("charger_connected", 0, 2),
            Signal("charger_plugged_in", 2, 1),
        ],
    },

    # Safety state
    0x683: {
        "name": "Vehicle_Safety_State",
        "signals": [
            Signal("fall_detection", 0, 4),
            Signal("tow_theft_detection", 4, 4),
            Signal("regen_availability", 8, 4),
            Signal("hill_hold", 12, 4),
        ],
    },
}

# CAN IDs we care about for telemetry
TRACKED_IDS = set(MESSAGES.keys())


def decode_frame(can_id: int, data: bytes, timestamp: float = 0.0) -> Optional[DecodedFrame]:
    """Decode a CAN frame into named signals. Returns None for unknown IDs."""
    if can_id not in MESSAGES:
        return None

    msg_def = MESSAGES[can_id]
    frame = DecodedFrame(
        can_id=can_id,
        name=msg_def["name"],
        timestamp=timestamp,
    )

    for signal in msg_def["signals"]:
        frame.signals[signal.name] = extract_signal(data, signal)

    return frame


def decode_grpc_frame(grpc_can_frame: bytes, timestamp: float = 0.0) -> Optional[DecodedFrame]:
    """Decode a gRPC CANPacket.can_frame (16 bytes: 4B ID big-endian + 1B DLC + 3B pad + 8B data)."""
    if len(grpc_can_frame) < 16:
        return None

    can_id = struct.unpack(">I", grpc_can_frame[0:4])[0]
    data = grpc_can_frame[8:16]

    return decode_frame(can_id, data, timestamp)


def get_cell_voltages(frames: dict) -> list:
    """Extract all 14 cell voltages from decoded frames. Returns list of (cell_number, voltage)."""
    cells = []
    cell_ids = {
        0x1A5: ["cell_1_V", "cell_2_V", "cell_3_V", "cell_4_V"],
        0x1A6: ["cell_5_V", "cell_6_V", "cell_7_V", "cell_8_V"],
        0x1A9: ["cell_9_V", "cell_10_V", "cell_11_V", "cell_12_V"],
        0x1AA: ["cell_13_V", "cell_14_V"],
    }
    cell_num = 1
    for can_id, signal_names in cell_ids.items():
        if can_id in frames:
            for name in signal_names:
                voltage = frames[can_id].signals.get(name, 0.0)
                cells.append((cell_num, voltage))
                cell_num += 1
        else:
            for _ in signal_names:
                cells.append((cell_num, 0.0))
                cell_num += 1
    return cells


def get_battery_summary(frames: dict) -> dict:
    """Build a battery health summary from decoded frames."""
    summary = {}

    if 0x120 in frames:
        summary["soc"] = frames[0x120].signals.get("soc_percent", 0)
        summary["current_A"] = frames[0x120].signals.get("battery_current_A", 0)

    if 0x150 in frames:
        summary["voltage_V"] = frames[0x150].signals.get("bus_voltage_V", 0)
        summary["soh"] = frames[0x150].signals.get("pack_soh_percent", 0)
        summary["delta_V"] = frames[0x150].signals.get("delta_voltage_V", 0)

    if 0x160 in frames:
        summary["temp_C"] = frames[0x160].signals.get("effective_temp_C", 0)
        summary["temp_min_C"] = frames[0x160].signals.get("temp_min_C", 0)
        summary["temp_max_C"] = frames[0x160].signals.get("temp_max_C", 0)

    cells = get_cell_voltages(frames)
    voltages = [v for _, v in cells if v > 0]
    if voltages:
        summary["cell_min_V"] = min(voltages)
        summary["cell_max_V"] = max(voltages)
        summary["cell_spread_mV"] = round((max(voltages) - min(voltages)) * 1000, 1)
        summary["cell_avg_V"] = round(sum(voltages) / len(voltages), 4)
        summary["cells"] = cells

    return summary


if __name__ == "__main__":
    # Self-test with a synthetic frame
    test_data = bytes([0x10, 0x10, 0x70, 0x17, 0x00, 0x00, 0x00, 0x00])
    frame = decode_frame(0x1A5, test_data)
    if frame:
        print(f"Decoded {frame.name}:")
        for name, value in frame.signals.items():
            print(f"  {name} = {value}")
    # cell_1 = 0x1010 = 4112 * 0.001 = 4.112V
    # cell_2 = 0x1770 = 6000 * 0.001 = 6.000V (test value, not realistic)
