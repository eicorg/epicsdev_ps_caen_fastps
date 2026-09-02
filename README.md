# caen_fastps

EPICS PVAccess server for CAEN FAST-PS power supplies, implemented with `epicsdev`.

Main server module: [caen_fastps/__main__.py](caen_fastps/__main__.py)  
IOC reference DB: [ioc/fastps.db](ioc/fastps.db)  
Phoebus screen generator: [screens/generate_screen.py](screens/generate_screen.py)

## Features

- TCP remote control interface to FAST-PS (default port `10001`)
- PV set modeled after IOC DB records in [ioc/fastps.db](ioc/fastps.db)
- Setpoint control with optional ramp mode:
  - `Voltage`, `Current`, `RampEnable`
- Output and diagnostics readback:
  - `OutputVoltage`, `OutputCurrent`, `GroundCurrent`, `DCLinkVoltage`, `HeatsinkTemp`
- Status/fault handling:
  - `StatusMSB`, `StatusLSB`, `StatusReset`, `Enable`
- Device identity:
  - `Model`, `Version`
- Optional limits readback via `MRG` fields:
  - `Limits`, `LimitMinV`, `LimitMaxV`, `LimitMinI`, `LimitMaxI`
- Generic command PVs:
  - `instrCmdS`, `instrCmdR`

## FAST-PS protocol mapping

Implemented command families (from the Remote Control Manual):

- `VER`
- `MON`, `MOFF`
- `LOOP`, `LOOP ?`
- `MWV`, `MWV ?`, `MWVR`
- `MWI`, `MWI ?`, `MWIR`
- `MRESET`
- `MST`
- `MRV`, `MRI`, `MGC`, `MRP`, `MRT`
- `MRG <field>` (optional for limits)

## Requirements

- Python 3.10+
- `epicsdev`
- `p4p`
- Network access to the CAEN FAST-PS device

## Run

From this module directory:

- `python -m caen_fastps`

Useful arguments:

- `--host` FAST-PS IP/hostname (default: `192.168.50.120`)
- `--port` TCP port (default: `10001`)
- `--timeout` socket timeout in seconds (default: `2.0`)
- `-d, --device` PV prefix device root (default: `fastps_`)
- `-i, --index` PV prefix index (default: `0`)
- `--limit-field-min-v`, `--limit-field-max-v`, `--limit-field-min-i`, `--limit-field-max-i`
  - `MRG` field IDs for limits. Keep `-1` to disable each field.

Example:

- `python -m caen_fastps --host 192.168.50.120 --port 10001 -d fastps_ -i 0 -v`

Default PV prefix:

- `fastps_0:`

## Screen generation

Generate a Phoebus `.bob` file:

- `python screens/generate_screen.py`

Options:

- `-t, --title` screen title
- `prefix` PV prefix macro/value (default: `$(DEV):`)

Output:

- [screens/caen_fastps.bob](screens/caen_fastps.bob)

## Notes

- The server uses common `epicsdev` control PVs (`server`, `sleep`, `status`, `HEARTBEAT`, etc.).
- `Enable` is synchronized from status bit 0 in `StatusLSB` during polling.
- For unsupported or custom diagnostics, use `instrCmdS`/`instrCmdR`.
