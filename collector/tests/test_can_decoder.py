import struct
import pytest
from collector.can_decoder import (
    Signal,
    DecodedFrame,
    extract_signal,
    decode_frame,
    decode_grpc_frame,
    get_cell_voltages,
    get_battery_summary,
    MESSAGES,
)


class TestExtractSignal:
    def test_simple_unsigned(self):
        sig = Signal("test", start_bit=0, bit_length=16, scaling=0.001, offset=0)
        data = bytes([0xD0, 0x07, 0, 0, 0, 0, 0, 0])  # 0x07D0 = 2000
        assert extract_signal(data, sig) == pytest.approx(2.0)

    def test_with_offset(self):
        sig = Signal("test", start_bit=0, bit_length=16, scaling=0.01, offset=-300)
        data = bytes([0x30, 0x75, 0, 0, 0, 0, 0, 0])  # 0x7530 = 30000
        assert extract_signal(data, sig) == pytest.approx(0.0)

    def test_signed_positive(self):
        sig = Signal("test", start_bit=0, bit_length=16, scaling=1, offset=0, signed=True)
        data = bytes([0x64, 0x00, 0, 0, 0, 0, 0, 0])  # 100
        assert extract_signal(data, sig) == 100.0

    def test_signed_negative(self):
        sig = Signal("test", start_bit=0, bit_length=16, scaling=1, offset=0, signed=True)
        data = bytes([0x9C, 0xFF, 0, 0, 0, 0, 0, 0])  # -100 in 16-bit signed
        assert extract_signal(data, sig) == -100.0

    def test_non_byte_aligned(self):
        sig = Signal("test", start_bit=4, bit_length=4, scaling=1, offset=0)
        data = bytes([0xA5, 0, 0, 0, 0, 0, 0, 0])  # bits 4-7 = 0xA = 10
        assert extract_signal(data, sig) == 10.0

    def test_single_bit(self):
        sig = Signal("flag", start_bit=0, bit_length=1, scaling=1, offset=0)
        data = bytes([0x01, 0, 0, 0, 0, 0, 0, 0])
        assert extract_signal(data, sig) == 1.0

        data_off = bytes([0x00, 0, 0, 0, 0, 0, 0, 0])
        assert extract_signal(data_off, sig) == 0.0

    def test_data_too_short(self):
        sig = Signal("test", start_bit=48, bit_length=16, scaling=1, offset=0)
        data = bytes([0x01, 0x02])
        assert extract_signal(data, sig) == 0.0


