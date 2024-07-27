import platform
from typing import TYPE_CHECKING, overload

import rtmidi
import rtmidi.midiconstants

import midiscripter.base.port_base
from midiscripter.logger import log
from midiscripter.midi.midi_msg import MidiType, MidiMsg

if TYPE_CHECKING:
    from collections.abc import Callable, Container


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


def _get_available_midi_port_names(
    rtmidi_port_class: type[rtmidi.MidiIn | rtmidi.MidiOut],
) -> list[str]:
    raw_port_names = rtmidi_port_class().get_ports()
    persistent_port_names = [port_name[: port_name.rfind(' ')] for port_name in raw_port_names]

    if platform.system() == 'Windows':
        return persistent_port_names
    else:
        port_names_without_prefixes = [
            port_name[port_name.find(':') + 1 :] for port_name in persistent_port_names
        ]
        return port_names_without_prefixes


class _MidiPortMixin(midiscripter.base.port_base.Port):
    name: str
    """MIDI port name"""

    _is_virtual: bool

    # Attrs provided by the class that inherits from MidiPortMixin
    is_enabled: bool
    _available_names: list[str]

    # noinspection PyMissingConstructor
    def __init__(
        self,
        port_name: str,
        virtual: bool,
        input_callback: 'Callable | None' = None,
    ):
        self.name = port_name
        self.name: str
        """MIDI port name"""
        self._is_virtual = virtual

        if input_callback:
            self._rtmidi_port = rtmidi.MidiIn()
            self._rtmidi_port.ignore_types(sysex=False)
            self._rtmidi_port.set_callback(input_callback)
        else:
            self._rtmidi_port = rtmidi.MidiOut()

    @property
    def _is_available(self) -> bool:
        """Port is available and can be opened."""
        return self.name in self._available_names

    def _open(self) -> None:
        if self._rtmidi_port.is_port_open():
            self.is_enabled = True
            return

        try:
            if self._is_virtual:
                if platform.system() == 'Windows':
                    log.red('Failed to open {port}', port=self)
                    log.red('Virtual ports are not available on Windows. Use loopMIDI.')
                    return

                self._rtmidi_port.open_virtual_port(self.name)
                log('Created and opened virtual port {port}', port=self)

            else:
                port_index = self._available_names.index(self.name)
                self._rtmidi_port.open_port(port_index)
                log('Opened {port}', port=self)

            self.is_enabled = True

        except ValueError:
            log.red("Can't find port {port}. Check the port name.", port=self)
        except Exception:
            log.red('Failed to open {port}', port=self)

    def _close(self) -> None:
        if not self._rtmidi_port.is_port_open():
            return

        try:
            self._rtmidi_port.close_port()
            self._rtmidi_port.delete()
            self.is_enabled = False
            log('Closed {port}', port=self)
        except Exception:
            log.red('Failed to close {port}', port=self)


