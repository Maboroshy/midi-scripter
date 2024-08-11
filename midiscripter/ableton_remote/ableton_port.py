from typing import overload, TYPE_CHECKING

import midiscripter.midi
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
    from midiscripter.base.msg_base import Msg


# noinspection PyMethodOverriding
class AbletonIn(midiscripter.midi.MidiIn):
    """Receives MIDI messages from Ableton Live remote script
    and produces [`AbletonMsg`][midiscripter.AbletonMsg] objects.
    """

    def __init__(self, proxy_midi_port_name: str, *, virtual: bool = False):
        """
        Args:
            proxy_midi_port_name: The name of proxy MIDI input port enabled in Ableton Live
            virtual: Create virtual port (Linux and macOS only)
        """
        super().__init__(proxy_midi_port_name, virtual=virtual)

    def _convert_to_msg(self, rt_midi_data: tuple[hex, ...]) -> 'AbletonMsg':
        msg_atts = self._raw_channel_midi_to_attrs(rt_midi_data)
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

        raise ValueError(f'{self} got invalid MIDI input: {msg_atts}')

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


class AbletonOut(midiscripter.midi.MidiOut):
    """Sends [`AbletonMsg`][midiscripter.AbletonMsg] objects
    as MIDI message to Ableton Live remote script.
    """

    def __init__(self, proxy_midi_port_name: str, *, virtual: bool = False):
        """
        Args:
            proxy_midi_port_name: The name of proxy MIDI output port enabled in Ableton Live
            virtual: Create virtual port (Linux and macOS only)
        """
        super().__init__(proxy_midi_port_name, virtual=virtual)

    def send(self, msg: AbletonMsg) -> None:
        """Send message to Ableton remote script.

        Args:
            msg: object to send
        """
        try:
            if msg.index is None:
                midi_lead_attrs = ableton_event_to_midi_map[msg.type]
            elif isinstance(msg.index, tuple) and len(msg.index) == 2:
                midi_lead_attrs = ableton_event_to_midi_map[msg.type][msg.index[0]][msg.index[1]]
            else:
                midi_lead_attrs = ableton_event_to_midi_map[msg.type][msg.index]

            if msg.value is True:
                value = 127
            elif msg.value is False:
                value = 0
            else:
                value = msg.value

            super().send(midiscripter.midi.ChannelMsg(*midi_lead_attrs, value))
            super()._log_msg_sent(msg)

        except (IndexError, KeyError):
            log.red("Invalid {msg}. Can't convert to MIDI message.", msg=msg)

    def _log_msg_sent(self, msg: 'Msg') -> None:
        """Overriding MidiOut method.
        Otherwise sent message will be logged as MidiMsg rather that AbletonMsg.
        """
        pass
