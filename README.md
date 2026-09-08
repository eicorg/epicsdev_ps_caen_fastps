# epicsdev_ps_caen_fastps

EPICS PVAccess server for CAEN FAST-PS power supplies, implemented with `epicsdev`.
## Features
- TCP remote control interface to FAST-PS (default port `10001`)
- PV set modeled after the IOC records in [docs/fastps.db](docs/fastps.db)
- Setpoint control with optional ramping:
  - `Voltage`, `Current`, `RampEnable`
- Output and diagnostic readback:
  - `OutputVoltage`, `OutputCurrent`, `GroundCurrent`, `DCLinkVoltage`, `HeatsinkTemp`
- Status and state control:
  - `StatusMSB`, `StatusLSB`, `StatusReset`, `Enable`, `RegulationMode`, `Upmode`
- Ramp-rate control:
  - `RampRateV`, `RampRateI`
- Device identity and inferred limits:
  - `Model`, `Version`, `Limits`
- Generic command passthrough:
  - `instrCmdS`, `instrCmdR`

## Requirements

- Python 3.10+
- `epicsdev` and its runtime dependencies (including `p4p`)
- Network access to the CAEN FAST-PS device

## Install and run

- `pip install epicsdev_ps_caen_fastps`
- `python -m epicsdev_ps_caen_fastps`

Useful arguments:

- `--host` FAST-PS IP/hostname (default: `130.199.104.57`)
- `--port` TCP port (default: `10001`)
- `--timeout` socket timeout in seconds (default: `2.0`)
- `-d, --device` PV prefix device root (default: `caen_fastps`)
- `-i, --index` PV prefix index (default: `0`)
- `-v` increase verbosity (`-vv` for more)
- `-a, --autosave` enable autosave with optional directory
- `-c, --recall` disable restoring autosaved values on startup

Example:

- `python -m epicsdev_ps_caen_fastps --host 130.199.104.57 -d caen_fastps:`

Default PV prefix:

- `caen_fastps0:`

## Generate a Phoebus screen

Generate `.bob` OPI file:

- `python generate_opi.py -t FAST-PS pva://caen_fastps:0:`

Options:

- `-t, --title` screen title
- `prefix` PV prefix macro/value (default: `$(DEV):`)

Output:

- [opi/caen_fastps.bob](opi/caen_fastps.bob)

## Screenshot

- [docs/opi_caen_fastps.jpg](docs/opi_caen_fastps.jpg)

## Notes

- The server uses common `epicsdev` control PVs such as `server`, `sleep`, `status`, and `HEARTBEAT`.
- `Enable` is synchronized from bit 0 of `StatusLSB` during polling.
- For unsupported/custom diagnostics, use `instrCmdS` and read the reply from `instrCmdR`.
