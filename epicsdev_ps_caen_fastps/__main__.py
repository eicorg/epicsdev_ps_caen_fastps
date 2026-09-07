"""EPICS PVAccess server for CAEN FAST-PS power supply."""
# pylint: disable=invalid-name,broad-exception-caught
__version__ = 'v0.0.2 2026-09-06'

import argparse
import re
import socket
import sys
import time

from epicsdev import epicsdev as edev

DEFAULT_HOST = '130.199.104.57'
DEFAULT_PORT = 10001
DEFAULT_TIMEOUT = 2.0
pargs = None
SetpointLimits = {#model: [minV, maxV, minI, maxI]
'FAST-PS 0520-100': [-20.0, 20.0, -5.0, 5.0],
'FAST-PS 0540-200': [-40.0, 40.0, -5.0, 5.0],
'FAST-PS 1020-200': [-20.0, 20.0, -10.0, 10.0],
'FAST-PS 0580-400': [-80.0, 80.0, -5.0, 5.0],
'FAST-PS 1040-400': [-40.0, 40.0, -10.0, 10.0],
'FAST-PS 2020-400': [-20.0, 20.0, -20.0, 20.0],
'FAST-PS 2040-600': [-40.0, 40.0, -20.0, 20.0],
'FAST-PS 3020-600': [-20.0, 20.0,-30.0, 30.0],
}

class C_:
    """Namespace for module state."""
    model = "/"
    sock = None
    PvDefs = []

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

def _send(cmd: str, updateStatus = False) -> str:
    """Send ASCII command terminated with CR and return one-line reply."""
    if C_.sock is None:
        raise RuntimeError('Socket is not connected')

    wire = f'{cmd}\r'.encode('ascii', errors='ignore')
    edev.printv(f'Sending command: {cmd!r} -> {wire!r}, updateStatus={updateStatus}')
    C_.sock.sendall(wire)
    reply = _read_line()
    if not reply:
        raise RuntimeError(f'Empty reply for command {cmd!r}')
    if updateStatus:
        edev.publish('status', '')# clear status before sending command
        _query_status()
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
        #edev.publish('_EnableInit', status_lsb, ifChanged=True)
        enable = 1 if (status_lsb & 0x1) else 0
        #edev.publish('_EnableInitCalc', enable, ifChanged=True)
        edev.publish('Enable', enable, ifChanged=True)
        reply = _send('UPMODE:?')
        mode = reply.split(':')[-1].strip()
        edev.publish('Upmode', mode, ifChanged=True)
        reply = _send('MSRV:?')
        rate_v = _parse_first_float(reply)
        edev.publish('RampRateV', rate_v, ifChanged=True)
        reply = _send('MSRI:?')
        rate_i = _parse_first_float(reply)
        edev.publish('RampRateI', rate_i, ifChanged=True)

    except Exception:
        handle_exception('in _query_status')

def set_regulation_mode(value, *_):
    try:
        mode = str(value).strip().upper()
        mode = 'I' if mode.startswith('I') or mode == '1' else 'V'
        reply = _send(f'LOOP {mode}', updateStatus=True)
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for LOOP: {reply}')
        edev.publish('RegulationMode', mode, ifChanged=True)
    except Exception:
        handle_exception('in set_regulation_mode')


def _set_setpoint(value: float, kind: str):
    use_ramp = str(edev.pvv('RampEnable')).upper() in ('1', 'ON', 'TRUE')
    cmd = f'MW{kind}R:{value}' if use_ramp else f'MW{kind}:{value}'
    print(f'Setting {kind} setpoint to {value} (ramp: {use_ramp}, cmd: {cmd})')
    reply = _send(cmd, updateStatus=True)
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
        reply = _send(cmd, updateStatus=True)
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for {cmd}: {reply}')
        edev.publish('Enable', 1 if on else 0, ifChanged=True)
    except Exception:
        handle_exception('in set_enable')


def set_status_reset(value, *_):
    try:
        v = str(value).upper()
        if v in ('1', 'ON', 'TRUE'):
            reply = _send('MRESET', updateStatus=True)
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
        reply = _send(text, updateStatus=True)
        edev.publish('instrCmdR', reply)
    except Exception:
        handle_exception('in set_instrCmdS')

def set_upmode(value, *_):
    try:
        mode = str(value).strip().upper()
        if mode not in ('NORMAL', 'ANALOG', 'WAVEFORM', 'SFP'):
            raise ValueError(f'Invalid update mode: {mode}')
        reply = _send(f'UPMODE:{mode}', updateStatus=True)
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for UPMODE: {reply}')
        edev.publish('Upmode', mode, ifChanged=True)
    except Exception:
        handle_exception('in set_upmode')

def set_rampV_rate(value, *_):
    try:
        rate = float(value)
        reply = _send(f'MSRV:{rate}', updateStatus=True)
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for MSRV: {reply}')
        edev.publish('RampRateV', rate, ifChanged=True)
    except Exception:
        handle_exception('in set_rampV_rate')

