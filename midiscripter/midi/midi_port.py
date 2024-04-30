from typing import TYPE_CHECKING, Optional, Union
from collections.abc import Callable

import rtmidi
import rtmidi.midiconstants

import midiscripter.base.port_base
from midiscripter.logger import log
from midiscripter.midi.midi_msg import MidiType

if TYPE_CHECKING:
    from midiscripter.midi.midi_msg import MidiMsg


BYTE_TO_TYPE_MAP = {
    rtmidi.midiconstants.NOTE_ON: MidiType.NOTE_ON,
    rtmidi.midiconstants.NOTE_OFF: MidiType.NOTE_OFF,
    rtmidi.midiconstants.PITCH_BEND: MidiType.PITCH_BEND,
    rtmidi.midiconstants.PROGRAM_CHANGE: MidiType.PROGRAM_CHANGE,
    rtmidi.midiconstants.CONTROLLER_CHANGE: MidiType.CONTROL_CHANGE,
    rtmidi.midiconstants.POLY_PRESSURE: MidiType.POLYTOUCH,
    rtmidi.midiconstants.CHANNEL_PRESSURE: MidiType.AFTERTOUCH,
}

TYPE_TO_BYTE_MAP = {type_: byte_ for byte_, type_ in BYTE_TO_TYPE_MAP.items()}

TYPE_TO_DATA_BYTES_COUNT = {
    MidiType.NOTE_ON: 3,
    MidiType.NOTE_OFF: 3,
    MidiType.CONTROL_CHANGE: 3,
    MidiType.POLYTOUCH: 3,
    MidiType.PITCH_BEND: 3,
    MidiType.AFTERTOUCH: 2,
    MidiType.PROGRAM_CHANGE: 2,
}


class _MidiPortMixin(midiscripter.base.port_base.Port):
    # Attrs provided by the class that inherits from MidiPortMixin
    is_enabled: bool
    _available_names: list[str]

    # noinspection PyMissingConstructor
    def __init__(self, port_name: str, input_callback: Callable | None = None):
        self.__port_name = port_name

        if input_callback:
            self.__rtmidi_port = rtmidi.MidiIn()
            self.__rtmidi_port.ignore_types(sysex=False)
            self.__rtmidi_port.set_callback(input_callback)
        else:
            self.__rtmidi_port = rtmidi.MidiOut()

    @property
    def _is_available(self) -> bool:
        """Port is available and can be opened."""
        return self.__port_name in self._available_names

    def _open(self):
        if self.__rtmidi_port.is_port_open():
            return

        try:
            port_index = self._available_names.index(self.__port_name)
            self.__rtmidi_port.open_port(port_index)
            self.is_enabled = True
            log('Opened {port}', port=self)
        except ValueError:
            log.red("Can't find port {port}. Check the port name.", port=self)
        except Exception:
            log.red('Failed to open {port}', port=self)

    def _close(self):
        if not self.__rtmidi_port.is_port_open():
            return

        try:
            self.__rtmidi_port.close_port()
            self.__rtmidi_port.delete()
            self.is_enabled = False
            log('Closed {port}', port=self)
        except Exception:
            log.red('Failed to close {port}', port=self)


class MidiIn(_MidiPortMixin, midiscripter.base.port_base.Input):
    """MIDI input port. Produces [`MidiMsg`][midiscripter.MidiMsg] objects."""

    _available_names: list[str] = [
        port_name[: port_name.rfind(' ')] for port_name in rtmidi.MidiIn().get_ports()
    ]

    def __init__(self, port_name: str):
        """
        Args:
            port_name: MIDI input port name
        """
        _MidiPortMixin.__init__(self, port_name, self.__callback)
        midiscripter.base.port_base.Input.__init__(self, port_name)

        self.attached_passthrough_outs: list['MidiOut'] = []
        """[`MidiOut`][midiscripter.MidiOut] ports attached as pass-through ports 
        which will send all incoming messages as soon as they arrive before sending them to calls"""

    def passthrough_out(self, midi_output: 'MidiOut'):
        """Attach [`MidiOut`][midiscripter.MidiOut] as a pass-through port to send all incoming messages
        as soon as they arrive, before sending them to calls. This can greatly reduce latency.

        Args:
            midi_output: [`MidiOut`][midiscripter.MidiOut] port to use for pass-through
        """
        if midi_output not in self.attached_passthrough_outs:
            self.attached_passthrough_outs.append(midi_output)
            log('{input} input will pass through {output}', input=self, output=midi_output)

    def __callback(self, rt_midi_input: tuple[tuple[hex, ...], float], _):
        if not self.is_enabled:
            return

        rt_midi_data, _ = rt_midi_input
        [output._passthrough_send(rt_midi_data) for output in self.attached_passthrough_outs]
        self._send_input_msg_to_calls(self.__convert_to_msg(rt_midi_data))

    def __convert_to_msg(
        self, rt_midi_data: tuple[hex, ...]
    ) -> Union['midiscripter.midi.midi_msg.ChannelMsg', 'midiscripter.midi.midi_msg.SysexMsg']:
        if (
            rt_midi_data[0] == rtmidi.midiconstants.SYSTEM_EXCLUSIVE
            and rt_midi_data[-1] == rtmidi.midiconstants.END_OF_EXCLUSIVE
        ):
            return midiscripter.midi.midi_msg.SysexMsg(rt_midi_data, source=self)

        elif rt_midi_data[0] < rtmidi.midiconstants.SYSTEM_EXCLUSIVE:
            midi_type_byte = rt_midi_data[0] & 0xF0
            midi_type = BYTE_TO_TYPE_MAP[midi_type_byte]
            channel = (rt_midi_data[0] & 0xF) + 1

            msg_atts = (midi_type, channel, *rt_midi_data[1:])
            return midiscripter.midi.midi_msg.ChannelMsg(*msg_atts, source=self)

        else:
            log.red(f'Unsupported MIDI msg type byte: {rt_midi_data[0]}')


class MidiOut(_MidiPortMixin, midiscripter.base.port_base.Output):
    """MIDI output port. Sends [`MidiMsg`][midiscripter.MidiMsg] objects."""

    _available_names: list[str] = [
        port_name[: port_name.rfind(' ')] for port_name in rtmidi.MidiOut().get_ports()
    ]

    def __init__(self, port_name: str):
        """
        Args:
            port_name: MIDI output port name
        """
        _MidiPortMixin.__init__(self, port_name)
        midiscripter.base.port_base.Output.__init__(self, port_name)

    def send(self, msg: 'MidiMsg') -> None:
        """Send the MIDI message.

        Args:
            msg: object to send
        """
        with self._check_and_log_sent_message(msg):
            if msg.type == MidiType.SYSEX:
                rt_midi_output = msg.combined_data
            else:
                status_byte = (TYPE_TO_BYTE_MAP[msg.type] & 0xF0) | (msg.channel - 1 & 0xF)
                msg_raw_data = status_byte, msg.data1, msg.data2
                rt_midi_output = [msg_raw_data][: TYPE_TO_DATA_BYTES_COUNT[msg.type]]

            self.__rtmidi_port.send_message(rt_midi_output)

    def _passthrough_send(self, rt_midi_data: tuple[hex, hex, hex]):
        if self.is_enabled:
            try:
                self.__rtmidi_port.send_message(rt_midi_data)
            except (
                Exception
            ):  # _rtmidi.SystemError: MidiOutWinMM::sendMessage: error sending MIDI message.
                log.red(f'Failed to send message data: {rt_midi_data}')
