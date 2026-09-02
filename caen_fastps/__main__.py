"""EPICS PVAccess server for CAEN FAST-PS power supply."""
# pylint: disable=invalid-name,broad-exception-caught
__version__ = 'v0.1.0 26-08-31'

import argparse
import re
import socket
import sys
import time

from epicsdev import epicsdev as edev


DEFAULT_HOST = '192.168.50.120'
DEFAULT_PORT = 10001
DEFAULT_TIMEOUT = 2.0
pargs = None


class C_:
    """Namespace for module state."""

    sock = None
    PvDefs = []
    last_hw_read = 0.0


def handle_exception(where: str):
    """Log exceptions through status/error PVs."""
    edev.printe(f'{where}: {sys.exc_info()[1]}')


def _connect():
    """Open TCP socket to FAST-PS."""
    try:
        C_.sock = socket.create_connection((pargs.host, pargs.port), timeout=pargs.timeout)
        C_.sock.settimeout(pargs.timeout)
        edev.printi(f'Connected to FAST-PS at {pargs.host}:{pargs.port}')
    except OSError:
        handle_exception(f'connecting to {pargs.host}:{pargs.port}')
        sys.exit(1)


def _read_line() -> str:
    """Read one reply line from the socket."""
    if C_.sock is None:
        raise RuntimeError('Socket is not connected')

    data = bytearray()
    while True:
        chunk = C_.sock.recv(1)
        if not chunk:
            break
        data.extend(chunk)
        if chunk == b'\n':
            break
    return data.decode('ascii', errors='ignore').strip()


def _send(cmd: str) -> str:
    """Send ASCII command terminated with CR and return one-line reply."""
    if C_.sock is None:
        raise RuntimeError('Socket is not connected')

    wire = f'{cmd}\r'.encode('ascii', errors='ignore')
    C_.sock.sendall(wire)
    reply = _read_line()
    if not reply:
        raise RuntimeError(f'Empty reply for command {cmd!r}')
    return reply


def _is_ack(reply: str) -> bool:
    r = reply.upper()
    return '#AK' in r or r == 'AK'


def _parse_first_float(text: str):
    m = re.search(r'[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?', str(text))
    return float(m.group(0)) if m else None


def _parse_status32(reply: str) -> int:
    """Parse MST reply value (hex preferred, int fallback)."""
    s = reply.strip()
    if ':' in s:
        s = s.split(':')[-1].strip()
    s = s.replace('#', '').replace('0x', '').replace('0X', '').strip()

    if re.fullmatch(r'[0-9A-Fa-f]+', s):
        return int(s, 16)

    m = re.search(r'\d+', s)
    if m:
        return int(m.group(0))
    raise ValueError(f'Cannot parse status from reply {reply!r}')


def _query_float(cmd: str, default=None):
    try:
        reply = _send(cmd)
        value = _parse_first_float(reply)
        return default if value is None else value
    except Exception:
        handle_exception(f'in _query_float({cmd})')
        return default


def _query_text(cmd: str, default='') -> str:
    try:
        return _send(cmd)
    except Exception:
        handle_exception(f'in _query_text({cmd})')
        return default


def _query_status():
    try:
        reply = _send('MST')
        status32 = _parse_status32(reply)
        status_lsb = status32 & 0xFFFF
        status_msb = (status32 >> 16) & 0xFFFF
        edev.publish('StatusLSB', status_lsb, ifChanged=True)
        edev.publish('StatusMSB', status_msb, ifChanged=True)
        edev.publish('_EnableInit', status_lsb, ifChanged=True)
        enable = 1 if (status_lsb & 0x1) else 0
        edev.publish('_EnableInitCalc', enable, ifChanged=True)
        edev.publish('Enable', enable, ifChanged=True)
    except Exception:
        handle_exception('in _query_status')


def _query_limits():
    """Read limits via configurable MRG fields (if provided)."""
    vals = []
    fields = (
        pargs.limit_field_min_v,
        pargs.limit_field_max_v,
        pargs.limit_field_min_i,
        pargs.limit_field_max_i,
    )
    for field in fields:
        if field < 0:
            vals.append(float('nan'))
        else:
            vals.append(_query_float(f'MRG {field}', float('nan')))

    edev.publish('Limits', vals)
    names = ('LimitMinV', 'LimitMaxV', 'LimitMinI', 'LimitMaxI')
    for pv, val in zip(names, vals):
        if val == val:
            edev.publish(pv, val, ifChanged=True)


def set_regulation_mode(value, *_):
    try:
        mode = str(value).strip().upper()
        mode = 'I' if mode.startswith('I') or mode == '1' else 'V'
        reply = _send(f'LOOP {mode}')
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for LOOP: {reply}')
        edev.publish('RegulationMode', mode, ifChanged=True)
    except Exception:
        handle_exception('in set_regulation_mode')


