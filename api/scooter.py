"""
gRPC client for the Ola S1 Pro Gen 1 head unit's diagnostics_server.

Provides read-only vehicle info RPCs and command sending via
ExecuteADBCommand (cansend on vcan0). All blocking gRPC calls run
in asyncio.to_thread() so they don't block the FastAPI event loop.
"""

import asyncio
import os
import struct
import sys
import threading
import time
from pathlib import Path

_ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import grpc
from collector import wifican_pb2
from collector import wifican_pb2_grpc
from google.protobuf.empty_pb2 import Empty

from collector.uds import (
    ECU_CAN_IDS,
    DID_BY_NAME,
    build_read_did_cmd,
    build_read_dtc_cmd,
    parse_uds_response,
    parse_dtc_response,
    uds_response_to_dict,
    ecus_info,
    dids_info,
)
from collector.commands import (
    COMMAND_BY_SLUG,
    BLOCKED_COMMANDS,
    COMMANDS,
    CATEGORY_LABELS,
    UNLOCK_REPEAT,
    UNLOCK_INTERVAL_MS,
    build_command_cansend,
)

SCOOTER_IP = os.environ.get("SCOOTER_IP", "")
GRPC_PORT = os.environ.get("GRPC_PORT", "50005")
GRPC_TIMEOUT = 5.0

OP_MODE_NAMES = {
    0: "None",
    1: "Manufacturing",
    2: "Customer",
    3: "Service",
    4: "Decommissioned",
}


def _addr() -> str:
    return f"{SCOOTER_IP}:{GRPC_PORT}"


def _make_channel():
    return grpc.insecure_channel(
        _addr(),
        options=[
            ("grpc.keepalive_time_ms", 10000),
            ("grpc.keepalive_timeout_ms", 3000),
            ("grpc.keepalive_permit_without_calls", 1),
        ],
    )


def _sync_check_connection() -> dict:
    if not SCOOTER_IP:
        return {"connected": False, "address": None, "error": "SCOOTER_IP not set"}
    try:
        channel = _make_channel()
        stub = wifican_pb2_grpc.WifiCanRpcStub(channel)
        resp = stub.GetSwVersion(Empty(), timeout=GRPC_TIMEOUT)
        channel.close()
        return {"connected": True, "address": _addr()}
    except grpc.RpcError as e:
        return {"connected": False, "address": _addr(),
                "error": f"{e.code().name}: {e.details()}"}
    except Exception as e:
        return {"connected": False, "address": _addr(), "error": str(e)}


def _sync_get_info() -> dict:
    channel = _make_channel()
    stub = wifican_pb2_grpc.WifiCanRpcStub(channel)
    info: dict = {}

    try:
        resp = stub.GetSwVersion(Empty(), timeout=GRPC_TIMEOUT)
        info["sw_version"] = resp.status_msg or None
    except grpc.RpcError:
        info["sw_version"] = None

    try:
        resp = stub.GetAospVersion(Empty(), timeout=GRPC_TIMEOUT)
        info["aosp_version"] = resp.status_msg or None
    except grpc.RpcError:
        info["aosp_version"] = None

    try:
        mode = stub.GetVehicleOperationMode(Empty(), timeout=GRPC_TIMEOUT)
        info["operation_mode"] = {
            "mode": OP_MODE_NAMES.get(mode.cur_mode, f"Unknown({mode.cur_mode})"),
            "mode_value": mode.cur_mode,
            "modified_ts": mode.modified_ts or None,
            "modified_ts_str": mode.modified_ts_str or None,
            "modified_by": mode.modified_by or None,
        }
    except grpc.RpcError:
        info["operation_mode"] = None

    try:
        ident = stub.GetVehicleIdentifiers(Empty(), timeout=GRPC_TIMEOUT)
        info["identifiers"] = ident.manifest_json or None
    except grpc.RpcError:
        info["identifiers"] = None

    try:
        flags = stub.GetEcosDynoFlags(Empty(), timeout=GRPC_TIMEOUT)
        info["ecos_dyno"] = {
            "ecos1": flags.ecos1 or None,
            "ecos2": flags.ecos2 or None,
            "dyno": flags.dyno or None,
        }
    except grpc.RpcError:
        info["ecos_dyno"] = None

    try:
        resp = stub.ValidateCerts(Empty(), timeout=GRPC_TIMEOUT)
        info["certs_valid"] = resp.status == 1
    except grpc.RpcError:
        info["certs_valid"] = None

    try:
        status = stub.SwUpdateCheckStatus(Empty(), timeout=GRPC_TIMEOUT)
        SW_STATE_NAMES = {
            0: "None", 1: "Idle", 2: "Upload Initialized", 3: "Upload In Progress",
            4: "Upload Success", 5: "Upload Failed", 6: "Installing System",
            7: "Installing BCM", 8: "Installing BMS", 9: "Installing BLE",
            10: "Installing MCU", 11: "Installing AOSP", 12: "Rebooting",
            13: "Success", 14: "Failed",
        }
        info["sw_update_status"] = {
            "state": SW_STATE_NAMES.get(status.status, f"Unknown({status.status})"),
            "state_value": status.status,
            "message": status.status_msg or None,
        }
    except grpc.RpcError:
        info["sw_update_status"] = None

    channel.close()
    return info


