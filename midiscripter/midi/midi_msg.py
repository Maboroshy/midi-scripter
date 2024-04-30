from typing import TYPE_CHECKING, Optional, Union
from collections.abc import Sequence

import rtmidi.midiconstants

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from midiscripter.midi.midi_port import MidiIn


class MidiType(midiscripter.base.msg_base.AttrEnum):
    """MIDI message type enumerator to use as [`MidiMsg`][midiscripter.MidiMsg] `type` attribute."""

    NOTE_ON = 'NOTE_ON'
    NOTE_OFF = 'NOTE_OFF'
    POLYTOUCH = 'POLYTOUCH'
    AFTERTOUCH = 'AFTERTOUCH'
    CONTROL_CHANGE = 'CONTROL_CHANGE'
    PROGRAM_CHANGE = 'PROGRAM_CHANGE'
    PITCH_BEND = 'PITCH_BEND'
    SYSEX = 'SYSEX'


class MidiMsg(midiscripter.base.msg_base.Msg):
    """The base class for MIDI message that sets the common attributes
    for [`ChannelMsg`][midiscripter.ChannelMsg] and [`SysexMsg`][midiscripter.SysexMsg].

    `MidiMsg` class will produce [`ChannelMsg`][midiscripter.ChannelMsg]
    or [`SysexMsg`][midiscripter.SysexMsg] objects depending on init arguments.

    It is advised to use [`ChannelMsg`][midiscripter.ChannelMsg]
    or [`SysexMsg`][midiscripter.SysexMsg] classes
    to create MIDI messages in calls for clarity.
    """

    __match_args__: tuple[str] = ('type', 'channel', 'data1', 'data2')

    type: MidiType
    channel: int | tuple[int] | tuple[int, int, int]
    data1: int | tuple[int, int]
    data2: int | tuple[int, ...]
    combined_data: int | tuple[int, ...]
    source: Optional['MidiIn']

    def __new__(cls, *args, **kwargs):
        if args and isinstance(args[0], tuple) or not args and 'combined_data' in kwargs:
            return SysexMsg.__new__(SysexMsg, *args, **kwargs)
        else:
            return ChannelMsg.__new__(ChannelMsg, *args, **kwargs)

    def matches(self, type=None, channel=None, data1=None, data2=None) -> bool:
        return super().matches(type, channel, data1, data2)


class ChannelMsg(MidiMsg):
    """Channel voice/mode MIDI message. The most common MIDI message."""

    type: MidiType
    """MIDI message type."""

    channel: int
    """MIDI message channel (1-16)."""

    data1: int
    """First data byte: note, control, program or aftertouch value 
    depending on MIDI message type (0-127)."""

    data2: int
    """Second data byte: velocity, value depending on MIDI message type (0-127)."""

    def __new__(cls, *args, **kwargs):
        """Resets base class custom __new__"""
        return object.__new__(ChannelMsg)

    def __init__(
        self,
        type: MidiType = MidiType.CONTROL_CHANGE,
        channel: int = 1,
        data1: int = 0,
        data2: int = 127,
        *,
        source: Optional['MidiIn'] = None,
    ):
        """
        Args:
            type: MIDI message type.
            channel: MIDI message channel
            data1: First data byte: note, control, program or aftertouch value
            depending on MIDI message type
            data2: Second data byte: velocity, value depending on MIDI message type
            source (MidiIn): The [`MidiIn`][midiscripter.MidiIn] instance that generated the message
        """
        super().__init__(type, source)
        self.channel = channel
        self.data1 = data1
        self.data2 = data2

    @property
    def combined_data(self) -> int | tuple[int, ...]:
        """Both data bytes combined to 14-bit number:
        pitch value for pitch bend MIDI message (0-16383)."""
        return self.data1 | (self.data2 << 7)

    @combined_data.setter
    def combined_data(self, combined_data_value: int | Sequence[int]):
        self.data1 = combined_data_value & 0x7F
        self.data2 = combined_data_value >> 7


class SysexMsg(MidiMsg):
    """System exclusive MIDI message"""

    type = MidiType.SYSEX
    """MIDI message type."""

    channel: tuple[int] | tuple[int, int, int]
    """Manufacturer ID (protocol)."""

    data1: tuple[int, int]
    """Sub ID (model, device, command, etc.)."""

    data2: tuple[int, ...]
    """Message data."""

    def __new__(cls, *args, **kwargs):
        return object.__new__(SysexMsg)

    def __init__(self, combined_data: tuple[int, ...], *, source: Optional['MidiIn'] = None):
        """
        Args:
            combined_data: Whole sysex message including opening (`240`) and closing (`247`) bytes
            source (MidiIn): The [`MidiIn`][midiscripter.MidiIn] instance that generated the message
        """
        midiscripter.base.msg_base.Msg.__init__(self, MidiType.SYSEX, source)
        self.combined_data = combined_data

    def __eq__(self, other: MidiMsg):
        return type(other) is SysexMsg and other.combined_data == self.combined_data

    def __str__(self):
        return f'{self.type} | {str(self.combined_data)[1:-1]}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.combined_data!s})'

    @property
    def combined_data(self) -> tuple[int, ...]:
        """Whole sysex message including opening (`240`) and closing (`247`) bytes."""
        return (
            rtmidi.midiconstants.SYSTEM_EXCLUSIVE,
            *self.channel,
            *self.data1,
            *self.data2,
            rtmidi.midiconstants.END_OF_EXCLUSIVE,
        )

    @combined_data.setter
    def combined_data(self, combined_data: Sequence[int]):
        if (
            combined_data[0] != rtmidi.midiconstants.SYSTEM_EXCLUSIVE
            or combined_data[-1] != rtmidi.midiconstants.END_OF_EXCLUSIVE
        ):
            raise AttributeError(
                'Sysex message should start with 240 (0xF0) and end with 247 (0xF7)'
            )

        # combined_data[0] is sysex status byte
        sub_id_start_index = 4 if combined_data[1] == 0 else 2
        data_start_index = sub_id_start_index + 2
        manufacturer = tuple(combined_data[1:sub_id_start_index])

        if len(combined_data) < data_start_index + 1:  # +1 for closing 247 byte
            raise AttributeError(
                f'Sysex message for manufacturer {manufacturer} '
                f'should be at least {data_start_index + 1} ints '
                f'starting with 240 and ending with 247'
            )

        self.channel = manufacturer
        self.data1 = tuple(combined_data[sub_id_start_index:data_start_index])
        self.data2 = tuple(combined_data[data_start_index:-1])  # sysex end byte excluded
