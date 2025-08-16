import time
from typing import NoReturn

import midiscripter.base.port_base
import midiscripter.shared
import midiscripter.logger.log_obj
import midiscripter.logger.console
import midiscripter.midi
from midiscripter.logger import log


def start_cli_debug() -> NoReturn:
    """Starts the script with log output to console.
    Console prints increase latency and jitter. Use for debugging only.
    """
    log._formatter = midiscripter.logger.console.console_log_formatter
    log._sink = midiscripter.logger.console.console_sink
    log._flushing_is_enabled = True

    log('')
    log('Available MIDI i/o ports:')
    [log.yellow(port_name) for port_name in midiscripter.midi.MidiIO._get_available_names()]
    log('')
    log('Available MIDI inputs:')
    [log.green(port_name) for port_name in midiscripter.midi.MidiIn._get_available_names()]
    log('')
    log('Available MIDI outputs:')
    [log.magenta(port_name) for port_name in midiscripter.midi.MidiOut._get_available_names()]
    log('')

    _run_cli_loop()


def start_silent() -> NoReturn:
    """Starts the script without logging. The fastest way to run the script"""
    log._accepts_messages = False
    _run_cli_loop()


def _run_cli_loop() -> NoReturn:
    """Opens the ports and loops until broken by user"""
    if not midiscripter.shared.SCRIPT_PATH_STR:
        raise RuntimeError('Starter can only be called from a script')

    midiscripter.shared.raise_current_process_cpu_priority()
    with midiscripter.base.port_base._all_opened():
        while True:
            try:
                time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                break

    log._flush()
