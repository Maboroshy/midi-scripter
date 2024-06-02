from typing import TYPE_CHECKING

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container
    from midiscripter.mouse.mouse_port import MouseIn


class MouseEvent(midiscripter.base.msg_base.AttrEnum):
    """Mouse event message type enumerator
    to use as [`MouseMsg`][midiscripter.MouseMsg] `type` attribute."""

    MOVE = 'MOVE'

    LEFT_CLICK = 'LEFT_CLICK'
    """Left button press and release. Isn't assigned by [`MouseIn`][midiscripter.MouseIn] 
       but can be sent with [`MouseOut`][midiscripter.MouseOut]."""
    MIDDLE_CLICK = 'MIDDLE_CLICK'
    """Middle button press and release. Isn't assigned by [`MouseIn`][midiscripter.MouseIn] 
       but can be sent with [`MouseOut`][midiscripter.MouseOut]."""
    RIGHT_CLICK = 'RIGHT_CLICK'
    """Right button press and release. Isn't assigned by [`MouseIn`][midiscripter.MouseIn] 
       but can be sent with [`MouseOut`][midiscripter.MouseOut]."""

    LEFT_PRESS = 'LEFT_PRESS'
    MIDDLE_PRESS = 'MIDDLE_PRESS'
    RIGHT_PRESS = 'RIGHT_PRESS'

    LEFT_RELEASE = 'LEFT_RELEASE'
    MIDDLE_RELEASE = 'MIDDLE_RELEASE'
    RIGHT_RELEASE = 'RIGHT_RELEASE'

    SCROLL_UP = 'SCROLL_UP'
    SCROLL_DOWN = 'SCROLL_DOWN'
    SCROLL_LEFT = 'SCROLL_LEFT'
    SCROLL_RIGHT = 'SCROLL_RIGHT'


class MouseMsg(midiscripter.base.msg_base.Msg):
    """Keyboard event message"""

    __match_args__ = ('type', 'x', 'y')

    type: MouseEvent
    """Mouse event type"""

    x: int
    """Event horizontal screen coordinates"""

    y: int
    """Event vertical screen coordinates"""

    source: 'None | MouseIn'

    def __init__(
        self,
        type: MouseEvent,
        x: int,
        y: int,
        *,
        source: 'None | MouseIn' = None,
    ):
        """
        Args:
            type: Mouse event type
            x: Event horizontal axis coordinates
            y: Event vertical axis coordinates
            source: The [`MouseIn`][midiscripter.MouseIn] instance that generated the message

        Tip:
            Run GUI and Enable mouse input. Use log to get mouse events you need.
        """
        super().__init__(type, source)
        self.x = x
        self.y = y

    def matches(
        self,
        type: 'None | Container[MouseEvent] | MouseEvent' = None,
        x: 'None | Container[int] | int' = None,
        y: 'None | Container[int] | int' = None,
    ) -> bool:
        return super().matches(type, x, y)
