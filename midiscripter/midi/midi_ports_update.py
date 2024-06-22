import time
from typing import ClassVar

import rtmidi

import midiscripter.base.port_base
import midiscripter.shared
import midiscripter.logger
from midiscripter.base.msg_base import Msg


class MidiPortsChangedIn(midiscripter.base.port_base.Input):
    """MIDI ports change watcher. Produces base [`Msg`][midiscripter.Msg] objects.

    Used as a service port for `Restart on new MIDI port found` GUI option.
    """

    refresh_rate_sec: float = 1
    """MIDI ports polling rate in seconds"""

    _force_uid: ClassVar[str] = 'MIDI Ports Change'

    def __init__(self):
        """"""
        super().__init__(self._force_uid)
        self.__dummy_midi_input = rtmidi.MidiIn()
        self.__dummy_midi_output = rtmidi.MidiOut()

        self.__last_check_inputs = self.__dummy_midi_input.get_ports()
        self.__last_check_outputs = self.__dummy_midi_output.get_ports()

    def _open(self) -> None:
        self.is_enabled = True
        self._call_on_port_open()
        midiscripter.shared.thread_executor.submit(self.__updater_worker)
        midiscripter.logger.log('Started MIDI ports change watcher')

    def _close(self) -> None:
        self.is_enabled = False

    def __updater_worker(self) -> None:
        while self.is_enabled:
            time.sleep(self.refresh_rate_sec)

            current_inputs = self.__dummy_midi_input.get_ports()
            current_outputs = self.__dummy_midi_output.get_ports()

            if (
                self.__last_check_inputs != current_inputs
                or self.__last_check_outputs != current_outputs
            ):
                msg = Msg('MIDI Ports Changed', self)
                self._send_input_msg_to_calls(msg)

                self.__last_check_inputs = current_inputs
                self.__last_check_outputs = current_outputs
