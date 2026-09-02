"""Generate a simple Phoebus screen for CAEN FAST-PS PVs."""
__version__ = 'v0.0.1 26-08-31'

import argparse
from pathlib import Path

import phoebusgen.screen
import phoebusgen.widget

DEFAULT_PREFIX = "$(DEV):"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=__version__,
    )
    parser.add_argument("-t", "--title", default="CAEN FAST-PS", help="Screen title")
    parser.add_argument(
        "prefix",
        nargs="?",
        default=DEFAULT_PREFIX,
        help=(
            "PV prefix used for all widget PV names. "
            "If not specified, the prefix is `$(DEV):`, it can be defined in screen macros."
        ),
    )
    return parser.parse_args()


def _add_items(widget, values: str) -> None:
    for item in values.split(", "):
        widget.item(item)


def main() -> None:
    pargs = _parse_args()
    prefix = pargs.prefix

    screen = phoebusgen.screen.Screen(pargs.title, "caen_fastps.bob")
    screen.width(1080)
    screen.height(660)

    w = phoebusgen.widget
    widgets = {
        "title": w.Label("title", "CAEN FAST-PS", 20, 10, 170, 30),
        "Model_lbl": w.Label("Model_lbl", "Model:", 200, 14, 40, 20),
        "Model": w.TextUpdate("Model", f"{prefix}Model", 245, 14, 260, 20),
        "Version_lbl": w.Label("Version_lbl", "FW:", 520, 14, 25, 20),
        "Version": w.TextUpdate("Version", f"{prefix}Version", 550, 14, 220, 20),
        "dateTime": w.TextUpdate("dateTime", f"{prefix}dateTime", 785, 14, 270, 20),

        "state_lbl": w.Label("state_lbl", "Run/Stop:", 20, 45, 65, 20),
        "server": w.ComboBox("server", f"{prefix}server", 90, 45, 110, 20),
        "sleep_lbl": w.Label("sleep_lbl", "Sleep [s]:", 215, 45, 60, 20),
        "sleep": w.TextEntry("sleep", f"{prefix}sleep", 280, 45, 70, 20),
        "hardPoll_lbl": w.Label("hardPoll_lbl", "HW Poll [s]:", 365, 45, 75, 20),
        "hardPoll": w.TextEntry("hardPoll", f"{prefix}hardPoll", 445, 45, 70, 20),
        "cycle_lbl": w.Label("cycle_lbl", "Cycle [s]:", 530, 45, 60, 20),
        "cycleTime": w.TextUpdate("cycleTime", f"{prefix}cycleTime", 595, 45, 80, 20),
        "hb_lbl": w.Label("hb_lbl", "HB:", 690, 45, 20, 20),
        "HEARTBEAT": w.TextUpdate("HEARTBEAT", f"{prefix}HEARTBEAT", 715, 45, 70, 20),
        "status_lbl": w.Label("status_lbl", "Status:", 800, 45, 40, 20),
        "status": w.TextUpdate("status", f"{prefix}status", 845, 45, 210, 20),

        "Enable_lbl": w.Label("Enable_lbl", "Enable:", 20, 90, 45, 20),
        "Enable": w.ComboBox("Enable", f"{prefix}Enable", 70, 90, 95, 20),
        "RegulationMode_lbl": w.Label("RegulationMode_lbl", "Reg mode:", 180, 90, 60, 20),
        "RegulationMode": w.ComboBox("RegulationMode", f"{prefix}RegulationMode", 245, 90, 80, 20),
        "RampEnable_lbl": w.Label("RampEnable_lbl", "Ramp:", 340, 90, 40, 20),
        "RampEnable": w.ComboBox("RampEnable", f"{prefix}RampEnable", 385, 90, 80, 20),
        "StatusReset": w.TextEntry("StatusReset", f"{prefix}StatusReset", 480, 90, 90, 20),

        "Voltage_lbl": w.Label("Voltage_lbl", "Voltage SP [V]:", 20, 125, 80, 20),
        "Voltage": w.TextEntry("Voltage", f"{prefix}Voltage", 105, 125, 95, 20),
        "Current_lbl": w.Label("Current_lbl", "Current SP [A]:", 220, 125, 80, 20),
        "Current": w.TextEntry("Current", f"{prefix}Current", 305, 125, 95, 20),

        "OutputVoltage_lbl": w.Label("OutputVoltage_lbl", "Output V [V]:", 20, 165, 75, 20),
        "OutputVoltage": w.TextUpdate("OutputVoltage", f"{prefix}OutputVoltage", 100, 165, 95, 20),
        "OutputCurrent_lbl": w.Label("OutputCurrent_lbl", "Output I [A]:", 220, 165, 75, 20),
        "OutputCurrent": w.TextUpdate("OutputCurrent", f"{prefix}OutputCurrent", 300, 165, 95, 20),
        "GroundCurrent_lbl": w.Label("GroundCurrent_lbl", "Ground I [A]:", 420, 165, 75, 20),
        "GroundCurrent": w.TextUpdate("GroundCurrent", f"{prefix}GroundCurrent", 500, 165, 95, 20),
        "DCLinkVoltage_lbl": w.Label("DCLinkVoltage_lbl", "DC-Link [V]:", 620, 165, 70, 20),
        "DCLinkVoltage": w.TextUpdate("DCLinkVoltage", f"{prefix}DCLinkVoltage", 695, 165, 95, 20),
        "HeatsinkTemp_lbl": w.Label("HeatsinkTemp_lbl", "Temp [C]:", 815, 165, 55, 20),
        "HeatsinkTemp": w.TextUpdate("HeatsinkTemp", f"{prefix}HeatsinkTemp", 875, 165, 95, 20),

        "StatusMSB_lbl": w.Label("StatusMSB_lbl", "Status MSB:", 20, 205, 65, 20),
        "StatusMSB": w.TextUpdate("StatusMSB", f"{prefix}StatusMSB", 90, 205, 95, 20),
        "StatusLSB_lbl": w.Label("StatusLSB_lbl", "Status LSB:", 210, 205, 65, 20),
        "StatusLSB": w.TextUpdate("StatusLSB", f"{prefix}StatusLSB", 280, 205, 95, 20),
        "ReadbackPoll__lbl": w.Label("ReadbackPoll__lbl", "Readback cnt:", 400, 205, 75, 20),
        "ReadbackPoll_": w.TextUpdate("ReadbackPoll_", f"{prefix}ReadbackPoll_", 480, 205, 95, 20),

        "LimitMinV_lbl": w.Label("LimitMinV_lbl", "Min V:", 20, 245, 40, 20),
        "LimitMinV": w.TextUpdate("LimitMinV", f"{prefix}LimitMinV", 65, 245, 85, 20),
        "LimitMaxV_lbl": w.Label("LimitMaxV_lbl", "Max V:", 160, 245, 40, 20),
        "LimitMaxV": w.TextUpdate("LimitMaxV", f"{prefix}LimitMaxV", 205, 245, 85, 20),
        "LimitMinI_lbl": w.Label("LimitMinI_lbl", "Min I:", 300, 245, 40, 20),
        "LimitMinI": w.TextUpdate("LimitMinI", f"{prefix}LimitMinI", 345, 245, 85, 20),
        "LimitMaxI_lbl": w.Label("LimitMaxI_lbl", "Max I:", 440, 245, 40, 20),
        "LimitMaxI": w.TextUpdate("LimitMaxI", f"{prefix}LimitMaxI", 485, 245, 85, 20),
        "Limits_lbl": w.Label("Limits_lbl", "Limits [Vmin,Vmax,Imin,Imax]:", 585, 245, 165, 20),
        "Limits": w.TextUpdate("Limits", f"{prefix}Limits", 755, 245, 300, 20),

        "cmd_lbl": w.Label("cmd_lbl", "Command:", 20, 290, 60, 20),
        "instrCmdS": w.TextEntry("instrCmdS", f"{prefix}instrCmdS", 85, 290, 230, 20),
        "reply_lbl": w.Label("reply_lbl", "Reply:", 330, 290, 35, 20),
        "instrCmdR": w.TextUpdate("instrCmdR", f"{prefix}instrCmdR", 370, 290, 685, 20),

        "StatusBits_lbl": w.Label("StatusBits_lbl", "StatusLSB bits", 20, 340, 90, 20),
        "bit0": w.TextUpdate("bit0", f"{prefix}_EnableInitCalc", 20, 365, 90, 20),
        "bit0_lbl": w.Label("bit0_lbl", "bit0 = ON/OFF", 120, 365, 120, 20),
        "bit1_lbl": w.Label("bit1_lbl", "bit1 = fault", 120, 390, 120, 20),
        "bit2_lbl": w.Label("bit2_lbl", "bit2/3 = mode", 120, 415, 120, 20),
    }

    _add_items(widgets["server"], "Start, Stop, Clear, Exit, Started, Stopped, Exited")
    _add_items(widgets["Enable"], "Off, On")
    _add_items(widgets["RegulationMode"], "V, I")
    _add_items(widgets["RampEnable"], "Off, On")

    for pv_name in (
        "sleep", "hardPoll", "Voltage", "Current", "OutputVoltage", "OutputCurrent",
        "GroundCurrent", "DCLinkVoltage", "HeatsinkTemp", "LimitMinV", "LimitMaxV",
        "LimitMinI", "LimitMaxI", "cycleTime"
    ):
        widgets[pv_name].format("Engineering")
        widgets[pv_name].precision(3)

    for pv_name in ("HEARTBEAT", "ReadbackPoll_", "StatusMSB", "StatusLSB"):
        widgets[pv_name].format("Decimal")
        widgets[pv_name].precision(0)

    widgets["bit0"].format("Decimal")
    widgets["bit0"].precision(0)
    widgets["instrCmdR"].wrap_words(False)

    screen.add_widget(list(widgets.values()))

    out = Path(__file__).with_name("caen_fastps.bob")
    screen.write_screen(str(out))


if __name__ == "__main__":
    main()