def _set_setpoint(value: float, kind: str):
    use_ramp = str(edev.pvv('RampEnable')).upper() in ('1', 'ON', 'TRUE')
    cmd = f'MW{kind}R {value}' if use_ramp else f'MW{kind} {value}'
    reply = _send(cmd)
    if not _is_ack(reply):
        raise RuntimeError(f'Unexpected reply for {cmd}: {reply}')


def set_voltage(value, *_):
    try:
        voltage = float(value)
        _set_setpoint(voltage, 'V')
        edev.publish('Voltage', voltage, ifChanged=True)
    except Exception:
        handle_exception('in set_voltage')


def set_current(value, *_):
    try:
        current = float(value)
        _set_setpoint(current, 'I')
        edev.publish('Current', current, ifChanged=True)
    except Exception:
        handle_exception('in set_current')


def set_enable(value, *_):
    try:
        on = str(value).upper() in ('1', 'ON', 'TRUE')
        cmd = 'MON' if on else 'MOFF'
        reply = _send(cmd)
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for {cmd}: {reply}')
        edev.publish('Enable', 1 if on else 0, ifChanged=True)
    except Exception:
        handle_exception('in set_enable')


def set_status_reset(value, *_):
    try:
        v = str(value).upper()
        if v in ('1', 'ON', 'TRUE'):
            reply = _send('MRESET')
            if not _is_ack(reply):
                raise RuntimeError(f'Unexpected reply for MRESET: {reply}')
        edev.publish('StatusReset', 0, ifChanged=True)
    except Exception:
        handle_exception('in set_status_reset')


def set_instrCmdS(cmd, *_):
    try:
        text = str(cmd).strip()
        if text == '':
            return
        reply = _send(text)
        edev.publish('instrCmdR', reply)
    except Exception:
        handle_exception('in set_instrCmdS')


def myPVDefs():
    """PV definitions similar to ioc/fastps.db records."""
    F, T, U, LL, LH, SET = 'features', 'type', 'units', 'limitLow', 'limitHigh', 'setter'

    pv_defs = [
        ['dateTime', 'Server local date/time', 'N/A'],
        ['host', 'FAST-PS host', pargs.host],
        ['port', 'FAST-PS TCP port', pargs.port, {T: 'u32'}],
        ['RegulationMode', 'Selects between voltage/current regulation', ['V', 'I'], {F: 'WD', SET: set_regulation_mode}],
        ['Voltage', 'Voltage control (V regulation mode)', 0.0, {F: 'W', U: 'V', SET: set_voltage}],
        ['Current', 'Current control (I regulation mode)', 0.0, {F: 'W', U: 'A', SET: set_current}],
        ['StatusReset', 'Reset status register / clear faults', 0, {F: 'W', T: 'u8', LL: 0, LH: 1, SET: set_status_reset}],
        ['RampEnable', 'Enable/disable ramp to setpoint', ['Off', 'On'], {F: 'WD'}],
        ['ReadbackPoll_', 'Head of readback chain', 0, {T: 'u32'}],
        ['OutputVoltage', 'Output voltage', 0.0, {U: 'V'}],
        ['OutputCurrent', 'Output current', 0.0, {U: 'A'}],
        ['GroundCurrent', 'Ground current', 0.0, {U: 'A'}],
        ['DCLinkVoltage', 'DC link voltage', 0.0, {U: 'V'}],
        ['HeatsinkTemp', 'Heatsink temperature', 0.0, {U: 'C'}],
        ['StatusMSB', 'Status MSB', 0, {T: 'u32'}],
        ['StatusLSB', 'Status LSB', 0, {T: 'u32'}],
        ['Limits', 'Voltage/current limits [MinV, MaxV, MinI, MaxI]', [0.0, 0.0, 0.0, 0.0]],
        ['LimitMinV', 'Low limit of voltage', 0.0, {U: 'V'}],
        ['LimitMaxV', 'High limit of voltage', 0.0, {U: 'V'}],
        ['LimitMinI', 'Low limit of current', 0.0, {U: 'A'}],
        ['LimitMaxI', 'High limit of current', 0.0, {U: 'A'}],
        ['Model', 'Power supply model', 'N/A'],
        ['Version', 'Power supply firmware version', 'N/A'],
        ['_EnableInit', 'Initialization for Enable (status LSB)', 0, {T: 'u32'}],
        ['_EnableInitCalc', 'Initialization bit for Enable', 0, {T: 'u8'}],
        ['Enable', 'Turn supply off/on', ['Off', 'On'], {F: 'WD', SET: set_enable}],
        ['instrCmdS', 'Execute custom FAST-PS command', 'VER', {F: 'W', SET: set_instrCmdS}],
        ['instrCmdR', 'Reply to custom FAST-PS command', ''],
        ['hardPoll', 'Hardware polling period', 1.0, {F: 'W', U: 's', LL: 0.05, LH: 60.0}],
    ]
    return pv_defs


