import types
from typing import TYPE_CHECKING, overload, Any

from PySide6.QtWidgets import *

import midiscripter.base.msg_base
import midiscripter.base.port_base
import midiscripter.gui.app

from .gui_msg import GuiEventMsg, GuiEvent

if TYPE_CHECKING:
    from collections.abc import Container, Callable
    from .mixins import WrappedQWidgetMixin


class GuiWidget(midiscripter.base.port_base.Input):
    """GUI windows widget which also acts like an input port"""

    _qt_widget_class: type[QWidget, 'WrappedQWidgetMixin']

    _content: Any | tuple[Any, ...]
    """Current content"""

    _color: str | tuple[int, int, int] | None = None
    """Current color"""

    _range: tuple[int, int] | None = None
    """Current range"""

    def __init__(
        self,
        title_and_content: Any | tuple[Any, ...],
        content: Any | tuple[Any, ...] | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: str | int | bool | None = None,
        select: int | str | None = None,
        toggle_state: bool | None = None,
        range: tuple[int, int] | None = None,
    ):
        """
        Args:
            title (Any): Widget's title
            content: Widget's text or text for its items
            color: Color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            select: Preselected item
            toggle_state: Initial toggle state
        """
        if isinstance(title_and_content, types.GeneratorType):
            title_and_content = tuple(title_and_content)
        if isinstance(content, types.GeneratorType):
            content = tuple(content)

        self.title = str(title_and_content)
        """Widget's title"""
        super().__init__(self.title)

        self.qt_widget = self._qt_widget_class()  # workaround for mkdocstrings issue #607

        self.qt_widget: QWidget
        """Wrapped `PySide6` `QWidget` that can be altered for extra customization"""

        self.qt_widget.setObjectName(self.title)
        midiscripter.gui.app.add_qwidget(self.qt_widget)

        self.content = content if content is not None else title_and_content

        if value:
            self.value = value
        if select:
            self.select(select)
        if toggle_state:
            self.toggle_state = toggle_state
        if color:
            self.color = color
        if range:
            self.range = range

        self.__connect_change_signals()

    def __connect_change_signals(self) -> None:
        self.qt_widget.triggered_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.TRIGGERED))
        )
        self.qt_widget.content_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEvent.CONTENT_SET, self._content))
        )
        self.qt_widget.value_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEvent.VALUE_CHANGED, self.qt_widget.get_value())
            )
        )
        self.qt_widget.selection_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEvent.SELECTED, self.qt_widget.get_selected_item_text())
            )
        )
        self.qt_widget.toggle_state_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEvent.TOGGLED, self.qt_widget.get_toggle_state())
            )
        )
        self.qt_widget.range_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEvent.RANGE_SET, self.qt_widget.get_range())
            )
        )

    @property
    def content(self) -> Any | tuple[Any, ...]:
        """Widget's text or text for its items"""
        return self._content

    @content.setter
    def content(self, content: Any | tuple[Any, ...]) -> None:
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