def set_rampI_rate(value, *_):
    try:
        rate = float(value)
        reply = _send(f'MSRI:{rate}', updateStatus=True)
        if not _is_ack(reply):
            raise RuntimeError(f'Unexpected reply for MSRI: {reply}')
        edev.publish('RampRateI', rate, ifChanged=True)
    except Exception:
        handle_exception('in set_rampI_rate')

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
        ['OutputVoltage', 'Output voltage', 0.0, {U: 'V'}],
        ['OutputCurrent', 'Output current', 0.0, {U: 'A'}],
        ['GroundCurrent', 'Ground current', 0.0, {U: 'A'}],
        ['DCLinkVoltage', 'DC link voltage', 0.0, {U: 'V'}],
        ['HeatsinkTemp', 'Heatsink temperature', 0.0, {U: 'C'}],
        ['StatusMSB', 'Status MSB', 0, {T: 'u32'}],
        ['StatusLSB', 'Status LSB', 0, {T: 'u32'}],
        ['Limits', 'Voltage/current limits [MinV, MaxV, MinI, MaxI]', [0.0, 0.0, 0.0, 0.0]],
        ['Model', 'Power supply model', 'N/A'],
        ['Version', 'Power supply firmware version', 'N/A'],
        ['Enable', 'Turn supply off/on', ['Off', 'On'], {F: 'WD', SET: set_enable}],
        ['instrCmdS', 'Execute custom FAST-PS command', 'VER', {F: 'W', SET: set_instrCmdS}],
        ['instrCmdR', 'Reply to custom FAST-PS command', ''],
        ['ReadbackPoll_.SCAN', 'Readback polling period',# it is not necessary because the polling period is defined by 'sleep' PV, it is kept for compatibility with original IOC
            ['1.0','0.5','0.2','0.1','0.01','2','5','10'], {F: 'WD', U: 's',
            SET: lambda v, *_: edev.publish('sleep', float(v), ifChanged=True)}],
        ['Upmode', 'Update mode', ['NORMAL', 'ANALOG', 'WAVEFORM', 'SFP'], {F: 'WD', SET: set_upmode}],
        ['RampRateV', 'Ramp rate V/s', 1.0, {F: 'W', U: 'V/s', LL:1e-6, LH:500.0, SET:set_rampV_rate}],
        ['RampRateI', 'Ramp rate I/s', 1.0, {F: 'W', U: 'A/s', LL:1e-6, LH:500.0, SET:set_rampI_rate}],
    ]
    return pv_defs

def refresh_static():
    """Read static identification and setpoint values."""
    ver = _query_text('VER', 'N/A')
    C_.model = ver.split(':')[1]
    edev.publish('Model', C_.model)
    fw = ver.rsplit(':',1)[-1]
    edev.publish('Version', fw)
    edev.publish('Limits', SetpointLimits[C_.model])

    loop = _query_text('LOOP ?', 'V').upper()
    edev.publish('RegulationMode', 'I' if 'I' in loop else 'V', ifChanged=True)

    edev.publish('Voltage', _query_float('MWV ?', 0.0), ifChanged=True)
    edev.publish('Current', _query_float('MWI ?', 0.0), ifChanged=True)

def poll():
    """Main polling hook."""
    edev.publish('OutputVoltage', _query_float('MRV', edev.pvv('OutputVoltage')), ifChanged=True)
    edev.publish('OutputCurrent', _query_float('MRI', edev.pvv('OutputCurrent')), ifChanged=True)
    edev.publish('GroundCurrent', _query_float('MGC', edev.pvv('GroundCurrent')), ifChanged=True)
    edev.publish('DCLinkVoltage', _query_float('MRP', edev.pvv('DCLinkVoltage')), ifChanged=True)
    edev.publish('HeatsinkTemp', _query_float('MRT', edev.pvv('HeatsinkTemp')), ifChanged=True)

def periodic_update():
    """Slow periodic update hook."""
    #print('Periodic update')
    edev.publish('dateTime', time.strftime('%Y-%m-%d %H:%M:%S'), ifChanged=True)
    _query_status()

def serverStateChanged(newState: str):
    """Callback for server state transitions."""
    if newState == 'Start':
        edev.printi('Start requested')
        refresh_static()
        _query_status()
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
    parser.add_argument('-d', '--device', default='caen_fastps', help='Device name, the PV prefix is <device><index>:')
    parser.add_argument('-i', '--index', default='0', help='Device index, the PV prefix is <device><index>:')
    parser.add_argument('-p', '--putlogPV', nargs='?', default='', help='PV name for logging put operations. Empty means default putlog:dump.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity (-vv for more).')

    parser.add_argument('--host', default=DEFAULT_HOST, help='FAST-PS host name or IP address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='FAST-PS TCP port')
    parser.add_argument('--timeout', type=float, default=DEFAULT_TIMEOUT, help='TCP timeout in seconds')

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