class MidiIn(_MidiPortMixin, midiscripter.base.port_base.Input):
    """MIDI input port. Produces [`MidiMsg`][midiscripter.MidiMsg] objects."""

    _available_names: list[str] = _get_available_midi_port_names(rtmidi.MidiIn)

    def __init__(self, port_name: str, *, virtual: bool = False):
        """
        Args:
            port_name: MIDI input port name
            virtual: Create virtual port (Linux and macOS only)
        """
        _MidiPortMixin.__init__(self, port_name, virtual, self._callback)
        midiscripter.base.port_base.Input.__init__(self, port_name)

        self.attached_passthrough_outs: list[MidiOut] = []
        """[`MidiOut`][midiscripter.MidiOut] ports attached as pass-through ports
        which will send all incoming messages as soon as they arrive before sending them to calls"""

    def passthrough_out(self, midi_output: 'MidiOut') -> None:
        """Attach [`MidiOut`][midiscripter.MidiOut] as a pass-through port
        to send all incoming messages as soon as they arrive,
        before sending them to calls. This can greatly reduce latency.

        Args:
            midi_output: [`MidiOut`][midiscripter.MidiOut] port to use for pass-through
        """
        if midi_output not in self.attached_passthrough_outs:
            self.attached_passthrough_outs.append(midi_output)
            log('{input} input will pass through {output}', input=self, output=midi_output)

    @overload
    def subscribe(self, call: 'Callable[[MidiMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container | MidiType' = None,
        channel: 'None | Container | int | tuple[int, ...]' = None,
        data1: 'None | Container | int | tuple[int, ...]' = None,
        data2: 'None | Container | int | tuple[int, ...]' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container | MidiType' = None,
        channel: 'None | Container | int | tuple[int, ...]' = None,
        data1: 'None | Container | int | tuple[int, ...]' = None,
        data2: 'None | Container | int | tuple[int, ...]' = None,
    ) -> 'Callable':
        return super().subscribe(type, channel, data1, data2)

    def _open(self) -> None:
        _MidiPortMixin._open(self)
        midiscripter.base.port_base.Input._call_on_port_open(self)

    def _callback(self, rt_midi_input: list[list[hex, ...], float], _: list) -> None:
        if not self.is_enabled:
            return
        rt_midi_data, _ = rt_midi_input
        [output._passthrough_send(rt_midi_data) for output in self.attached_passthrough_outs]
        self._send_input_msg_to_calls(self._convert_to_msg(rt_midi_data))

    @staticmethod
    def _raw_channel_midi_to_attrs(rt_midi_data: list[hex, ...]) -> tuple[MidiType, int, ...]:
        midi_type_byte = rt_midi_data[0] & 0xF0
        midi_type = BYTE_TO_TYPE_MAP[midi_type_byte]
        channel = (rt_midi_data[0] & 0xF) + 1
        return midi_type, channel, *rt_midi_data[1:]

    def _convert_to_msg(
        self, rt_midi_data: list[hex, ...]
    ) -> 'midiscripter.midi.midi_msg.ChannelMsg | midiscripter.midi.midi_msg.SysexMsg':
        if (
            rt_midi_data[0] == rtmidi.midiconstants.SYSTEM_EXCLUSIVE
            and rt_midi_data[-1] == rtmidi.midiconstants.END_OF_EXCLUSIVE
        ):
            return midiscripter.midi.midi_msg.SysexMsg(rt_midi_data, source=self)

        elif rt_midi_data[0] < rtmidi.midiconstants.SYSTEM_EXCLUSIVE:
            msg_atts = self._raw_channel_midi_to_attrs(rt_midi_data)
            return midiscripter.midi.midi_msg.ChannelMsg(*msg_atts, source=self)

        else:
            log.red(f'Unsupported MIDI msg type byte: {rt_midi_data[0]}')


class MidiOut(_MidiPortMixin, midiscripter.base.port_base.Output):
    """MIDI output port. Sends [`MidiMsg`][midiscripter.MidiMsg] objects."""

    _available_names: list[str] = _get_available_midi_port_names(rtmidi.MidiOut)

    def __init__(self, port_name: str, *, virtual: bool = False):
        """
        Args:
            port_name: MIDI output port name
            virtual: Create virtual port (Linux and macOS only)
        """
        _MidiPortMixin.__init__(self, port_name, virtual)
        midiscripter.base.port_base.Output.__init__(self, port_name)

    def send(self, msg: MidiMsg) -> None:
        """Send the MIDI message.

        Args:
            msg: object to send
        """
        if not self._validate_msg_send(msg):
            return

        if msg.type == MidiType.SYSEX:
            rt_midi_output = msg.combined_data
        else:
            status_byte = (TYPE_TO_BYTE_MAP[msg.type] & 0xF0) | (msg.channel - 1 & 0xF)
            msg_raw_data = status_byte, msg.data1, msg.data2
            rt_midi_output = msg_raw_data[: TYPE_TO_DATA_BYTES_COUNT[msg.type]]

        try:
            self._rtmidi_port.send_message(rt_midi_output)
        except Exception:
            # For _rtmidi.SystemError: MidiOutWinMM::sendMessage: error sending MIDI message
            log.red(f'Failed to send message: {msg}')
            return

        self._log_msg_sent(msg)

    def _passthrough_send(self, rt_midi_data: tuple[hex, hex, hex]) -> None:
        if self.is_enabled:
            try:
                self._rtmidi_port.send_message(rt_midi_data)
            except Exception:
                # For _rtmidi.SystemError: MidiOutWinMM::sendMessage: error sending MIDI message
                log.red(f'Failed to send message data: {rt_midi_data}')
