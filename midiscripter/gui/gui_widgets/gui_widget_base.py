import types
from typing import TYPE_CHECKING, overload, Any, Self
from collections.abc import Sequence

from PySide6.QtWidgets import *

import midiscripter.base.msg_base
import midiscripter.base.port_base
import midiscripter.gui.app

from .gui_msg import GuiEventMsg, GuiEvent

if TYPE_CHECKING:
    from collections.abc import Container, Callable
    from .mixins import WrappedQWidgetMixin


class GuiWindowItem:
    """GUI windows item (widget, layout) which can also by bound to `GuiWidgetLayout`"""

    _title: str
    """Title for dock widget and position saving, set by content or type if `None`"""

    _title_to_instance: dict[str, 'GuiWindowItem'] = {}
    """Title to instances registry filled by `__init__`"""

    _stretch_multiplier = 1
    """Stretch multiplier for layout. Set by multiplying the object."""

    def __init__(self, content: Any | None = None, title: str | None = None):
        counter = 1
        title_id = title or str(content) or self.__class__.__name__
        title = title_id
        while title in self._title_to_instance:
            counter += 1
            title = f'{title_id} {counter}'

        self._title = title
        self._title_to_instance[self._title] = self

    def __mul__(self, multiplier: int) -> Self:
        self._stretch_multiplier = multiplier
        return self


class GuiWidget(GuiWindowItem, midiscripter.base.port_base.Subscribable):
    """
    GUI windows widget which can have calls subscribed to it's
    [`GuiEventMsg`][midiscripter.GuiEventMsg].
    """

    _log_color: str | None = 'green'
    _log_show_link: bool = False

    _qt_widget_class: type[QWidget, 'WrappedQWidgetMixin']

    _content: str | Sequence[str]
    """Current content cache. Used when `self.qt_widget` has not `.get_content` method."""

    _color: str | tuple[int, int, int] | None = None
    """Current color"""

    _range: tuple[int, int] | None = None
    """Current range"""

    def __init__(
        self,
        content: str | Sequence[str] | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: str | int | bool | None = None,
        select: int | str | None = None,
        toggle_state: bool | None = None,
        range: tuple[int, int] | None = None,
        title: str | None = None,
    ):
        """
        Args:
            content: Widget's text or text for its items
            color: Color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            select: Preselected item
            toggle_state: Initial toggle state
            title: Title for dock widget and position saving, set by content or type if `None`
        """
        midiscripter.base.port_base.Subscribable.__init__(self)
        GuiWindowItem.__init__(self, content, title)

        self.qt_widget = self._qt_widget_class()  # workaround for mkdocstrings issue #607

        self.qt_widget: QWidget | WrappedQWidgetMixin
        """Wrapped `PySide6` `QWidget` that can be altered for extra customization"""

        self.qt_widget.setObjectName(self._title)

        midiscripter.gui.app.add_qwidget(self.qt_widget)

        if isinstance(content, types.GeneratorType):
            content = tuple(content)

        self.content = content

        if value is not None:
            self.value = value
        if select is not None:
            self.select(select)
        if toggle_state is not None:
            self.toggle_state = toggle_state
        if color is not None:
            self.color = color
        if range is not None:
            self.range = range

        self.__connect_change_signals_to_msgs()

    def __str__(self):
        return self.qt_widget.objectName()

    def __connect_change_signals_to_msgs(self) -> None:
        self.qt_widget.triggered_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.TRIGGERED))
        )
        self.qt_widget.content_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.CONTENT_SET, self.content))
        )
        self.qt_widget.value_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.VALUE_CHANGED, self.value))
        )
        self.qt_widget.selection_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEvent.SELECTED, self.selected_item_text)
            )
        )
        self.qt_widget.toggle_state_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.TOGGLED, self.toggle_state))
        )
        self.qt_widget.range_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.RANGE_SET, self.range))
        )

    @property
    def content(self) -> Any | tuple[Any, ...]:
        """Widget's text or text for its items"""
        try:
            return self.qt_widget.get_content()
        except NotImplementedError:
            return self._content

    @content.setter
    def content(self, content: str | Sequence[str]) -> None:
        self._content = content
        self.qt_widget.set_content_signal.emit(content)
        self.qt_widget.content_changed_signal.emit()

    @property
    def value(self) -> str | int | bool | None:
        """Widget's value / selected item text"""
        try:
            return self.qt_widget.get_value()
        except NotImplementedError:
            return None

    @value.setter
    def value(self, value: str | int | bool | None) -> None:
        self.qt_widget.set_value_signal.emit(value)
        self.qt_widget.value_changed_signal.emit()

    @property
    def selected_item_text(self) -> str | None:
        """Widget's currently selected item's text"""
        try:
            return self.qt_widget.get_selected_item_text()
        except NotImplementedError:
            return None

    @property
    def selected_item_index(self) -> int | None:
        """Widget's currently selected item's index"""
        try:
            return self.qt_widget.get_selected_item_index()
        except NotImplementedError:
            return None

    def select(self, selection: int | str) -> None:
        """Select widget's item

        Args:
            selection: Index or text of item to select
        """
        self.qt_widget.set_selection_signal.emit(selection)
        self.qt_widget.selection_changed_signal.emit()

    @property
    def toggle_state(self) -> bool | None:
        """Toggle state"""
        try:
            return self.qt_widget.get_toggle_state()
        except NotImplementedError:
            return None

    @toggle_state.setter
    def toggle_state(self, state: bool) -> None:
        self.qt_widget.set_toggle_state_signal.emit(state)
        self.qt_widget.toggle_state_changed_signal.emit()

    @property
    def range(self) -> tuple[int, int] | None:
        """Value range"""
        return self._range

    @range.setter
    def range(self, range: tuple[int, int]) -> None:
        self._range = range
        self.qt_widget.set_range_signal.emit(range)
        self.qt_widget.range_changed_signal.emit()

    @property
    def color(self) -> str | tuple[int, int, int] | None:
        """Color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple"""
        return self._color

    @color.setter
    def color(self, color: str | tuple[int, int, int]) -> None:
        self._color = color
        self.qt_widget.set_color_signal.emit(color)
        self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.COLOR_SET, color, source=self))

    @property
    def is_visible(self) -> bool:
        """Widget is currently visible"""
        return self.qt_widget.isVisible()

    @overload
    def subscribe(self, call: 'Callable[[GuiEventMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container[GuiEvent] | GuiEvent' = None,
        data: 'None | Container | str | int | bool | Sequence' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container[GuiEvent] | GuiEvent' = None,
        data: 'None | Container | str | int | bool | Sequence' = None,
    ) -> 'Callable':
        return super().subscribe(type, data)
