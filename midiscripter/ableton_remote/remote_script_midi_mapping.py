from midiscripter.midi.midi_msg import MidiType
from .ableton_msg import AbletonEvent


_BUTTONS_CC_VALUES = {
    AbletonEvent.DEVICE_BANK: list(range(17, 25)),
    AbletonEvent.DEVICE_BANK_NEXT: 25,
    AbletonEvent.DEVICE_BANK_PREV: 26,
    AbletonEvent.DEVICE_TOGGLE: 27,
    AbletonEvent.DEVICE_LOCK: 28,
    AbletonEvent.TRACK_MUTE: list(range(53, 61)),
    AbletonEvent.TRACK_SOLO: list(range(61, 69)),
    AbletonEvent.TRACK_SELECT: list(range(69, 77)),
    AbletonEvent.TRACK_ARM: list(range(77, 85)),
    AbletonEvent.TRACK_NEXT_8: 85,
    AbletonEvent.TRACK_PREV_8: 86,
    AbletonEvent.MASTER_VOL: 87,
    AbletonEvent.CUE_VOL: 88,
    AbletonEvent.CROSSFADER: 89,
    AbletonEvent.STOP: 90,
    AbletonEvent.PLAY: 91,
    AbletonEvent.REC: 92,
    AbletonEvent.SESSION_REC: 93,
    AbletonEvent.OVERDUB: 94,
    AbletonEvent.METRONOME: 95,
    AbletonEvent.LOOP: 96,
    AbletonEvent.REWIND: 97,
    AbletonEvent.FORWARD: 98,
    AbletonEvent.PUNCH_IN: 99,
    AbletonEvent.PUNCH_OUT: 100,
    AbletonEvent.NUDGE_UP: 101,
    AbletonEvent.NUDGE_DOWN: 102,
    AbletonEvent.TAP_TEMPO: 103,
}

_SLIDERS_CC_VALUES = {
    AbletonEvent.ENCODER: list(range(1, 17)),
    AbletonEvent.TRACK_VOL: list(range(29, 37)),
    AbletonEvent.TRACK_SEND_A: list(range(37, 45)),
    AbletonEvent.TRACK_SEND_B: list(range(45, 53)),
}

_MESSAGETYPE = MidiType.CONTROL_CHANGE
_CHANNEL = 15


def _cc_map_to_msg_map(
    cc_map: dict[AbletonEvent, int | list],
) -> dict[AbletonEvent, tuple[MidiType, int, int] | list[tuple[MidiType, int, int]]]:
    msg_map = {}
    for event, value in cc_map.items():
        if isinstance(value, int):
            msg_map[event] = (_MESSAGETYPE, _CHANNEL, value)
        elif isinstance(value, list):
            msg_map[event] = [(_MESSAGETYPE, _CHANNEL, sub_value) for sub_value in value]
    return msg_map


def _reversed_event_to_msg_map(
    source_map: dict[AbletonEvent, tuple[MidiType, int, int] | list],
) -> dict[tuple[MidiType, int, int], tuple[AbletonEvent, int | None]]:
    reversed_map = {}
    for event, item in source_map.items():
        if isinstance(item, tuple):
            reversed_map[item] = (event, None)
        elif isinstance(item, list):
            for index, attrs in enumerate(item):
                reversed_map[attrs] = (event, index)

    return reversed_map


ableton_button_to_midi_attrs_map = _cc_map_to_msg_map(_BUTTONS_CC_VALUES)
ableton_slider_to_midi_attrs_map = _cc_map_to_msg_map(_SLIDERS_CC_VALUES)

ableton_event_to_midi_map = ableton_button_to_midi_attrs_map | ableton_slider_to_midi_attrs_map

midi_to_ableton_button_map = _reversed_event_to_msg_map(ableton_button_to_midi_attrs_map)
midi_to_ableton_slider_map = _reversed_event_to_msg_map(ableton_slider_to_midi_attrs_map)
