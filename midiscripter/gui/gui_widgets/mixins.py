from typing import Any
from collections.abc import Sequence

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# noinspection PyUnresolvedReferences
class WrappedQWidgetMixin:
    # Signals are required to emit them from another thread.
    # That is not possible for setter methods below.
    set_content_signal = Signal(object)
    set_value_signal = Signal(object)
    set_selection_signal = Signal(object)
    set_toggle_state_signal = Signal(bool)
    set_color_signal = Signal(object)
    set_range_signal = Signal(object)

    triggered_signal = Signal()
    content_changed_signal = Signal()
    value_changed_signal = Signal()
    selection_changed_signal = Signal()
    toggle_state_changed_signal = Signal()
    range_changed_signal = Signal()

    def __init__(self):
        self._color = None

        self.set_content_signal.connect(self.set_content)
        self.set_value_signal.connect(self.set_value)
        self.set_selection_signal.connect(self.set_selection)
        self.set_toggle_state_signal.connect(self.set_toggle_state)
        self.set_color_signal.connect(self.set_color)
        self.set_range_signal.connect(self.set_range)

    # Setters only, getters not used

    def set_content(self, content: Any | Sequence[Any]) -> None:
        raise NotImplementedError

    def set_range(self, range: tuple[int | float, int | float]) -> None:
        raise NotImplementedError

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qcolor = QColor(color) if isinstance(color, str) else QColor(*color)

        palette = self.palette()
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, qcolor)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, qcolor)
        self.setPalette(palette)

    # Getters and setters

    def get_value(self) -> str | None:
        raise NotImplementedError

    def set_value(self, value: str | int | bool) -> None:
        raise NotImplementedError

    def get_selected_item_index(self) -> int | None:
        raise NotImplementedError

    def get_selected_item_text(self) -> str | None:
        raise NotImplementedError

    def set_selection(self, selection: int | str) -> None:
        raise NotImplementedError

    def get_toggle_state(self) -> bool | None:
        raise NotImplementedError

    def set_toggle_state(self, state: bool) -> None:
        raise NotImplementedError


# noinspection PyUnresolvedReferences
class AdaptiveTextSizeMixin:
    SIZE_CHANGE_INCREMENT_DIVIDER: int = 20
    """Sets the balance between CPU load and size change smoothness. Less divider - less load."""

    def __init__(self: QWidget):
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored))
        self.setContentsMargins(10, 5, 10, 5)
        self.__longest_text_rect_size = QFontMetrics(self.font()).boundingRect(self.text()).size()

    def setText(self, text: str) -> None:
        super().setText(text)

        text_rect = QFontMetrics(self.font()).boundingRect(self.text())
        if (
            text_rect.height() > self.__longest_text_rect_size.height()
            or text_rect.width() > self.__longest_text_rect_size.width()
        ):
            self.__make_text_size_fit_widget_size()
            self.__longest_text_rect_size = text_rect

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.__make_text_size_fit_widget_size()

    def __make_text_size_fit_widget_size(self: QWidget) -> None:
        if not self.text():
            return

        font = self.font()
        content_rect = self.contentsRect()

        font_size = 1
        increment = 1
        text_rect = QSize()
        while (
            text_rect.height() < content_rect.height() and text_rect.width() < content_rect.width()
        ):
            # increment decreases CPU load while keeping size change smooth
            increment = int(1 + (font_size / self.SIZE_CHANGE_INCREMENT_DIVIDER))
            font_size += increment
            font.setPointSize(font_size)
            font_metrics = QFontMetrics(font)

            lines_widths = []
            lines_heights = []
            for line in self.text().split('\n'):
                line_rect = font_metrics.boundingRect(line)
                lines_widths.append(line_rect.width())
                lines_heights.append(line_rect.height())

            text_rect = QSize(max(lines_widths), sum(lines_heights))

        font.setPointSize(font_size - increment)
        self.setFont(font)