def _sync_send_command(command_id: str, repeat: int | None = None,
                       interval_ms: int | None = None) -> dict:
    cmd = COMMAND_BY_SLUG.get(command_id)
    if cmd is None:
        return {"ok": False, "error": f"Unknown command: {command_id}"}

    if cmd.byte in BLOCKED_COMMANDS:
        return {"ok": False, "error": f"Blocked: {cmd.label} (0x{cmd.byte:02X}) is dangerous"}

    if command_id == "unlock":
        repeat = repeat if repeat is not None else UNLOCK_REPEAT
        interval_ms = interval_ms if interval_ms is not None else UNLOCK_INTERVAL_MS
    else:
        repeat = repeat if repeat is not None else 1
        interval_ms = interval_ms if interval_ms is not None else 0

    cansend_str = build_command_cansend(cmd.byte)
    channel = _make_channel()
    stub = wifican_pb2_grpc.WifiCanRpcStub(channel)

    results = []
    try:
        for i in range(repeat):
            req = wifican_pb2.Command(cmd_msg=cansend_str)
            resp = stub.ExecuteADBCommand(req, timeout=GRPC_TIMEOUT)
            results.append({
                "status": resp.status,
                "message": resp.status_msg,
            })
            if i < repeat - 1 and interval_ms > 0:
                time.sleep(interval_ms / 1000.0)
    except grpc.RpcError as e:
        channel.close()
        return {
            "ok": False,
            "command": command_id,
            "name": cmd.label,
            "hex": f"0x{cmd.byte:02X}",
            "sent": len(results),
            "target": repeat,
            "error": f"{e.code().name}: {e.details()}",
        }

    channel.close()
    return {
        "ok": True,
        "command": command_id,
        "name": cmd.label,
        "hex": f"0x{cmd.byte:02X}",
        "sent": len(results),
        "target": repeat,
    }


def get_command_list() -> list[dict]:
    by_cat: dict[str, list[dict]] = {}
    for cmd in COMMANDS:
        cat = by_cat.setdefault(cmd.category, [])
        cat.append({
            "id": cmd.slug,
            "name": cmd.label,
            "hex": f"0x{cmd.byte:02X}",
            "blocked": cmd.byte in BLOCKED_COMMANDS,
        })
    return [
        {"name": CATEGORY_LABELS.get(cat_id, cat_id), "commands": cmds}
        for cat_id, cmds in by_cat.items()
    ]


async def check_connection() -> dict:
    return await asyncio.to_thread(_sync_check_connection)


async def get_vehicle_info() -> dict:
    return await asyncio.to_thread(_sync_get_info)


async def send_command(command_id: str, repeat: int | None = None,
                       interval_ms: int | None = None) -> dict:
    return await asyncio.to_thread(_sync_send_command, command_id, repeat, interval_ms)


# ---------------------------------------------------------------------------
# UDS diagnostics
# ---------------------------------------------------------------------------

UDS_RESPONSE_TIMEOUT = 3.0


