import platform
from typing import TYPE_CHECKING, overload

import supriya_midi

import midiscripter.base.port_base
from midiscripter.logger import log
from midiscripter.midi.midi_msg import MidiType, MidiMsg

if TYPE_CHECKING:
    from midiscripter.midi.teVirtualMIDI import TeVirtualMidiPort
    from collections.abc import Callable, Container
    from midiscripter.ableton_remote.ableton_port import AbletonIn, AbletonOut
    from midiscripter.base.match_conditions import MatchCondition


BYTE_TO_TYPE_MAP = {
    0x90: MidiType.NOTE_ON,
    0x80: MidiType.NOTE_OFF,
    0xE0: MidiType.PITCH_BEND,
    0xC0: MidiType.PROGRAM_CHANGE,
    0xB0: MidiType.CONTROL_CHANGE,
    0xA0: MidiType.POLY_PRESSURE,
    0xD0: MidiType.CHANNEL_PRESSURE,
}

TYPE_TO_BYTE_MAP = {type_: byte_ for byte_, type_ in BYTE_TO_TYPE_MAP.items()}

TYPE_TO_DATA_BYTES_COUNT = {
    MidiType.NOTE_ON: 3,
    MidiType.NOTE_OFF: 3,
    MidiType.CONTROL_CHANGE: 3,
    MidiType.POLY_PRESSURE: 3,
    MidiType.PITCH_BEND: 3,
    MidiType.CHANNEL_PRESSURE: 2,
    MidiType.PROGRAM_CHANGE: 2,
}


def get_persistent_midi_port_names(raw_port_names: list[str]) -> list[str]:
    persistent_port_names = [port_name[: port_name.rfind(' ')] for port_name in raw_port_names]

    if platform.system() == 'Windows':
        return persistent_port_names
    else:
        port_names_without_prefixes = [
            port_name[port_name.find(':') + 1 :] for port_name in persistent_port_names
        ]
        return port_names_without_prefixes


class _MidiPortMixin(midiscripter.base.port_base.Port):
    # Attrs provided by the class that inherits from MidiPortMixin
    _is_opened: bool
    _uid: str
    _rtmidi_port_class: type[supriya_midi.MidiIn | supriya_midi.MidiOut]
    _rtmidi_port: supriya_midi.MidiIn | supriya_midi.MidiOut | None = None
    _pytemidi_port: 'TeVirtualMidiPort | None' = None

    # noinspection PyMissingConstructor
    def __init__(self, virtual: bool, input_callback: 'Callable | None' = None):
        self._is_virtual = virtual
        self._input_callback = input_callback

    @classmethod
    def _get_available_names(cls) -> list[str]:
        """Get available MIDI port names"""
        rtmidi_port = cls._rtmidi_port_class()
        raw_port_names = rtmidi_port.get_ports()
        rtmidi_port.delete()
        return get_persistent_midi_port_names(raw_port_names)

    @property
    def _is_available(self) -> bool:
        """Port is available and can be opened"""
        if self._is_virtual:
            return True

        return self._uid in self._get_available_names()

    def _open(self) -> None:
        is_input = bool(self._input_callback)

        try:
            if platform.system() == 'Windows' and self._is_virtual:
                if not self._pytemidi_port:  # _pytemidi_port can be pre-set by MidiIO wrapper
                    from midiscripter.midi.teVirtualMIDI import TeVirtualMidiPort

                    self._pytemidi_port = TeVirtualMidiPort(
                        self._uid,
                        self._input_callback,
                        no_input=not is_input,
                        no_output=is_input,
                    )
                self._pytemidi_port.create()
            else:
                self._rtmidi_port = self._rtmidi_port_class()

                if is_input:
                    self._rtmidi_port.ignore_types(sysex=False)
                    self._rtmidi_port.set_callback(self._input_callback)

                if self._is_virtual:
                    self._rtmidi_port.open_virtual_port(self._uid)
                else:
                    port_index = self._get_available_names().index(self._uid)
                    self._rtmidi_port.open_port(port_index)

            log._port_open(self, True)
            self._is_opened = True

        except ValueError:
            log._port_not_found(self)
            self._rtmidi_port.delete()
            self._rtmidi_port = None
        except Exception:
            log._port_open(self, False)
            self._rtmidi_port.delete()
            self._rtmidi_port = None

    def _close(self) -> None:
        try:
            if self._pytemidi_port:
                self._pytemidi_port.close()
            else:
                self._rtmidi_port.close_port()
                self._rtmidi_port.delete()
                self._rtmidi_port = None

            self._is_opened = False

            log._port_close(self, True)
        except Exception:
            log._port_close(self, False)


