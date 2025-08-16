import time
from typing import ClassVar

import midiscripter.base.port_base
import midiscripter.shared
import midiscripter.logger
from midiscripter.base.msg_base import Msg
from midiscripter.midi.midi_port import MidiIn, MidiOut


class MidiPortsChangedIn(midiscripter.base.port_base.Input):
    """
    MIDI ports change watcher. Produces base [`Msg`][midiscripter.Msg] objects.
    Used as a service port for GUI.
    """

    refresh_rate_sec: float = 1
    """MIDI ports polling rate in seconds"""

    _forced_uid: ClassVar[str] = 'MIDI Ports Watcher'

    def __init__(self):
        super().__init__()

    def _open(self) -> None:
        self.is_opened = True

        self.__last_check_inputs = MidiIn._get_available_names()
        self.__last_check_outputs = MidiOut._get_available_names()

        midiscripter.shared.thread_executor.submit(self.__updater_worker)
        midiscripter.logger.log('Started MIDI ports change watcher')

    def _close(self) -> None:
        self.is_opened = False
        midiscripter.logger.log('Stopped MIDI ports change watcher')

    def __updater_worker(self) -> None:
        n = 0
        while self.is_opened:
            n += 1

            time.sleep(self.refresh_rate_sec)

            current_inputs = MidiIn._get_available_names()
            current_outputs = MidiOut._get_available_names()

            if (
                self.__last_check_inputs != current_inputs
                or self.__last_check_outputs != current_outputs
            ):
                msg = Msg('MIDI Ports Changed', self)
                self._send_input_msg_to_calls(msg)

                self.__last_check_inputs = current_inputs
                self.__last_check_outputs = current_outputs