def _sync_uds_read(cansend_cmd: str, response_can_id: int) -> bytes | None:
    """Send a UDS request via cansend and capture the response from CanDumpStream."""
    channel = _make_channel()
    stub = wifican_pb2_grpc.WifiCanRpcStub(channel)

    response_data = [None]
    error_holder = [None]

    def listen():
        try:
            stream = stub.CanDumpStream(Empty(), timeout=UDS_RESPONSE_TIMEOUT + 2)
            deadline = time.time() + UDS_RESPONSE_TIMEOUT
            for packet in stream:
                if time.time() > deadline:
                    break
                frame = packet.can_frame
                if len(frame) >= 16:
                    can_id = struct.unpack(">I", frame[0:4])[0]
                    if can_id == response_can_id:
                        response_data[0] = frame[8:16]
                        break
            stream.cancel()
        except Exception as e:
            error_holder[0] = str(e)

    listener = threading.Thread(target=listen, daemon=True)
    listener.start()
    time.sleep(0.15)

    try:
        req = wifican_pb2.Command(cmd_msg=cansend_cmd)
        stub.ExecuteADBCommand(req, timeout=GRPC_TIMEOUT)
    except grpc.RpcError as e:
        channel.close()
        raise RuntimeError(f"Failed to send UDS request: {e.code().name}: {e.details()}")

    listener.join(timeout=UDS_RESPONSE_TIMEOUT + 1)
    channel.close()

    if error_holder[0]:
        raise RuntimeError(f"Stream error: {error_holder[0]}")

    return response_data[0]


def _sync_read_did(ecu: str, did: int) -> dict:
    """Read a UDS DID from an ECU. Returns parsed response dict."""
    if ecu not in ECU_CAN_IDS:
        return {"success": False, "error": f"Unknown ECU: {ecu}"}

    cmd_str = build_read_did_cmd(ecu, did)
    resp_can_id = ECU_CAN_IDS[ecu][1]

    try:
        data = _sync_uds_read(cmd_str, resp_can_id)
    except RuntimeError as e:
        return {"success": False, "ecu": ecu, "did": f"0x{did:04X}", "error": str(e)}

    if data is None:
        return {"success": False, "ecu": ecu, "did": f"0x{did:04X}",
                "error": "No response received (timeout)"}

    parsed = parse_uds_response(ecu, data)
    result = {"success": parsed.error is None, "ecu": ecu, "did": f"0x{did:04X}"}
    result.update(uds_response_to_dict(parsed))
    return result


def _sync_read_dtc(ecu: str) -> dict:
    """Read DTCs from an ECU."""
    if ecu not in ECU_CAN_IDS:
        return {"success": False, "error": f"Unknown ECU: {ecu}"}

    cmd_str = build_read_dtc_cmd(ecu)
    resp_can_id = ECU_CAN_IDS[ecu][1]

    try:
        data = _sync_uds_read(cmd_str, resp_can_id)
    except RuntimeError as e:
        return {"success": False, "ecu": ecu, "error": str(e), "dtcs": []}

    if data is None:
        return {"success": False, "ecu": ecu,
                "error": "No response received (timeout)", "dtcs": []}

    parsed = parse_uds_response(ecu, data)
    if parsed.error:
        return {"success": False, "ecu": ecu, "error": parsed.error,
                "raw_hex": parsed.raw_hex, "dtcs": []}

    dtcs = parse_dtc_response(parsed.data)
    return {
        "success": True,
        "ecu": ecu,
        "raw_hex": parsed.raw_hex,
        "dtc_count": len(dtcs),
        "dtcs": [
            {"code": d.code, "status": f"0x{d.status:02X}",
             "active": d.active, "stored": d.stored}
            for d in dtcs
        ],
    }


async def read_did(ecu: str, did: int) -> dict:
    return await asyncio.to_thread(_sync_read_did, ecu, did)


async def read_dtc(ecu: str) -> dict:
    return await asyncio.to_thread(_sync_read_dtc, ecu)


def get_ecus() -> list[dict]:
    return ecus_info()


def get_dids() -> list[dict]:
    return dids_info()
