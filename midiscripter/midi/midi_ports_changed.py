import time
from typing import ClassVar

import supriya_midi

import midiscripter.base.port_base
import midiscripter.shared
import midiscripter.logger
from midiscripter.base.msg_base import Msg


class MidiPortsChangedIn(midiscripter.base.port_base.Input):
    """
    MIDI ports change watcher. Produces base [`Msg`][midiscripter.Msg] objects.
    Used as a service port for GUI.
    """

    refresh_rate_sec: float = 2
    """MIDI ports polling rate in seconds"""

    _forced_uid: ClassVar[str] = 'MIDI Ports Watcher'

    def __init__(self):
        super().__init__()

    def _open(self) -> None:
        self._is_opened = True

        self.__input_checker = supriya_midi.MidiIn()
        self.__output_checker = supriya_midi.MidiOut()

        midiscripter.shared.thread_executor.submit(self.__updater_worker)
        midiscripter.logger.log('Started MIDI ports change watcher')

    def _close(self) -> None:
        self._is_opened = False

        self.__input_checker.delete()
        self.__input_checker = None
        self.__output_checker.delete()
        self.__output_checker = None

        midiscripter.logger.log('Stopped MIDI ports change watcher')

    def __updater_worker(self) -> None:
        last_check_inputs = self.__input_checker.get_ports()
        last_check_outputs = self.__output_checker.get_ports()

        while self._is_opened:
            current_inputs = self.__input_checker.get_ports()
            current_outputs = self.__output_checker.get_ports()

            if last_check_inputs != current_inputs or last_check_outputs != current_outputs:
                msg = Msg('MIDI Ports Changed')
                self._send_input_msg_to_calls(msg)

                last_check_inputs = current_inputs
                last_check_outputs = current_outputs

            time.sleep(self.refresh_rate_sec)