def refresh_static():
    """Read static identification and setpoint values."""
    ver = _query_text('VER', 'N/A')
    model = ver
    fw = ver
    if 'FW' in ver.upper():
        parts = re.split(r'\bFW\b', ver, flags=re.IGNORECASE)
        if len(parts) >= 2:
            model = parts[0].strip(' :,-')
            fw = parts[1].strip(' :,-')
    edev.publish('Model', model)
    edev.publish('Version', fw)

    loop = _query_text('LOOP ?', 'V').upper()
    edev.publish('RegulationMode', 'I' if 'I' in loop else 'V', ifChanged=True)

    edev.publish('Voltage', _query_float('MWV ?', 0.0), ifChanged=True)
    edev.publish('Current', _query_float('MWI ?', 0.0), ifChanged=True)


def poll():
    """Main polling hook."""
    edev.publish('ReadbackPoll_', int(edev.pvv('ReadbackPoll_')) + 1)
    now = time.time()
    if now - C_.last_hw_read < float(edev.pvv('hardPoll')):
        return
    C_.last_hw_read = now

    edev.publish('OutputVoltage', _query_float('MRV', edev.pvv('OutputVoltage')), ifChanged=True)
    edev.publish('OutputCurrent', _query_float('MRI', edev.pvv('OutputCurrent')), ifChanged=True)
    edev.publish('GroundCurrent', _query_float('MGC', edev.pvv('GroundCurrent')), ifChanged=True)
    edev.publish('DCLinkVoltage', _query_float('MRP', edev.pvv('DCLinkVoltage')), ifChanged=True)
    edev.publish('HeatsinkTemp', _query_float('MRT', edev.pvv('HeatsinkTemp')), ifChanged=True)
    _query_status()
    _query_limits()


def periodic_update():
    """Slow periodic update hook."""
    edev.publish('dateTime', time.strftime('%Y-%m-%d %H:%M:%S'), ifChanged=True)


def serverStateChanged(newState: str):
    """Callback for server state transitions."""
    if newState == 'Start':
        edev.printi('Start requested')
        refresh_static()
        _query_status()
        _query_limits()
    elif newState == 'Stop':
        edev.printi('Stop requested')
    elif newState == 'Exit':
        edev.printi('Exit requested')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=__version__,
    )
    parser.add_argument('-a', '--autosave', nargs='?', default='', help='Autosave control. If omitted, autosave is enabled with default directory.')
    parser.add_argument('-c', '--recall', action='store_false', help='If given: do not restore initial PV values from autosave cache.')
    parser.add_argument('-d', '--device', default='fastps_', help='Device name, the PV prefix is <device><index>:')
    parser.add_argument('-i', '--index', default='0', help='Device index, the PV prefix is <device><index>:')
    parser.add_argument('-p', '--putlogPV', nargs='?', default='', help='PV name for logging put operations. Empty means default putlog:dump.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity (-vv for more).')

    parser.add_argument('--host', default=DEFAULT_HOST, help='FAST-PS host name or IP address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='FAST-PS TCP port')
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT, help='TCP timeout in seconds')
    parser.add_argument('--limit-field-min-v', type=int, default=-1, help='MRG field id for minimum voltage')
    parser.add_argument('--limit-field-max-v', type=int, default=-1, help='MRG field id for maximum voltage')
    parser.add_argument('--limit-field-min-i', type=int, default=-1, help='MRG field id for minimum current')
    parser.add_argument('--limit-field-max-i', type=int, default=-1, help='MRG field id for maximum current')

    pargs = parser.parse_args()
    if pargs.putlogPV == '':
        pargs.putlogPV = 'putlog:dump'
    pargs.prefix = f'{pargs.device}{pargs.index}:'

    _connect()
    C_.PvDefs = myPVDefs()

    PVs = edev.init_epicsdev(
        pargs.prefix,
        C_.PvDefs,
        pargs.verbose,
        serverStateChanged,
        '',
        pargs.autosave,
        pargs.recall,
        pargs.putlogPV,
    )

    edev.publish('VERSION', __version__)
    edev.set_server('Start')

    server = edev.Server(providers=[PVs])
    edev.printi(f'Server for {pargs.prefix} started. Sleeping per cycle: {repr(edev.pvv("sleep"))} S.')
    while True:
        state = edev.serverState()
        if state.startswith('Exit'):
            break
        if not state.startswith('Stop'):
            poll()
        if not edev.sleep():
            periodic_update()

    try:
        if C_.sock is not None:
            C_.sock.close()
    except OSError:
        pass

    edev.printi('Server is exited')