class MidiIn(_MidiPortMixin, midiscripter.base.port_base.Input):
    """MIDI input port. Produces [`MidiMsg`][midiscripter.MidiMsg] objects."""

    _rtmidi_port_class: type[supriya_midi.MidiIn | supriya_midi.MidiOut] = supriya_midi.MidiIn
    _log_description: str = 'MIDI input'

    def __init__(self, port_name: str, *, virtual: bool = False):
        """
        Args:
            port_name: MIDI input port name
            virtual: Create virtual port
        """
        midiscripter.base.port_base.Input.__init__(self, port_name)
        _MidiPortMixin.__init__(self, virtual, self._callback)

        self._attached_passthrough_outs: list[MidiOut] = []
        """[`MidiOut`][midiscripter.MidiOut] ports attached as pass-through ports
        which will send all incoming messages as soon as they arrive before sending them to calls"""

    def passthrough_out(self, midi_output: 'MidiOut') -> None:
        """Attach [`MidiOut`][midiscripter.MidiOut] as a pass-through port
        to send all incoming messages as soon as they arrive,
        before sending them to calls. This can greatly reduce latency.

        Args:
            midi_output: [`MidiOut`][midiscripter.MidiOut] port to use for pass-through
        """
        if midi_output not in self._attached_passthrough_outs:
            self._attached_passthrough_outs.append(midi_output)
            log('{input} input will pass through {output}', input=self, output=midi_output)

    @overload
    def subscribe(self, call: 'Callable[[MidiMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | MatchCondition | Container | MidiType' = None,
        channel: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data1: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data2: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | MatchCondition | Container | MidiType' = None,
        channel: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data1: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data2: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
    ) -> 'Callable':
        return super().subscribe(type, channel, data1, data2)

    @overload
    def _callback(self, rtmidi_input: list[hex, ...], timestamp: float, data: None) -> None: ...

    @overload
    def _callback(self, pytemidi_input: list[hex, ...]) -> None: ...

    def _callback(self, *args) -> None:
        if not self._is_opened:
            return

        raw_midi_data = args[0]
        [output._passthrough_send(raw_midi_data) for output in self._attached_passthrough_outs]
        self._send_input_msg_to_calls(self._convert_to_msg(raw_midi_data))

    @staticmethod
    def _raw_channel_midi_to_attrs(raw_midi_data: list[hex, ...]) -> tuple[MidiType, int, ...]:
        midi_type_byte = raw_midi_data[0] & 0xF0
        midi_type = BYTE_TO_TYPE_MAP[midi_type_byte]
        channel = (raw_midi_data[0] & 0xF) + 1
        return midi_type, channel, *raw_midi_data[1:]

    def _convert_to_msg(
        self, raw_midi_data: list[hex, ...]
    ) -> 'midiscripter.midi.midi_msg.ChannelMsg | midiscripter.midi.midi_msg.SysexMsg':
        if (
            raw_midi_data[0] == 0xF0
            and raw_midi_data[-1] == 0xF7
        ):
            return midiscripter.midi.midi_msg.SysexMsg(raw_midi_data)

        elif raw_midi_data[0] < 0xF0:
            msg_atts = self._raw_channel_midi_to_attrs(raw_midi_data)
            return midiscripter.midi.midi_msg.ChannelMsg(*msg_atts)

        else:
            log.red(f'Unsupported MIDI msg type byte: {raw_midi_data[0]}')


class MidiOut(_MidiPortMixin, midiscripter.base.port_base.Output):
    """MIDI output port. Sends [`MidiMsg`][midiscripter.MidiMsg] objects."""

    _rtmidi_port_class: type[supriya_midi.MidiIn | supriya_midi.MidiOut] = supriya_midi.MidiOut
    _log_description: str = 'MIDI output'
    _disable_logging_in_send: bool = False

    def __init__(self, port_name: str, *, virtual: bool = False):
        """
        Args:
            port_name: MIDI output port name
            virtual: Create virtual port
        """
        midiscripter.base.port_base.Output.__init__(self, port_name)
        _MidiPortMixin.__init__(self, virtual)

    def send(self, msg: MidiMsg) -> None:
        """Send the MIDI message.

        Args:
            msg: object to send
        """
        if not self._is_opened:
            log._send_failed_port_is_closed(self, msg)

        if msg.type == MidiType.SYSEX:
            raw_midi_output = msg.combined_data
        else:
            status_byte = (TYPE_TO_BYTE_MAP[msg.type] & 0xF0) | (msg.channel - 1 & 0xF)
            msg_raw_data = status_byte, msg.data1, msg.data2
            raw_midi_output = msg_raw_data[: TYPE_TO_DATA_BYTES_COUNT[msg.type]]

        try:
            if self._pytemidi_port:
                self._pytemidi_port.send(raw_midi_output)
            else:
                self._rtmidi_port.send_message(raw_midi_output)
        except Exception:
            # For rtmidi errors or teVirtualMIDI.DriverError
            log.red(f'Failed to send message: {msg}')
            return

        if not self._disable_logging_in_send:
            log._msg_sent(self, msg)

    def _passthrough_send(self, raw_midi_data: tuple[hex, ...]) -> None:
        if self._is_opened:
            try:
                if self._pytemidi_port:
                    self._pytemidi_port.send(raw_midi_data)
                else:
                    self._rtmidi_port.send_message(raw_midi_data)
            except Exception:
                # For rtmidi errors or teVirtualMIDI.DriverError
                log.red(f'Failed to send message data: {raw_midi_data}')


