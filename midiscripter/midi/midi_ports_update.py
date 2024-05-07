import time

import rtmidi

import midiscripter.base.msg_base
import midiscripter.base.port_base
import midiscripter.base.shared
import midiscripter.logger


class MidiPortsChangedIn(midiscripter.base.port_base.Input):
    """MIDI ports change watcher. Produces [`Msg`][midiscripter.base.msg_base.Msg] objects
    with `MIDI Ports Changed` as `type` on any MIDI port connection or disconnection.

    Used as a service port for `Restart on new MIDI port found` GUI option.

    Notes:
        Can be used to restart CLI scripts on ports change by:
        `MidiPortsChangedIn().subscribe(restart_script)`.
    """

    REFRESH_RATE_SEC = 1
    """MIDI ports polling rate."""

    _force_uid = 'MIDI Ports Change'

    def __init__(self):
        super().__init__(self._force_uid)
        self.__dummy_midi_input = rtmidi.MidiIn()
        self.__dummy_midi_output = rtmidi.MidiOut()

        self.__last_check_inputs = self.__dummy_midi_input.get_ports()
        self.__last_check_outputs = self.__dummy_midi_output.get_ports()

    def _open(self) -> None:
        self.is_enabled = True
        midiscripter.base.shared.thread_executor.submit(self.__updater_worker)
        midiscripter.logger.log('Started MIDI ports change watcher')

    def _close(self) -> None:
        self.is_enabled = False

    def __updater_worker(self) -> None:
        while self.is_enabled:
            time.sleep(self.REFRESH_RATE_SEC)

            current_inputs = self.__dummy_midi_input.get_ports()
            current_outputs = self.__dummy_midi_output.get_ports()

            if (
                self.__last_check_inputs != current_inputs
                or self.__last_check_outputs != current_outputs
            ):
                self.__last_check_inputs = current_inputs
                self.__last_check_outputs = current_outputs
                self._send_input_msg_to_calls(midiscripter.base.msg_base.Msg('MIDI Ports Changed'))
