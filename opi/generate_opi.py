"""Generate a simple Phoebus screen for CAEN FAST-PS PVs."""
__version__ = 'v0.0.4 2026-09-08'
# pylint: disable=invalid-name,broad-exception-caught

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
        "Model": w.TextUpdate("Model", f"{prefix}Model", 245, 14, 80, 20),
        "Version_lbl": w.Label("Version_lbl", "FW:", 340, 14, 25, 20),
        "Version": w.TextUpdate("Version", f"{prefix}Version", 365, 14, 40, 20),
        "dateTime": w.TextUpdate("dateTime", f"{prefix}dateTime", 420, 14, 130, 20),
    }
    y = 45
    widgets.update({
        "srvStatus_lbl": w.Label("srvStatus_lbl", "Server:", 20, y, 100, 20),
        "srvStatus": w.TextUpdate("srvStatus", f"{prefix}status", 70, y, 790, 20),
    })
    y += 40
    widgets.update({
        "state_lbl": w.Label("state_lbl", "Run/Stop:", 20, y, 65, 20),
        "server": w.ComboBox("server", f"{prefix}server", 90, y, 110, 20),
        "upmode_lbl": w.Label("upmode_lbl", "UpMode:", 215, y, 90, 20),
        "Upmode": w.ComboBox("Upmode", f"{prefix}Upmode", 285, y, 120, 20),
        "sleep_lbl": w.Label("sleep_lbl", "Sleep:", 410, y, 40, 20),
        "sleep": w.TextEntry("sleep", f"{prefix}sleep", 450, y, 50, 20),
        "cycle_lbl": w.Label("cycle_lbl", "Cycle:", 520, y, 40, 20),
        "cycleTime": w.TextUpdate("cycleTime", f"{prefix}cycleTime", 560, y, 60, 20),
        "hb_lbl": w.Label("hb_lbl", "HB:", 640, y, 30, 20),
        "HEARTBEAT": w.TextUpdate("HEARTBEAT", f"{prefix}HEARTBEAT", 670, y, 70, 20),
    })
    y += 40
    widgets.update({
        "Enable_lbl": w.Label("Enable_lbl", "Enable:", 20, y, 45, 20),
        "Enable": w.ComboBox("Enable", f"{prefix}Enable", 70, y, 95, 20),
        "RegulationMode_lbl": w.Label("RegulationMode_lbl", "Regulate:", 180, y, 90, 20),
        "RegulationMode": w.ComboBox("RegulationMode", f"{prefix}RegulationMode", 250, y, 50, 20),
        "RampEnable_lbl": w.Label("RampEnable_lbl", "Ramp:", 340, y, 40, 20),
        "RampEnable": w.ComboBox("RampEnable", f"{prefix}RampEnable", 385, y, 80, 20),
    })
    y += 40
    widgets.update({
        "Voltage_lbl": w.Label("Voltage_lbl", "Voltage SP:", 20, y, 80, 20),
        "Voltage": w.TextEntry("Voltage", f"{prefix}Voltage", 110, y, 95, 20),
        "Current_lbl": w.Label("Current_lbl", "Current SP:", 220, y, 80, 20),
        "Current": w.TextEntry("Current", f"{prefix}Current", 305, y, 95, 20),
    })
    y += 20
    widgets.update({
        "RampRateV_lbl": w.Label("RampRateV_lbl", "RampRateV:", 20, y, 85, 20),
        "RampRateV": w.TextEntry("RampRateV", f"{prefix}RampRateV", 110, y, 95, 20),
        "RampRateI_lbl": w.Label("RampRateI_lbl", "RampRateI:", 220, y, 80, 20),
        "RampRateI": w.TextEntry("RampRateI", f"{prefix}RampRateI", 305, y, 95, 20),
    })
    y += 20
    widgets.update({
        "OutputVoltage_lbl": w.Label("OutputVoltage_lbl", "Output V:", 20, y, 75, 20),
        "OutputVoltage": w.TextUpdate("OutputVoltage", f"{prefix}OutputVoltage", 110, y, 95, 20),
        "OutputCurrent_lbl": w.Label("OutputCurrent_lbl", "Output I:", 220, y, 75, 20),
        "OutputCurrent": w.TextUpdate("OutputCurrent", f"{prefix}OutputCurrent", 305, y, 95, 20),
        "GroundCurrent_lbl": w.Label("GroundCurrent_lbl", "Ground I [A]:", 420, y, 75, 20),
        "GroundCurrent": w.TextUpdate("GroundCurrent", f"{prefix}GroundCurrent", 500, y, 95, 20),
        "DCLinkVoltage_lbl": w.Label("DCLinkVoltage_lbl", "DC-Link [V]:", 620, y, 70, 20),
        "DCLinkVoltage": w.TextUpdate("DCLinkVoltage", f"{prefix}DCLinkVoltage", 695, y, 95, 20),
        "HeatsinkTemp_lbl": w.Label("HeatsinkTemp_lbl", "Heatsink:", 800, y, 70, 20),
        "HeatsinkTemp": w.TextUpdate("HeatsinkTemp", f"{prefix}HeatsinkTemp", 870, y, 60, 20),
    })
    y += 20
    widgets.update({
        "Limits_lbl": w.Label("Limits_lbl", "Limits:", 20, y, 60, 20),
        "Limits": w.TextUpdate("Limits", f"{prefix}Limits", 80, y, 120, 20),
    })
    widgets.update({"plot": w.DataBrowser("Plot", "caen_fastps.plt", 320, y, 680, 350)})
    y += 80

    dy = 15
    ysame = y

    # MSB Status bits
    x = 20
    widgets["StatusMSBBits"] = w.Label("StatusMSB_lbl", "StatusMSB bits", x, y, 90, 20)
    y += 20
    widgets["MSBBits"] = w.ByteMonitor("MSBBits", f"{prefix}StatusMSB", 20, y, 90, 16*dy)
    widgets["MSBBits"].num_bits(16)
    widgets["MSBBits"].horizontal(False)
    widgets["MSBBits"].on_color(255, 0, 0)
    bitLabelsMSB = [
        "bit 31", "bit 30", "bit 29: over-power", "bit 28", "bit 27: ext.interlock #2",
        "bit 26: ext.interlock #1", "bit 25: high ripple", "bit 24: regulation fault",
        "bit 23: earth fuse fault", "bit 22: earth leakage fault", "bit 21: DC-Link fault",
        "bit 20: over-temperature", "bit 19", "bit 18: crowbar", "bit 17: overcurrent", 
        "bit 16"]
    for i, lblName in enumerate(bitLabelsMSB):
        widgets[f"MSBbit{i}"] = w.Label(f"bit{i}", lblName, x+20, y, 140, dy)
        y += dy

    # LSB Status bits
    y = ysame
    x = 180
    widgets["StatusLSBBits"] = w.Label("StatusLSB_lbl", "StatusLSB bits", x, y, 90, 20)
    y += 20
    widgets["LSBBits"] = w.ByteMonitor("LSBBits", f"{prefix}StatusLSB", x, y, 90, 16*dy)
    widgets["LSBBits"].num_bits(16)
    widgets["LSBBits"].horizontal(False)
    bitLabelsLSB = [
        "bit 0: ON/OFF", "bit 1: fault indicator", "bit 2: control mode [0]",
        "bit 3: control mode [1]", "bit 4:", "bit 5: regulation mode",
        "bit 6: update mode [0]", "bit 7: update mode [1]", "bit 8:", "bit 9:",
        "bit 10:", "bit 11:", "bit 12: ramping", "bit 13: waveform", "bit 14:", "bit 15:"]
    bitLabelsLSB.reverse()
    for i, lblName in enumerate(bitLabelsLSB):
        widgets[f"LSBbit{i}"] = w.Label(f"bit{i}", lblName, x+20, y, 140, dy)
        y += dy

    y += 20
    widgets.update({
        "cmd_lbl": w.Label("cmd_lbl", "Command:", 20, y, 70, 20),
        "instrCmdS": w.TextEntry("instrCmdS", f"{prefix}instrCmdS", 90, y, 230, 20),
        "reply_lbl": w.Label("reply_lbl", "Reply:", 330, y, 45, 20),
        "instrCmdR": w.TextUpdate("instrCmdR", f"{prefix}instrCmdR", 375, y, 685, 20),
    })

    _add_items(widgets["server"], "Start, Stop, Clear, Exit, Started, Stopped, Exited")
    _add_items(widgets["Enable"], "Off, On")
    _add_items(widgets["RegulationMode"], "V, I")
    _add_items(widgets["RampEnable"], "Off, On")

    for pv_name in (
        "Voltage", "Current", "OutputVoltage", "OutputCurrent",
        "GroundCurrent", "DCLinkVoltage"):
        widgets[pv_name].format("Engineering")
        widgets[pv_name].precision(3)

    for pv_name in ("HEARTBEAT", "Limits"):
        widgets[pv_name].format("Decimal")
        widgets[pv_name].precision(0)

    for pv_name in ("HeatsinkTemp", "sleep"):
        widgets[pv_name].format("Decimal")
        widgets[pv_name].precision(1)

    widgets["instrCmdR"].wrap_words(False)

    screen.add_widget(list(widgets.values()))

    out = Path(__file__).with_name("caen_fastps.bob")
    screen.write_screen(str(out))

if __name__ == "__main__":
    main()
