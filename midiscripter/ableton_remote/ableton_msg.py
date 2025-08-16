from typing import TYPE_CHECKING, overload

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container
    from midiscripter.ableton_remote.ableton_port import AbletonIn


class AbletonEvent(midiscripter.base.msg_base.AttrEnum):
    CUE_VOL = 'CUE_VOL'
    """Cue level control"""
    CROSSFADER = 'CROSSFADER'
    """Crossfader control"""

    DEVICE_BANK = 'DEVICE_BANK'
    """Select device encoder bank by index"""
    DEVICE_BANK_NEXT = 'DEVICE_BANK_NEXT'
    """Select next device encoder bank"""
    DEVICE_BANK_PREV = 'DEVICE_BANK_PREV'
    """Select previous device encoder bank"""
    DEVICE_LOCK = 'DEVICE_LOCK'
    """Device lock (lock "blue hand")"""
    DEVICE_TOGGLE = 'DEVICE_TOGGLE'
    """Toggle selected device on/off"""

    ENCODER = 'ENCODER'
    """Parameters control"""

    FORWARD = 'FORWARD'
    """Fast forward"""

    LOOP = 'LOOP'
    """Loop on/off"""

    MASTER_SEL = 'MASTER_SEL'
    """Master track select"""
    MASTER_VOL = 'MASTER_VOL'
    """Master track volume"""
    METRONOME = 'METRONOME'
    """Metronome on/off"""

    NUDGE_UP = 'NUDGE_UP'
    """Tempo Nudge Up"""
    NUDGE_DOWN = 'NUDGE_DOWN'
    """Tempo Nudge Down"""

    OVERDUB = 'OVERDUB'
    """Overdub on/off"""

    PLAY = 'PLAY'
    """Global play"""
    PUNCH_IN = 'PUNCH_IN'
    """Punch in"""
    PUNCH_OUT = 'PUNCH_OUT'
    """Punch out"""

    REC = 'REC'
    """Global record"""
    REWIND = 'REWIND'
    """Rewind"""

    SESSION_REC = 'SESSION_REC'
    """Session record"""
    STOP = 'STOP'
    """Global stop"""

    TAP_TEMPO = 'TAP_TEMPO'
    """Tap tempo"""
    TEMPO_CONTROL = 'TEMPO_CONTROL'
    """Tempo control"""

    TRACK_ARM = 'TRACK_ARM'
    """Track record arm by index"""
    TRACK_LEFT = 'TRACK_LEFT'
    """Track left"""
    TRACK_RIGHT = 'TRACK_RIGHT'
    """Track right"""
    TRACK_MUTE = 'TRACK_MUTE'
    """Track On/Off by index"""
    TRACK_NEXT_8 = 'TRACK_NEXT_8'
    """Select next 8 tracks to control with track controls"""
    TRACK_PREV_8 = 'TRACK_PREV_8'
    """Select previous 8 tracks to control with track controls"""
    TRACK_SELECT = 'TRACK_SELECT'
    """Track select by index"""
    TRACK_SEND_A = 'TRACK_SEND_A'
    """Track Send A"""
    TRACK_SEND_B = 'TRACK_SEND_B'
    """Track Send B"""
    TRACK_SOLO = 'TRACK_SOLO'
    """Track solo by index"""
    TRACK_STOP = 'TRACK_STOP'
    """Track clip stop by track index"""
    TRACK_VOL = 'TRACK_VOL'
    """Track Volume"""

    UNSUPPORTED = 'UNSUPPORTED'
    """Unknown message"""


class AbletonMsg(midiscripter.base.msg_base.Msg):
    """Ableton Live remote script event message"""

    __match_args__: tuple[str] = ('type', 'index', 'value')

    type: AbletonEvent
    """Ableton Live remote script event"""

    index: None | int = None
    """Track/clip/send index"""

    value: int | bool
    """Control event value"""

    source: 'None | AbletonIn'

    @overload
    def __init__(
        self,
        type: AbletonEvent,
        index: int | tuple[int, int],
        value: int | bool,
        *,
        source: 'None | AbletonIn' = None,
    ): ...

    @overload
    def __init__(
        self, type: AbletonEvent, value: int | bool = True, *, source: 'None | AbletonIn' = None
    ): ...

    def __init__(
        self,
        type: AbletonEvent,
        index_or_value: int | bool = True,
        value: int | bool = None,
        *,
        source: 'None | AbletonIn' = None,
    ):
        """
        **Overloads:**
            ``` python
            AbletonMsg(
                type: AbletonEvent,
                index: int,
                value: int | bool,
                *,
                source: 'None | AbletonIn' = None
            )
            ```
            ``` python
            AbletonMsg(
                type: AbletonEvent,
                value: int | bool,
                *,
                source: 'None | AbletonIn' = None
            )
            ```

        Args:
            type: Ableton Live remote script event
            index (int): Track/encoder/device bank index
            value (int | bool): Control event value (0-127 or True / False)
            source: The [`AbletonIn`][midiscripter.AbletonIn] instance that generated the message
        """
        super().__init__(type, source)
        if value is None:
            self.value = index_or_value
        else:
            self.index = index_or_value
            self.value = value

    def __repr__(self):
        present_attrs = (repr(attr) for attr in self._as_tuple() if attr is not None)
        return f'{self.__class__.__name__}({", ".join(present_attrs)})'

    def matches(
        self,
        type: 'None | Container[AbletonEvent] | AbletonEvent' = None,
        index: 'None | Container[int] | int' = None,
        value: 'None | Container[int] | int | bool' = None,
    ) -> bool:
        return super().matches(type, index, value)