class TestDecodeFrame:
    def test_battery_soc(self):
        # 0x120: soc_percent at bits 16-31, scaling 0.01
        # SOC = 75.50% → raw = 7550 = 0x1D7E
        data = bytes([0x00, 0x00, 0x7E, 0x1D, 0x00, 0x00, 0x00, 0x00])
        frame = decode_frame(0x120, data, timestamp=1.0)
        assert frame is not None
        assert frame.name == "Overall_Battery_Status_Info"
        assert frame.can_id == 0x120
        assert frame.timestamp == 1.0
        assert frame.signals["soc_percent"] == pytest.approx(75.50, abs=0.01)

    def test_battery_current(self):
        # 0x120: battery_current_A at bits 0-15, scaling 0.01, offset -300
        # 0A → raw = 30000 = 0x7530
        data = bytes([0x30, 0x75, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        frame = decode_frame(0x120, data)
        assert frame.signals["battery_current_A"] == pytest.approx(0.0, abs=0.01)

    def test_cell_voltages(self):
        # 0x1A5: 4 cells, each 16 bits, scaling 0.001
        # cell_1 = 4.112V → raw = 4112 = 0x1010
        # cell_2 = 3.800V → raw = 3800 = 0x0ED8
        # cell_3 = 3.650V → raw = 3650 = 0x0E42
        # cell_4 = 4.000V → raw = 4000 = 0x0FA0
        data = bytes([0x10, 0x10, 0xD8, 0x0E, 0x42, 0x0E, 0xA0, 0x0F])
        frame = decode_frame(0x1A5, data)
        assert frame is not None
        assert frame.name == "Cell_Voltage_1_4"
        assert frame.signals["cell_1_V"] == pytest.approx(4.112)
        assert frame.signals["cell_2_V"] == pytest.approx(3.800)
        assert frame.signals["cell_3_V"] == pytest.approx(3.650)
        assert frame.signals["cell_4_V"] == pytest.approx(4.000)

    def test_speed(self):
        # 0x313: speed_kmph at bits 0-15, scaling 0.1
        # 45.2 km/h → raw = 452 = 0x01C4
        data = bytes([0xC4, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        frame = decode_frame(0x313, data)
        assert frame is not None
        assert frame.name == "MCU_Data"
        assert frame.signals["speed_kmph"] == pytest.approx(45.2, abs=0.1)

    def test_unknown_can_id(self):
        data = bytes(8)
        assert decode_frame(0xFFFF, data) is None

    def test_odometer(self):
        # 0x356: odometer_m at bits 0-31, scaling 1
        # 25000000 meters = 0x017D7840
        data = bytes([0x40, 0x78, 0x7D, 0x01, 0x00, 0x00, 0x00, 0x00])
        frame = decode_frame(0x356, data)
        assert frame is not None
        assert frame.signals["odometer_m"] == 25000000


class TestDecodeGrpcFrame:
    def test_valid_frame(self):
        # 16-byte gRPC frame: 4B CAN ID (big-endian) + 1B DLC + 3B pad + 8B data
        can_id_bytes = struct.pack(">I", 0x1A5)
        dlc_pad = bytes([8, 0, 0, 0])
        # cell_1 = 4.000V → raw 4000 = 0x0FA0
        data = bytes([0xA0, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        grpc_frame = can_id_bytes + dlc_pad + data

        frame = decode_grpc_frame(grpc_frame, timestamp=99.0)
        assert frame is not None
        assert frame.can_id == 0x1A5
        assert frame.timestamp == 99.0
        assert frame.signals["cell_1_V"] == pytest.approx(4.000)

    def test_short_frame(self):
        assert decode_grpc_frame(bytes(10)) is None

    def test_unknown_id_returns_none(self):
        can_id_bytes = struct.pack(">I", 0xBEEF)
        grpc_frame = can_id_bytes + bytes(12)
        assert decode_grpc_frame(grpc_frame) is None


class TestGetCellVoltages:
    def _make_frame(self, can_id, signals):
        return DecodedFrame(can_id=can_id, name="test", signals=signals)

    def test_all_cells_present(self):
        frames = {
            0x1A5: self._make_frame(0x1A5, {"cell_1_V": 4.0, "cell_2_V": 4.01, "cell_3_V": 3.99, "cell_4_V": 4.02}),
            0x1A6: self._make_frame(0x1A6, {"cell_5_V": 4.0, "cell_6_V": 3.98, "cell_7_V": 4.01, "cell_8_V": 4.0}),
            0x1A9: self._make_frame(0x1A9, {"cell_9_V": 3.99, "cell_10_V": 4.0, "cell_11_V": 4.01, "cell_12_V": 3.98}),
            0x1AA: self._make_frame(0x1AA, {"cell_13_V": 4.0, "cell_14_V": 4.01}),
        }
        cells = get_cell_voltages(frames)
        assert len(cells) == 14
        assert cells[0] == (1, 4.0)
        assert cells[13] == (14, 4.01)

    def test_missing_frames(self):
        cells = get_cell_voltages({})
        assert len(cells) == 14
        assert all(v == 0.0 for _, v in cells)

    def test_partial_frames(self):
        frames = {
            0x1A5: self._make_frame(0x1A5, {"cell_1_V": 4.0, "cell_2_V": 4.01, "cell_3_V": 3.99, "cell_4_V": 4.02}),
        }
        cells = get_cell_voltages(frames)
        assert len(cells) == 14
        assert cells[0][1] == 4.0
        assert cells[4][1] == 0.0  # cell 5 from missing 0x1A6


class TestGetBatterySummary:
    def _make_frame(self, can_id, signals):
        return DecodedFrame(can_id=can_id, name="test", signals=signals)

    def test_full_summary(self):
        frames = {
            0x120: self._make_frame(0x120, {"soc_percent": 75.0, "battery_current_A": -5.2}),
            0x150: self._make_frame(0x150, {"bus_voltage_V": 52.5, "pack_soh_percent": 98, "delta_voltage_V": 0.015}),
            0x160: self._make_frame(0x160, {"effective_temp_C": 32.0, "temp_min_C": 30.0, "temp_max_C": 34.0}),
            0x1A5: self._make_frame(0x1A5, {"cell_1_V": 3.80, "cell_2_V": 3.81, "cell_3_V": 3.79, "cell_4_V": 3.82}),
            0x1A6: self._make_frame(0x1A6, {"cell_5_V": 3.80, "cell_6_V": 3.81, "cell_7_V": 3.80, "cell_8_V": 3.80}),
            0x1A9: self._make_frame(0x1A9, {"cell_9_V": 3.81, "cell_10_V": 3.80, "cell_11_V": 3.80, "cell_12_V": 3.79}),
            0x1AA: self._make_frame(0x1AA, {"cell_13_V": 3.80, "cell_14_V": 3.81}),
        }
        summary = get_battery_summary(frames)
        assert summary["soc"] == 75.0
        assert summary["current_A"] == -5.2
        assert summary["voltage_V"] == 52.5
        assert summary["soh"] == 98
        assert summary["temp_C"] == 32.0
        assert summary["cell_min_V"] == 3.79
        assert summary["cell_max_V"] == 3.82
        assert summary["cell_spread_mV"] == pytest.approx(30.0, abs=0.1)
        assert len(summary["cells"]) == 14

    def test_empty_frames(self):
        summary = get_battery_summary({})
        assert "soc" not in summary
        assert "cell_min_V" not in summary
