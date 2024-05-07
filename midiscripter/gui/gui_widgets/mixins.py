from collections.abc import Sequence

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


# noinspection PyUnresolvedReferences
class WrappedQWidgetMixin:
    # Signals are required to emit them from another thread that is not possible for setter methods below
    set_content_signal = Signal(object)
    set_value_signal = Signal(object)
    set_selection_signal = Signal(object)
    set_toggle_state_signal = Signal(bool)
    set_color_signal = Signal(object)

    triggered_signal = Signal()
    content_changed_signal = Signal()
    value_changed_signal = Signal()
    selection_changed_signal = Signal()
    toggle_state_changed_signal = Signal()

    def __init__(self):
        self.__color = None

        self.set_content_signal.connect(self.set_content)
        self.set_value_signal.connect(self.set_value)
        self.set_selection_signal.connect(self.set_selection)
        self.set_toggle_state_signal.connect(self.set_toggle_state)
        self.set_color_signal.connect(self.set_color)

    def get_content(self) -> str | Sequence[str]:
        raise NotImplementedError

    def set_content(self, new_content: str | Sequence[str]) -> None:
        raise NotImplementedError

    def get_value(self) -> str | None:
        raise NotImplementedError

    def set_value(self, new_value: str | int | bool) -> None:
        raise NotImplementedError

    def get_selected_item_index(self) -> int | None:
        raise NotImplementedError

    def get_selected_item_text(self) -> str | None:
        raise NotImplementedError

    def set_selection(self, selection: int | str) -> None:
        raise NotImplementedError

    def get_toggle_state(self) -> bool | None:
        raise NotImplementedError

    def set_toggle_state(self, new_state: bool) -> None:
        raise NotImplementedError

    def get_color(self) -> str | None:
        return self.__color

    def set_color(self, new_color_value: str | tuple[int, int, int]) -> None:
        if isinstance(new_color_value, str):
            color = QColor(new_color_value)
        else:
            color = QColor(*new_color_value)

        palette = self.palette()
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, color)
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, color)
        self.setPalette(palette)
        self.__color = new_color_value


# noinspection PyUnresolvedReferences, PyPep8Naming
class AdaptiveTextSizeMixin:
    def __init__(self):
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

    def __make_text_size_fit_widget_size(self) -> None:
        if not self.text():
            return

        font = self.font()
        content_rect = self.contentsRect()

        font_size = 0
        text_rect = QSize()
        while (
            text_rect.height() < content_rect.height() and text_rect.width() < content_rect.width()
        ):
            font_size += 1
            font.setPixelSize(font_size)
            text_rect = QFontMetrics(font).boundingRect(self.text())

        self.setFont(font)
