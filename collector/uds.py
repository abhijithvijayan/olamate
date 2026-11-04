"""
UDS (ISO 14229) protocol definitions for Ola S1 Pro Gen 1 ECUs.

Covers frame building, response parsing, DID catalogs, and DTC decoding.
All read-only — no security access or write operations.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# ECU CAN ID pairs (request → response), from diagnostics app EcuCanId.smali
# ---------------------------------------------------------------------------

ECU_CAN_IDS: dict[str, tuple[int, int]] = {
    "bms": (0x078E, 0x07B1),
    "vcu": (0x0786, 0x07B0),
    "mcu": (0x07A6, 0x07B4),
}

ECU_NAMES: dict[str, str] = {
    "bms": "Battery Management System",
    "vcu": "Vehicle Control Unit",
    "mcu": "Motor Control Unit",
}

# ---------------------------------------------------------------------------
# UDS service IDs
# ---------------------------------------------------------------------------

SID_SESSION_CTRL = 0x10
SID_READ_DTC = 0x19
SID_READ_DID = 0x22

CAN_INTERFACE = "vcan0"

# ---------------------------------------------------------------------------
# DID catalog — known data identifiers from diagnostics app analysis
# ---------------------------------------------------------------------------

@dataclass
class DIDEntry:
    did: int
    name: str
    description: str
    ecus: list[str]
    category: str


DID_CATALOG: list[DIDEntry] = [
    # General (all ECUs)
    DIDEntry(0xF190, "vin", "Vehicle Identification Number", ["bms", "vcu", "mcu"], "general"),
    DIDEntry(0x0100, "version", "Software version + vehicle variant", ["bms", "vcu", "mcu"], "general"),
    DIDEntry(0x0103, "odometer", "Odometer value", ["vcu"], "general"),
    DIDEntry(0x017E, "customer-mode", "Customer mode status", ["vcu"], "general"),
    DIDEntry(0x0102, "hypercharge", "HyperCharge status", ["bms"], "general"),

    # VCU feature flags
    DIDEntry(0xCF6F, "hill-hold", "Hill Hold feature flag", ["vcu"], "vcu-features"),
    DIDEntry(0xCF37, "boost-mode", "Boost Mode feature flag", ["vcu"], "vcu-features"),
    DIDEntry(0xCF64, "proximity", "Proximity Lock/Unlock flag", ["vcu"], "vcu-features"),
    DIDEntry(0xCF68, "motor-cutoff", "Motor Cutoff Delay flag", ["vcu"], "vcu-features"),

    # BMS config (E4xx range) — selected key parameters
    DIDEntry(0xE400, "bms-config-0", "BMS config parameter 0", ["bms"], "bms-config"),
    DIDEntry(0xE401, "bms-config-1", "BMS config parameter 1", ["bms"], "bms-config"),
    DIDEntry(0xE402, "bms-config-2", "BMS config parameter 2", ["bms"], "bms-config"),

    # MCU torque maps (B1xx range)
    DIDEntry(0xB131, "torque-normal", "Normal mode torque limits", ["mcu"], "mcu-torque"),
    DIDEntry(0xB132, "torque-sport", "Sport mode torque limits", ["mcu"], "mcu-torque"),
    DIDEntry(0xB133, "torque-hyper", "Hyper mode torque limits", ["mcu"], "mcu-torque"),
    DIDEntry(0xB134, "torque-limp", "Limp-home mode torque limits", ["mcu"], "mcu-torque"),
    DIDEntry(0xB136, "torque-reverse", "Reverse mode torque limits", ["mcu"], "mcu-torque"),
]

DID_BY_NAME: dict[str, DIDEntry] = {d.name: d for d in DID_CATALOG}

DID_CATEGORIES: dict[str, str] = {
    "general": "General",
    "vcu-features": "VCU Feature Flags",
    "bms-config": "BMS Configuration",
    "mcu-torque": "MCU Torque Maps",
}

# ---------------------------------------------------------------------------
# UDS frame building — returns cansend command strings
# ---------------------------------------------------------------------------

def build_read_did_cmd(ecu: str, did: int) -> str:
    """Build cansend command for ReadDataByIdentifier (SID 0x22).

    ISO-TP single frame: [PCI=0x03] [SID=0x22] [DID_hi] [DID_lo] [pad x4]
    """
    req_id = ECU_CAN_IDS[ecu][0]
    did_hi = (did >> 8) & 0xFF
    did_lo = did & 0xFF
    data = f"03{SID_READ_DID:02X}{did_hi:02X}{did_lo:02X}00000000"
    return f"cansend {CAN_INTERFACE} {req_id:03X}#{data}"


def build_read_dtc_cmd(ecu: str) -> str:
    """Build cansend command for ReadDTCInformation (SID 0x19).

    Sub-function 0x02 = reportDTCByStatusMask, mask 0xFF = all DTCs.
    """
    req_id = ECU_CAN_IDS[ecu][0]
    data = f"03{SID_READ_DTC:02X}02FF00000000"
    return f"cansend {CAN_INTERFACE} {req_id:03X}#{data}"


def build_session_ctrl_cmd(ecu: str, session: int = 0x03) -> str:
    """Build cansend command for DiagnosticSessionControl (SID 0x10).

    session: 0x01=Default, 0x03=Extended. 0x02 (Programming) is blocked.
    """
    if session == 0x02:
        raise ValueError("Programming session (0x02) is blocked for safety")
    req_id = ECU_CAN_IDS[ecu][0]
    data = f"02{SID_SESSION_CTRL:02X}{session:02X}0000000000"
    return f"cansend {CAN_INTERFACE} {req_id:03X}#{data}"


# ---------------------------------------------------------------------------
# UDS response parsing
# ---------------------------------------------------------------------------

@dataclass
class UDSResponse:
    ecu: str
    service: int
    did: int | None
    data: bytes
    raw_hex: str
    error: str | None = None
    nrc: int | None = None


UDS_NRC_NAMES: dict[int, str] = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "subFunctionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooLong",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x25: "noResponseFromSubnetComponent",
    0x26: "failurePreventsExecutionOfRequestedAction",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceededNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x70: "uploadDownloadNotAccepted",
    0x71: "transferDataSuspended",
    0x72: "generalProgrammingFailure",
    0x73: "wrongBlockSequenceCounter",
    0x78: "requestCorrectlyReceivedResponsePending",
    0x7E: "subFunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession",
}


def parse_uds_response(ecu: str, data: bytes) -> UDSResponse:
    """Parse a UDS response from CAN frame data bytes (8 bytes)."""
    if len(data) < 3:
        return UDSResponse(ecu=ecu, service=0, did=None, data=data,
                           raw_hex=data.hex(), error="Response too short")

    pci = data[0]
    length = pci & 0x0F

    # Negative response: [PCI] [0x7F] [rejected SID] [NRC]
    if data[1] == 0x7F:
        rejected_sid = data[2]
        nrc = data[3] if len(data) > 3 else 0
        nrc_name = UDS_NRC_NAMES.get(nrc, f"unknown(0x{nrc:02X})")
        return UDSResponse(
            ecu=ecu, service=rejected_sid, did=None, data=data,
            raw_hex=data.hex(),
            error=f"Negative response: {nrc_name}",
            nrc=nrc,
        )

    response_sid = data[1]

    # Positive ReadDID response: [PCI] [0x62] [DID_hi] [DID_lo] [data...]
    if response_sid == 0x62:
        did = (data[2] << 8) | data[3]
        payload = data[4:4 + max(0, length - 3)]
        return UDSResponse(ecu=ecu, service=SID_READ_DID, did=did,
                           data=payload, raw_hex=data.hex())

    # Positive ReadDTC response: [PCI] [0x59] [sub] [mask] [DTC data...]
    if response_sid == 0x59:
        return UDSResponse(ecu=ecu, service=SID_READ_DTC, did=None,
                           data=data[2:], raw_hex=data.hex())

    # Positive SessionControl response: [PCI] [0x50] [session] ...
    if response_sid == 0x50:
        return UDSResponse(ecu=ecu, service=SID_SESSION_CTRL, did=None,
                           data=data[2:], raw_hex=data.hex())

    return UDSResponse(ecu=ecu, service=response_sid, did=None,
                       data=data[1:], raw_hex=data.hex())


# ---------------------------------------------------------------------------
# DTC parsing
# ---------------------------------------------------------------------------

@dataclass
class DTC:
    code: str
    status: int
    active: bool
    stored: bool


def parse_dtc_response(data: bytes) -> list[DTC]:
    """Parse DTCs from a ReadDTCInformation response payload.

    Format after sub-function and status mask:
    [DTC_hi] [DTC_mid] [DTC_lo] [status_byte] repeated
    """
    dtcs = []
    # Skip sub-function byte and status availability mask
    payload = data[2:] if len(data) > 2 else data
    i = 0
    while i + 3 < len(payload):
        dtc_hi = payload[i]
        dtc_mid = payload[i + 1]
        dtc_lo = payload[i + 2]
        status = payload[i + 3] if i + 3 < len(payload) else 0
        code = f"{dtc_hi:02X}{dtc_mid:02X}{dtc_lo:02X}"
        dtcs.append(DTC(
            code=code,
            status=status,
            active=bool(status & 0x01),
            stored=bool(status & 0x04),
        ))
        i += 4
    return dtcs


def parse_grpc_can_frame(grpc_frame: bytes) -> tuple[int, bytes] | None:
    """Parse gRPC CANPacket.can_frame (16 bytes) → (can_id, data[8])."""
    if len(grpc_frame) < 16:
        return None
    can_id = struct.unpack(">I", grpc_frame[0:4])[0]
    data = grpc_frame[8:16]
    return can_id, data


# ---------------------------------------------------------------------------
# Serialization helpers for the API
# ---------------------------------------------------------------------------

def ecus_info() -> list[dict]:
    return [
        {
            "id": ecu,
            "name": ECU_NAMES[ecu],
            "request_can_id": f"0x{req:03X}",
            "response_can_id": f"0x{resp:03X}",
        }
        for ecu, (req, resp) in ECU_CAN_IDS.items()
    ]


def dids_info() -> list[dict]:
    return [
        {
            "name": d.name,
            "did_hex": f"0x{d.did:04X}",
            "did": d.did,
            "description": d.description,
            "ecus": d.ecus,
            "category": d.category,
            "category_label": DID_CATEGORIES.get(d.category, d.category),
        }
        for d in DID_CATALOG
    ]


def uds_response_to_dict(resp: UDSResponse) -> dict:
    result: dict = {
        "ecu": resp.ecu,
        "raw_hex": resp.raw_hex,
    }
    if resp.error:
        result["error"] = resp.error
        if resp.nrc is not None:
            result["nrc"] = resp.nrc
            result["nrc_name"] = UDS_NRC_NAMES.get(resp.nrc, "unknown")
    else:
        result["service"] = f"0x{resp.service:02X}"
        if resp.did is not None:
            result["did"] = f"0x{resp.did:04X}"
        result["data_hex"] = resp.data.hex()
        result["data_ascii"] = resp.data.decode("ascii", errors="replace")
        result["data_bytes"] = list(resp.data)
    return result
