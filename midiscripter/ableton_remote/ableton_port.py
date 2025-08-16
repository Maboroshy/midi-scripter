from typing import overload, TYPE_CHECKING

from midiscripter.midi import MidiIn, MidiOut, MidiIO, ChannelMsg
from midiscripter.base.port_base import Input
from midiscripter.logger import log
from midiscripter.ableton_remote.ableton_msg import AbletonEvent, AbletonMsg
from midiscripter.ableton_remote.remote_script_midi_mapping import (
    ableton_event_to_midi_map,
    midi_to_ableton_button_map,
    midi_to_ableton_slider_map,
)

if TYPE_CHECKING:
    from collections.abc import Container, Callable


# noinspection PyMethodOverriding
class AbletonIn(MidiIn):
    """Receives MIDI messages from Ableton Live remote script
    and produces [`AbletonMsg`][midiscripter.AbletonMsg] objects.
    """

    def __init__(self, proxy_midi_port_name: str, *, virtual: bool = False):
        """
        Args:
            proxy_midi_port_name: The name of proxy MIDI input port enabled in Ableton Live
            virtual: Create virtual MIDI port
        """
        super().__init__(proxy_midi_port_name, virtual=virtual)

    def _convert_to_msg(self, raw_midi_data: tuple[hex, ...]) -> 'AbletonMsg':
        msg_atts = self._raw_channel_midi_to_attrs(raw_midi_data)
        lead_msg_atts = msg_atts[:3]
        value = msg_atts[3]

        try:
            event, index = midi_to_ableton_button_map[lead_msg_atts]
            return AbletonMsg(event, index, bool(value), source=self)
        except KeyError:
            pass

        try:
            event, index = midi_to_ableton_slider_map[lead_msg_atts]
            return AbletonMsg(event, index, value, source=self)
        except KeyError:
            pass

        return AbletonMsg(AbletonEvent.UNSUPPORTED, lead_msg_atts[1], lead_msg_atts[2])

    @overload
    def subscribe(self, call: 'Callable[[AbletonMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container[AbletonEvent] | AbletonEvent' = None,
        index: 'None | Container | int | tuple[int, int]' = None,
        value: 'None | Container[int] | int | bool' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container[AbletonEvent] | AbletonEvent' = None,
        index: 'None | Container[int, tuple[int, int]] | int | tuple[int, int]' = None,
        value: 'None | Container[int] | int | bool' = None,
    ) -> 'Callable':
        return Input.subscribe(self, type, index, value)  # bypassing MidiIn method


class AbletonOut(MidiOut):
    """Sends [`AbletonMsg`][midiscripter.AbletonMsg] objects
    as MIDI message to Ableton Live remote script.
    """

    _disable_logging_in_send = True

    def __init__(self, proxy_midi_port_name: str, *, virtual: bool = False):
        """
        Args:
            proxy_midi_port_name: The name of proxy MIDI output port enabled in Ableton Live
            virtual: Create virtual MIDI port
        """
        super().__init__(proxy_midi_port_name, virtual=virtual)

    def send(self, msg: AbletonMsg | ChannelMsg) -> None:
        """Send message to Ableton remote script.

        Args:
            msg: object to send
        """
        if isinstance(msg, ChannelMsg):
            super().send(msg)
            log._msg_sent(self, msg)
            return

        try:
            if msg.index is None:
                midi_lead_attrs = ableton_event_to_midi_map[msg.type]
            else:
                midi_lead_attrs = ableton_event_to_midi_map[msg.type][msg.index]

            if msg.value is True:
                value = 127
            elif msg.value is False:
                value = 0
            else:
                value = msg.value

            super().send(ChannelMsg(*midi_lead_attrs, value))
            log._msg_sent(self, msg)

        except (IndexError, KeyError):
            log.red("Invalid message {msg}. Can't convert to MIDI message.", msg=msg)


# noinspection PyMethodOverriding
class AbletonIO(MidiIO):
    _input_port_class: 'type[MidiIn | AbletonIn]' = AbletonIn
    _output_port_class: 'type[MidiOut | AbletonOut]' = AbletonOut

    def __init__(self, proxy_midi_port_name: str, *, virtual: bool = False):
        super().__init__(proxy_midi_port_name, virtual=virtual)

    @overload
    def subscribe(self, call: 'Callable[[AbletonMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container[AbletonEvent] | AbletonEvent' = None,
        index: 'None | Container | int | tuple[int, int]' = None,
        value: 'None | Container[int] | int | bool' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container[AbletonEvent] | AbletonEvent' = None,
        index: 'None | Container[int, tuple[int, int]] | int | tuple[int, int]' = None,
        value: 'None | Container[int] | int | bool' = None,
    ) -> 'Callable':
        return self._input_ports[0].subscribe(type, index, value)

    def send(self, msg: AbletonMsg | ChannelMsg) -> None:
        """Send message to Ableton remote script.

        Args:
            msg: object to send
        """
        self._output_ports[0].send(msg)
