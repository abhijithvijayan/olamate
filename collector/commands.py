"""
Vehicle command definitions for the Ola S1 Pro Gen 1.

CommandFromHMI enum extracted from HVDP's MasterCommander. Each command is
a single byte written to CAN ID 0x6BC byte 0 via `cansend vcan0 6BC#XX00...`.

This module is data-only — no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass

COMMAND_CAN_ID = 0x6BC
CAN_INTERFACE = "vcan0"

# ---------------------------------------------------------------------------
# CommandFromHMI enum — ordinal IS the byte on CAN 0x6BC byte 0
# ---------------------------------------------------------------------------

COMMAND_FROM_HMI: dict[str, int] = {
    "No_Command": 0x00,
    "Lock_with_Steering": 0x01,
    "Lock_without_Steering": 0x02,
    "Seat_Unlock_Cmd": 0x03,
    "Reverse_mode_activated": 0x04,
    "Headlight_Turn_ON_Request": 0x05,
    "ECO_Mode_Rejected_by_User": 0x06,
    "ECO_Mode_Accepted_by_User": 0x07,
    "Vehicle_Shutdown_is_Rejected_by_User": 0x08,
    "ALARM_Turn_Off_Request": 0x09,
    "Headlight_Turn_OFF_Request": 0x0A,
    "Accepted_Get_Home_Request": 0x0B,
    "Rejected_Get_Home_Request": 0x0C,
    "Stop_Charge": 0x0D,
    "Scooter_Reboot": 0x0E,
    "OTA_Installation_Started": 0x0F,
    "OTA_Installation_in_Progress": 0x10,
    "OTA_Installation_Complete": 0x11,
    "MCU_Reboot": 0x12,
    "HU_Reboot": 0x13,
    "Passcode_ACK": 0x14,
    "TripoMeter_Reset_Successfull": 0x15,
    "CTA_LOCK": 0x16,
    "CTA_UNLOCK": 0x17,
    "CTA_IGNORE": 0x18,
    "PASSCODE_AUTH": 0x19,
    "High_Beam_ON": 0x1A,
    "High_Beam_OFF": 0x1B,
    "Low_Beam_ON": 0x1C,
    "Low_Beam_OFF": 0x1D,
    "Rear_Light_ON": 0x1E,
    "Rear_Light_OFF": 0x1F,
    "Left_Indicator_ON": 0x20,
    "Left_Indicator_OFF": 0x21,
    "Right_Indicator_ON": 0x22,
    "Right_Indicator_OFF": 0x23,
    "Front_DRL_ON": 0x24,
    "Front_DRL_OFF": 0x25,
    "AUTO_HEADLIGHT_SUNRISE_EN": 0x26,
    "Auto_HEAD_LIGHT_SUNSET_EN": 0x27,
    "Auto_Head_Light_Reserved": 0x28,
    "Regen_Type_Default_SELECTED": 0x29,
    "Regen_Type_City_Ride_En_Selected": 0x2A,
    "Regen_Type_Highway_Glide_En_Selected": 0x2B,
    "Smart_Head_Light_Default_Selected": 0x2C,
    "Smart_Head_Light_Low_Beam_En_Selected": 0x2D,
    "Smart_Head_Light_High_Beam_En_Selected": 0x2E,
    "Smart_Head_Light_Smart_Light_En_Selected": 0x2F,
    "Boost_Mode_Enable_Selected": 0x30,
    "Boost_Mode_Disable_Selected": 0x31,
    "Accident_Detection_Enable_Selected": 0x32,
    "Accident_Detection_Disable_Selected": 0x33,
    "Tow_Tamper_Detection_Enable_Selected": 0x34,
    "Tow_Tamper_Detection_Disable_Selected": 0x35,
    "Proximity_Lock_Unlock_Enable_Selected": 0x36,
    "Proximity_Lock_Unlock_Disable_Selected": 0x37,
    "Smart_DRL_Light_Enable_Selected": 0x38,
    "Smart_DRL_Light_Disable_Selected": 0x39,
    "Auto_Head_Light_Handling_Enable_Selected": 0x3A,
    "Auto_Head_Light_Handling_Disable_Selected": 0x3B,
    "Hazard_Light_Feature_Enable_Selected": 0x3C,
    "Hazard_Light_Feature_Disable_Selected": 0x3D,
    "Auto_Indicator_Turn_off_Feature_Enable_Selected": 0x3E,
    "Auto_Indicator_Turn_off_Feature_Disable_Selected": 0x3F,
    "Motor_Cutoff_Delay_Selected_Enable_Selected": 0x40,
    "Motor_Cutoff_Delay_Selected_Disable_Selected": 0x41,
    "Hill_Hold_Request_Enable_Selected": 0x42,
    "Hill_Hold_Request_Disable_Selected": 0x43,
    "VACATION_MODE_ON": 0x44,
    "VACATION_MODE_OFF": 0x45,
    "NEED_HELP": 0x46,
    "I_AM_SAFE": 0x47,
    "DELETE_PROFILE": 0x48,
    "USER_CALIBRATION_REQUEST": 0x49,
    "Hazard_Light_Turn_ON": 0x4A,
    "Hazard_Light_Turn_OFF": 0x4B,
    "HMI_Alarm_ignore_True": 0x4C,
    "Tow_Theft_Low_Sensitivity": 0x4D,
    "Tow_Theft_High_Sensitivity": 0x4E,
    "HMI_Alarm_ignore_False": 0x4F,
    "Exit_Diagnostic_Mode": 0x50,
    "Version_Mismatched": 0x51,
    "Smart_Head_Light_SMART_LIGHT_EN_Deselected": 0x52,
    "Ride_Now": 0x53,
    "Lock_Now": 0x54,
    "TMH_Lights_Enable": 0x55,
    "TMH_Lights_Disabled": 0x56,
    "Alarm_unlock_Now": 0x57,
    "Drive_acess_revoked_enable": 0x58,
    "Drive_acess_revoked_disable": 0x59,
    "SIDE_STAND_DISABLE": 0x5A,
    "SIDE_STAND_ENABLE": 0x5B,
    "Brake_Switch_Fault_Deactivate": 0x5C,
    "Brake_Switch_Fault_Activate": 0x5D,
    "AI_Ind_OFF": 0x5E,
    "Brk_Snsr_Fail_detect_AI": 0x5F,
    "Brk_Snsr_Fail_clear_AI": 0x60,
    "OTA_MCU_Reset": 0x61,
    "HMI_Wakeup_pass": 0x62,
}

VALUE_TO_NAME: dict[int, str] = {v: k for k, v in COMMAND_FROM_HMI.items()}

BLOCKED_COMMANDS: dict[int, str] = {
    0x0E: "Scooter_Reboot",
    0x0F: "OTA_Installation_Started",
    0x10: "OTA_Installation_in_Progress",
    0x11: "OTA_Installation_Complete",
    0x12: "MCU_Reboot",
    0x13: "HU_Reboot",
    0x48: "DELETE_PROFILE",
    0x61: "OTA_MCU_Reset",
}


# ---------------------------------------------------------------------------
# CLI-friendly command definitions with categories for the dashboard
# ---------------------------------------------------------------------------

@dataclass
class CommandDef:
    slug: str
    byte: int
    label: str
    category: str
    confirm: bool = False


COMMANDS: list[CommandDef] = [
    # Lock / Unlock
    CommandDef("unlock", 0x19, "Unlock (Passcode Auth)", "lock-unlock", confirm=True),
    CommandDef("lock", 0x54, "Lock Now", "lock-unlock"),
    CommandDef("lock-steering", 0x01, "Lock with Steering", "lock-unlock"),
    CommandDef("lock-no-steering", 0x02, "Lock without Steering", "lock-unlock"),
    CommandDef("seat-unlock", 0x03, "Seat Unlock", "lock-unlock", confirm=True),

    # Indicators
    CommandDef("indicator-left-on", 0x20, "Left Indicator ON", "indicators"),
    CommandDef("indicator-left-off", 0x21, "Left Indicator OFF", "indicators"),
    CommandDef("indicator-right-on", 0x22, "Right Indicator ON", "indicators"),
    CommandDef("indicator-right-off", 0x23, "Right Indicator OFF", "indicators"),
    CommandDef("hazard-on", 0x4A, "Hazard ON", "indicators"),
    CommandDef("hazard-off", 0x4B, "Hazard OFF", "indicators"),

    # Lights
    CommandDef("highbeam-on", 0x1A, "High Beam ON", "lights"),
    CommandDef("highbeam-off", 0x1B, "High Beam OFF", "lights"),
    CommandDef("lowbeam-on", 0x1C, "Low Beam ON", "lights"),
    CommandDef("lowbeam-off", 0x1D, "Low Beam OFF", "lights"),
    CommandDef("rear-light-on", 0x1E, "Rear Light ON", "lights"),
    CommandDef("rear-light-off", 0x1F, "Rear Light OFF", "lights"),
    CommandDef("drl-on", 0x24, "DRL ON", "lights"),
    CommandDef("drl-off", 0x25, "DRL OFF", "lights"),
    CommandDef("headlight-on", 0x05, "Headlight ON", "lights"),
    CommandDef("headlight-off", 0x0A, "Headlight OFF", "lights"),
    CommandDef("tmh-lights-on", 0x55, "Take Me Home Lights ON", "lights"),
    CommandDef("tmh-lights-off", 0x56, "Take Me Home Lights OFF", "lights"),

    # Smart Lights
    CommandDef("smart-light-default", 0x2C, "Default", "smart-lights"),
    CommandDef("smart-light-low", 0x2D, "Low Beam", "smart-lights"),
    CommandDef("smart-light-high", 0x2E, "High Beam", "smart-lights"),
    CommandDef("smart-light-smart", 0x2F, "Smart Light", "smart-lights"),
    CommandDef("smart-drl-on", 0x38, "Smart DRL ON", "smart-lights"),
    CommandDef("smart-drl-off", 0x39, "Smart DRL OFF", "smart-lights"),
    CommandDef("auto-headlight-on", 0x3A, "Auto Headlight ON", "smart-lights"),
    CommandDef("auto-headlight-off", 0x3B, "Auto Headlight OFF", "smart-lights"),

    # Drive Modes
    CommandDef("eco-accept", 0x07, "Accept ECO Mode", "drive"),
    CommandDef("eco-reject", 0x06, "Reject ECO Mode", "drive"),
    CommandDef("boost-on", 0x30, "Boost Mode ON", "drive"),
    CommandDef("boost-off", 0x31, "Boost Mode OFF", "drive"),
    CommandDef("reverse", 0x04, "Reverse Mode", "drive", confirm=True),
    CommandDef("ride-now", 0x53, "Ride Now", "drive"),

    # Regen
    CommandDef("regen-default", 0x29, "Default Regen", "regen"),
    CommandDef("regen-city", 0x2A, "City Ride Regen", "regen"),
    CommandDef("regen-highway", 0x2B, "Highway Glide Regen", "regen"),

    # Safety
    CommandDef("hill-hold-on", 0x42, "Hill Hold ON", "safety"),
    CommandDef("hill-hold-off", 0x43, "Hill Hold OFF", "safety"),
    CommandDef("motor-cutoff-on", 0x40, "Motor Cutoff Delay ON", "safety"),
    CommandDef("motor-cutoff-off", 0x41, "Motor Cutoff Delay OFF", "safety"),
    CommandDef("accident-detect-on", 0x32, "Accident Detection ON", "safety"),
    CommandDef("accident-detect-off", 0x33, "Accident Detection OFF", "safety"),
    CommandDef("tow-tamper-on", 0x34, "Tow/Tamper Detection ON", "safety"),
    CommandDef("tow-tamper-off", 0x35, "Tow/Tamper Detection OFF", "safety"),
    CommandDef("tow-tamper-low", 0x4D, "Tow/Tamper Low Sensitivity", "safety"),
    CommandDef("tow-tamper-high", 0x4E, "Tow/Tamper High Sensitivity", "safety"),
    CommandDef("proximity-on", 0x36, "Proximity Unlock ON", "safety"),
    CommandDef("proximity-off", 0x37, "Proximity Unlock OFF", "safety"),
    CommandDef("hazard-brake-on", 0x3C, "Hazard on Hard Brake ON", "safety"),
    CommandDef("hazard-brake-off", 0x3D, "Hazard on Hard Brake OFF", "safety"),
    CommandDef("auto-indicator-on", 0x3E, "Auto Indicator OFF ON", "safety"),
    CommandDef("auto-indicator-off", 0x3F, "Auto Indicator OFF OFF", "safety"),

    # Alarm
    CommandDef("alarm-off", 0x09, "Alarm OFF", "alarm"),
    CommandDef("alarm-unlock", 0x57, "Alarm Unlock", "alarm"),

    # Misc
    CommandDef("vacation-on", 0x44, "Vacation Mode ON", "misc"),
    CommandDef("vacation-off", 0x45, "Vacation Mode OFF", "misc"),
    CommandDef("sidestand-disable", 0x5A, "Side Stand Disable", "misc", confirm=True),
    CommandDef("sidestand-enable", 0x5B, "Side Stand Enable", "misc"),
    CommandDef("trip-reset", 0x15, "Trip Reset", "misc"),
    CommandDef("stop-charge", 0x0D, "Stop Charge", "misc", confirm=True),
    CommandDef("wakeup", 0x62, "HMI Wakeup", "misc"),
    CommandDef("drive-revoke-on", 0x58, "Revoke Drive Access", "misc", confirm=True),
    CommandDef("drive-revoke-off", 0x59, "Restore Drive Access", "misc"),
    CommandDef("passcode-ack", 0x14, "Passcode ACK", "misc"),
]

COMMAND_BY_SLUG: dict[str, CommandDef] = {c.slug: c for c in COMMANDS}

CATEGORY_LABELS: dict[str, str] = {
    "lock-unlock": "Lock / Unlock",
    "indicators": "Indicators",
    "lights": "Lights",
    "smart-lights": "Smart Lights",
    "drive": "Drive Modes",
    "regen": "Regen",
    "safety": "Safety Features",
    "alarm": "Alarm",
    "misc": "Misc",
}

UNLOCK_REPEAT = 30
UNLOCK_INTERVAL_MS = 100


# ---------------------------------------------------------------------------
# cansend frame building
# ---------------------------------------------------------------------------

def build_command_cansend(command_byte: int) -> str:
    """Build the cansend command string for a CommandFromHMI byte."""
    data_hex = f"{command_byte:02X}" + "00" * 7
    return f"cansend {CAN_INTERFACE} {COMMAND_CAN_ID:03X}#{data_hex}"


def validate_command(slug: str) -> CommandDef:
    """Look up a command by slug and check it's not blocked."""
    cmd = COMMAND_BY_SLUG.get(slug)
    if cmd is None:
        raise ValueError(f"Unknown command: {slug}")
    if cmd.byte in BLOCKED_COMMANDS:
        raise ValueError(f"Blocked command: {slug} ({BLOCKED_COMMANDS[cmd.byte]})")
    return cmd


# ---------------------------------------------------------------------------
# Serialization for the API
# ---------------------------------------------------------------------------

def commands_info() -> list[dict]:
    categories: dict[str, list[dict]] = {}
    for cmd in COMMANDS:
        if cmd.byte in BLOCKED_COMMANDS:
            continue
        cat = categories.setdefault(cmd.category, [])
        cat.append({
            "slug": cmd.slug,
            "byte": f"0x{cmd.byte:02X}",
            "label": cmd.label,
            "confirm": cmd.confirm,
        })
    return [
        {
            "id": cat_id,
            "label": CATEGORY_LABELS.get(cat_id, cat_id),
            "commands": cmds,
        }
        for cat_id, cmds in categories.items()
    ]
