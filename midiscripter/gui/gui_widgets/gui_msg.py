from typing import TYPE_CHECKING

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Sequence, Container
    from midiscripter.gui.gui_widgets.gui_widget_base import GuiWidget


class GuiEventType(midiscripter.base.msg_base.AttrEnum):
    """GUI event type enumerator to use as [`GuiEventMsg`][midiscripter.GuiEventMsg] `type` attribute."""

    TRIGGERED = 'TRIGGERED'
    CONTENT_SET = 'CONTENT_SET'
    COLOR_SET = 'COLOR_SET'
    TOGGLED = 'TOGGLED'
    SELECTED = 'SELECTED'
    VALUE_CHANGED = 'VALUE_CHANGED'


class GuiEventMsg(midiscripter.base.msg_base.Msg):
    """GUI interaction message produced by GUI widget port."""

    type: GuiEventType
    """GUI event type."""

    data: 'str | int | bool | Sequence | None'
    """New value set by event.
    
    Data meaning for event types:  
    TRIGGERED - None.  
    CONTENT_SET - New content.  
    COLOR_SET - New text color.  
    TOGGLED - New toggle state.  
    SELECTED - Selected item text.  
    VALUE_CHANGED - New value.
    """

    source: 'None | GuiWidget'

    __match_args__: tuple[str] = ('type', 'data')

    def __init__(
        self,
        type: GuiEventType,
        data: 'str | int | bool | Sequence | None' = None,
        *,
        source: 'None | GuiWidget' = None,
    ):
        super().__init__(source)
        self.type = type
        self.data = data

    def matches(
        self,
        type: 'None | Container[GuiEventType] | GuiEventType' = None,
        data: 'None | Container[str | int | bool | Sequence | None] | \
                       str | int | bool | Sequence | None' = None,
    ) -> bool:
        return super().matches(type, data)