class MidiIO(midiscripter.base.port_base.MultiPort):
    """
    MIDI input/output port that combines [`MidiIn`][midiscripter.MidiIn] and
    [`MidiOut`][midiscripter.MidiOut] ports with the same name.
    Produces and sends [`MidiMsg`][midiscripter.MidiMsg] objects.
    """

    _input_port_class: 'type[MidiIn | AbletonIn]' = MidiIn
    _output_port_class: 'type[MidiOut | AbletonOut]' = MidiOut
    _log_description: str = 'MIDI i/o port'

    def __init__(self, port_name: str, *, virtual: bool = False, loopback: bool = False):
        """
        Args:
            port_name: MIDI port name common for input and output, also works for common part of "In"/"Out" name pair
            virtual: Create virtual input and output ports
            loopback: Immediately send the messages received by the input port with the output port
        """
        self._is_virtual = virtual

        # For better MIDI port repr in log
        if self._is_virtual:
            input_port = self._input_port_class(port_name, virtual=self._is_virtual)
            output_port = self._output_port_class(port_name, virtual=self._is_virtual)
        else:
            input_port_name, output_port_name = self._get_io_names(port_name)
            input_port = self._input_port_class(input_port_name)
            output_port = self._output_port_class(output_port_name)

        super().__init__(port_name, input_port, output_port)

        if loopback:
            input_port.passthrough_out(output_port)

        if virtual and platform.system() == 'Windows':
            import midiscripter.midi.teVirtualMIDI

            for port in (input_port, output_port):
                if port._pytemidi_port:
                    port._pytemidi_port.close()

            pytemidi_port = midiscripter.midi.teVirtualMIDI.TeVirtualMidiPort(
                port_name, input_port._input_callback
            )

            for port in (input_port, output_port):
                port._pytemidi_port = pytemidi_port
                if port._is_opened:
                    port._pytemidi_port.create()

    def _get_io_names(self, port_name: str) -> tuple[str, str]:
        """Get MIDI input and output port names for the port name"""
        available_input_names = self._input_port_class._get_available_names()
        available_output_names = self._output_port_class._get_available_names()

        if port_name in available_input_names and port_name in available_output_names:
            input_port_name = output_port_name = port_name
        elif f'{port_name} Out' in available_input_names and f'{port_name} In' in available_output_names:
            input_port_name = f'{port_name} Out'
            output_port_name = f'{port_name} In'
        elif f'{port_name} In' in available_input_names and f'{port_name} Out' in available_output_names:
            input_port_name = f'{port_name} In'
            output_port_name = f'{port_name} Out'
        else:
            input_port_name = output_port_name = port_name  # make an absent port

        return input_port_name, output_port_name

    @classmethod
    def _get_available_names(cls) -> list[str]:
        """Get available MIDI IO port names"""
        input_rtmidi_port = supriya_midi.MidiIn()
        output_rtmidi_port = supriya_midi.MidiOut()
        input_port_names = get_persistent_midi_port_names(input_rtmidi_port.get_ports())
        output_port_names = get_persistent_midi_port_names(output_rtmidi_port.get_ports())
        input_rtmidi_port.delete()
        output_rtmidi_port.delete()

        stripped_output_port_names = [port.removesuffix(' In').removesuffix(' Out') for port in output_port_names]

        available_names = []
        for port_name in input_port_names:
            if port_name in output_port_names:
                available_names.append(port_name)
            elif port_name.removesuffix(' In').removesuffix(' Out') in stripped_output_port_names:
                available_names.append(port_name.removesuffix(' In').removesuffix(' Out'))

        return available_names

    @property
    def _is_available(self) -> bool:
        """Port is available and can be opened"""
        return self._uid in self._get_available_names()

    def passthrough_out(self, midi_output: 'MidiOut') -> None:
        """Attach [`MidiOut`][midiscripter.MidiOut] as a pass-through port
        to send all incoming messages as soon as they arrive,
        before sending them to calls. This can greatly reduce latency.

        Args:
            midi_output: [`MidiOut`][midiscripter.MidiOut] port to use for pass-through
        """
        self._input_ports[0].passthrough_out(midi_output)

    @overload
    def subscribe(self, call: 'Callable[[MidiMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | MatchCondition | Container | MidiType' = None,
        channel: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data1: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data2: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | MatchCondition | Container | MidiType' = None,
        channel: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data1: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
        data2: 'None | MatchCondition | Container | int | tuple[int, ...]' = None,
    ) -> 'Callable':
        return self._input_ports[0].subscribe(type, channel, data1, data2)

    def send(self, msg: MidiMsg) -> None:
        """Send the MIDI message.

        Args:
            msg: object to send
        """
        self._output_ports[0].send(msg)
