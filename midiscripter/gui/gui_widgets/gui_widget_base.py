import types
from typing import TYPE_CHECKING
from collections.abc import Sequence

from PySide6.QtWidgets import *

import midiscripter.base.msg_base
import midiscripter.base.port_base
import midiscripter.gui.app

from .gui_msg import GuiEventMsg, GuiEventType

if TYPE_CHECKING:
    from .mixins import WrappedQWidgetMixin


class GuiWidget(midiscripter.base.port_base.Input):
    """GUI windows widget which also acts like an input port."""

    _qt_widget_class: type[QWidget, 'WrappedQWidgetMixin']

    def __init__(
        self,
        content: str | tuple[str, ...],
        title: str | None = None,
        color: str | tuple[int, int, int] | None = None,
        *,
        value: str | None = None,
        select: int | str | None = None,
        toggle_state: bool | None = None,
    ):
        """
        Args:
            content: Widget's text or text for its items
            title: Widget's title, `None` for same as content
            color: Preset text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Preset value
            select: Preset item text / index to select
            toggle_state: Preset toggle state
        """
        if isinstance(content, types.GeneratorType):
            content = tuple(content)

        self.title = title or str(content)
        """Widget's title."""
        super().__init__(self.title)

        self.qt_widget = self._qt_widget_class()  # workaround for mkdocstrings issue #607

        self.qt_widget: QWidget
        """Wrapped `PySide6` `QWidget` that can be altered for extra customization."""

        self.qt_widget.setObjectName(self.title)
        midiscripter.gui.app.add_qwidget(self.qt_widget)

        self.content = content

        if value:
            self.value = value

        if select:
            self.select(select)

        if toggle_state:
            self.toggle_state = toggle_state

        if color:
            self.color = color

        self.__connect_change_signals()

    def __connect_change_signals(self) -> None:
        self.qt_widget.triggered_signal.connect(
            lambda: self._send_input_msg_to_calls(GuiEventMsg(GuiEventType.TRIGGERED))
        )
        self.qt_widget.content_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEventType.CONTENT_SET, self.qt_widget.get_content())
            )
        )
        self.qt_widget.value_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEventType.VALUE_CHANGED, self.qt_widget.get_value())
            )
        )
        self.qt_widget.selection_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEventType.SELECTED, self.qt_widget.get_selected_item_text())
            )
        )
        self.qt_widget.toggle_state_changed_signal.connect(
            lambda: self._send_input_msg_to_calls(
                GuiEventMsg(GuiEventType.TOGGLED, self.qt_widget.get_toggle_state())
            )
        )

    @property
    def content(self) -> str | tuple[str, ...]:
        """Widget's text or text for its items."""
        return self.qt_widget.get_content()

    @content.setter
    def content(self, new_content: str | tuple[str, ...]) -> None:
        self.qt_widget.set_content_signal.emit(new_content)
        self.qt_widget.content_changed_signal.emit()

    @property
    def value(self) -> str | None:
        """Widget's value / selected item text."""
        try:
            return self.qt_widget.get_value()
        except NotImplementedError:
            return None

    @value.setter
    def value(self, new_value: str | None) -> None:
        self.qt_widget.set_value_signal.emit(new_value)
        self.qt_widget.value_changed_signal.emit()

    @property
    def selected_item_text(self) -> str | None:
        """Widget's currently selected item's text."""
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
        """Toggle state."""
        try:
            return self.qt_widget.get_toggle_state()
        except NotImplementedError:
            return None

    @toggle_state.setter
    def toggle_state(self, new_state: bool) -> None:
        self.qt_widget.set_toggle_state_signal.emit(new_state)
        self.qt_widget.toggle_state_changed_signal.emit()

    @property
    def color(self) -> str | tuple[int, int, int] | None:
        """Text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple"""
        return self.qt_widget.get_color()

    @color.setter
    def color(self, new_color_value: str | tuple[int, int, int]) -> None:
        self.qt_widget.set_color_signal.emit(new_color_value)
        self._send_input_msg_to_calls(
            GuiEventMsg(GuiEventType.COLOR_SET, new_color_value, source=self)
        )

    @property
    def is_visible(self) -> bool:
        """Widget is currently visible."""
        return self.qt_widget.isVisible()
