from typing import TYPE_CHECKING, overload

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container
    from midiscripter.ableton_remote.ableton_port import AbletonIn


class AbletonEvent(midiscripter.base.msg_base.AttrEnum):
    CLIP_LAUNCH = 'CLIP_LAUNCH'
    """Clip launch by (x, y) index"""
    CUE_LEVEL = 'CUE_LEVEL'
    """Cue level control"""
    CROSSFADER = 'CROSSFADER'
    """Crossfader control"""

    DEVICE_BANK = 'DEVICE_BANK'
    """Select Device bank by index"""
    DEVICE_LOCK = 'DEVICE_LOCK'
    """Device lock (lock "blue hand")"""
    DEVICE_NAV_LEFT = 'DEVICE_NAV_LEFT'
    """Device nav left"""
    DEVICE_NAV_RIGHT = 'DEVICE_NAV_RIGHT'
    """Device nav right"""
    DEVICE_BANK_NAV_LEFT = 'DEVICE_BANK_NAV_LEFT'
    """Device bank nav left"""
    DEVICE_BANK_NAV_RIGHT = 'DEVICE_BANK_NAV_RIGHT'
    """Device bank nav right"""
    DEVICE_TOGGLE = 'DEVICE_TOGGLE'
    """Toggle selected device on/off"""
    DRUM_PAD = 'DRUM_PAD'
    """Drum pad Trigger by index"""

    LOOP = 'LOOP'
    """Loop on/off"""

    MASTER_SEL = 'MASTER_SEL'
    """Master track select"""
    MASTER_VOLUME = 'MASTER_VOLUME'
    """Master track volume"""
    METRONOME = 'METRONOME'
    """Metronome on/off"""

    NUDGE_UP = 'NUDGE_UP'
    """Tempo Nudge Up"""
    NUDGE_DOWN = 'NUDGE_DOWN'
    """Tempo Nudge Down"""

    OVERDUB = 'OVERDUB'
    """Overdub on/off"""

    PARAM_CONTROL = 'PARAM_CONTROL'
    """Parameters control"""
    PLAY = 'PLAY'
    """Global play"""
    PUNCH_IN = 'PUNCH_IN'
    """Punch in"""
    PUNCH_OUT = 'PUNCH_OUT'
    """Punch out"""

    REC = 'REC'
    """Global record"""
    REC_QUANT_TOGGLE = 'REC_QUANT_TOGGLE'
    """Record quantization on/off"""
    REDO = 'REDO'
    """Redo"""

    SCENE_UP = 'SCENE_UP'
    """Scene down"""
    SCENE_DOWN = 'SCENE_DOWN'
    """Scene up"""
    SCENE_LAUNCH = 'SCENE_LAUNCH'
    """Scene launch by index"""

    SEEK_FWD = 'SEEK_FWD'
    """Seek forward"""
    SEEK_RWD = 'SEEK_RWD'
    """Seek rewind"""

    SESSION_LEFT = 'SESSION_LEFT'
    """Session left"""
    SESSION_RIGHT = 'SESSION_RIGHT'
    """Session right"""
    SESSION_UP = 'SESSION_UP'
    """Session up"""
    SESSION_DOWN = 'SESSION_DOWN'
    """Session down"""

    SEL_CLIP_LAUNCH = 'SEL_CLIP_LAUNCH'
    """Selected clip launch"""
    SEL_SCENE_LAUNCH = 'SEL_SCENE_LAUNCH'
    """Selected scene launch"""
    SEL_TRACK_MUTE = 'SEL_TRACK_MUTE'
    """Mute Selected Track"""
    SEL_TRACK_REC = 'SEL_TRACK_REC'
    """Arm Selected Track"""
    SEL_TRACK_SOLO = 'SEL_TRACK_SOLO'
    """Solo Selected Track"""

    STOP = 'STOP'
    """Global stop"""
    STOP_ALL_CLIPS = 'STOP_ALL_CLIPS'
    """Stop all clips"""

    TAP_TEMPO = 'TAP_TEMPO'
    """Tap tempo"""
    TEMPO_CONTROL = 'TEMPO_CONTROL'
    """Tempo control CC assignment"""

    TRACK_ARM = 'TRACK_ARM'
    """Track record arm by index"""
    TRACK_LEFT = 'TRACK_LEFT'
    """Track left"""
    TRACK_RIGHT = 'TRACK_RIGHT'
    """Track right"""
    TRACK_MUTE = 'TRACK_MUTE'
    """Track On/Off by index"""
    TRACK_PAN = 'TRACK_PAN'
    """Track Pan"""
    TRACK_SELECT = 'TRACK_SELECT'
    """Track select by index"""
    TRACK_SEND = 'TRACK_SEND'
    """Track Send"""
    TRACK_SOLO = 'TRACK_SOLO'
    """Track solo by index"""
    TRACK_STOP = 'TRACK_STOP'
    """Track clip stop by track index"""
    TRACK_VOL = 'TRACK_VOL'
    """Track Volume"""

    UNDO = 'UNDO'
    """Undo"""

    VIEW_DETAIL = 'VIEW_DETAIL'
    """Detail view switch"""
    VIEW_CLIPTRACK = 'VIEW_CLIPTRACK'
    """Clip/Track view switch"""

    ZOOM_UP = 'ZOOM_UP'
    """Session Zoom up"""
    ZOOM_DOWN = 'ZOOM_DOWN'
    """Session Zoom down"""
    ZOOM_LEFT = 'ZOOM_LEFT'
    """Session Zoom left"""
    ZOOM_RIGHT = 'ZOOM_RIGHT'
    """Session Zoom right"""


class AbletonMsg(midiscripter.base.msg_base.Msg):
    """Ableton Live remote script event message"""

    __match_args__: tuple[str] = ('type', 'index', 'value')

    type: AbletonEvent
    """Ableton Live remote script event"""

    index: None | int | tuple[int, int] = None
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
                index: int | tuple[int, int],
                value: int | bool,
                *,
                source: 'None | AbletonIn' = None
            )
            ```
            ``` python
            AbletonMsg(
                type: AbletonEvent,
                value: int | bool, *,
                source: 'None | AbletonIn' = None
            )
            ```

        Args:
            type: Ableton Live remote script event
            index (int): Track/clip/send index
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
        index: 'None | Container[int, tuple[int, int]] | int | tuple[int, int]' = None,
        value: 'None | Container[int] | int | bool' = None,
    ) -> bool:
        return super().matches(type, index, value)
