import time
from typing import NoReturn

import midiscripter.base.port_base
import midiscripter.base.shared
import midiscripter.logger.console_sink
import midiscripter.logger.log
import midiscripter.midi
from midiscripter.logger import log


def start_cli_debug() -> NoReturn:
    """Starts the script with log output to console.
    Console prints increase latency and jitter. Use for debugging only.
    """
    log._sink = midiscripter.logger.console_sink.ConsoleSink()
    log('')
    log('Available MIDI inputs:')
    [log('{input}', input=port_name) for port_name in midiscripter.midi.MidiIn._available_names]
    log('')
    log('Available MIDI outputs:')
    [log('{output}', output=port_name) for port_name in midiscripter.midi.MidiOut._available_names]
    log('')
    _run_cli_loop()


def start_silent() -> NoReturn:
    """Starts the script without logging. The fastest way to run the script."""
    log.is_enabled = False
    _run_cli_loop()


def _run_cli_loop() -> NoReturn:
    """Opens the ports and loops until broken by user."""
    if not midiscripter.base.shared.script_path:
        raise RuntimeError('Starter can only be called from a script')

    midiscripter.base.shared._raise_current_process_cpu_priority()
    with midiscripter.base.port_base._all_opened():
        while True:
            try:
                time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                break
