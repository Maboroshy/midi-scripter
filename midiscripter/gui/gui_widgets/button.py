from typing import overload, Any

from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import *

from .gui_widget_base import GuiWidget
from .mixins import AdaptiveTextSizeMixin, WrappedQWidgetMixin


class AdaptablePushButtonWidget(AdaptiveTextSizeMixin, WrappedQWidgetMixin, QPushButton):
    def __init__(self):
        QPushButton.__init__(self)
        WrappedQWidgetMixin.__init__(self)
        AdaptiveTextSizeMixin.__init__(self)
        self.set_content = self.setText

    def set_content(self, content: str) -> None:
        raise self.setText(str(content))


class ButtonWidget(AdaptablePushButtonWidget):
    def __init__(self):
        super().__init__()
        self.clicked.connect(self.triggered_signal)


class GuiButton(GuiWidget):
    """Simple button widget."""

    _qt_widget_class = ButtonWidget

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
    ):
        """
        **Overloads:**
            ``` python
            GuiToggleButton(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
            )
            ```
            ``` python
            GuiToggleButton(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
            )
            ```

        Args:
            title_and_content: Widget's title and button text, should be unique among all widgets.
            content: Button text, if set `title_and_content` is used only for title
            color: Button text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
        """
        super().__init__(title_and_content, content, color=color)


class ToggleButtonWidget(AdaptablePushButtonWidget):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.toggled.connect(self.toggle_state_changed_signal)

        self.get_toggle_state = self.isChecked
        self.set_toggle_state = self.setChecked


class GuiToggleButton(GuiWidget):
    """Toggleable button."""

    _qt_widget_class = ToggleButtonWidget

    @overload
    def __init__(
        self,
        title: Any,
        content: Any,
        *,
        color: str | tuple[int, int, int] | None = None,
        toggle_state: bool | None = None,
    ): ...

    @overload
    def __init__(
        self,
        content: Any,
        *,
        color: str | tuple[int, int, int] | None = None,
        toggle_state: bool | None = None,
    ): ...

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        toggle_state: bool | None = None,
    ):
        """
        **Overloads:**
            ``` python
            GuiToggleButton(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                toggle_state: bool = False
            )
            ```
            ``` python
            GuiToggleButton(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                toggle_state: bool = False
            )
            ```

        Args:
            title (Any): Widget's title
            content: Button text
            color: Button text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            toggle_state: Button initial toggle state
        """
        super().__init__(title_and_content, content, color=color, toggle_state=toggle_state)

    def __bool__(self):
        return self.toggle_state


class ButtonGroupWidgetHorizontal(WrappedQWidgetMixin, QWidget):
    layout_class = QHBoxLayout

    def __init__(self):
        QWidget.__init__(self)
        WrappedQWidgetMixin.__init__(self)
        self.qt_button_group = QButtonGroup()
        self.wrapped_qt_buttons_map = {}

    def set_content(self, button_labels: list[str]) -> None:
        self.qt_button_group.deleteLater()
        self.qt_button_group = QButtonGroup()
        self.wrapped_qt_buttons_map: dict[str | int, AdaptablePushButtonWidget] = {}

        layout = self.layout_class()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        for index, text in enumerate(button_labels):
            text = str(text)

            qt_button = AdaptablePushButtonWidget()
            qt_button.setText(text)
            qt_button.setCheckable(True)

            layout.addWidget(qt_button)
            self.qt_button_group.addButton(qt_button, index)

            self.wrapped_qt_buttons_map[index] = qt_button
            self.wrapped_qt_buttons_map[text] = qt_button

        self.qt_button_group.idReleased.connect(self.selection_changed_signal)

    def set_selection(self, selection: int | str) -> None:
        try:
            self.wrapped_qt_buttons_map[selection].click()
        except KeyError:
            pass

    def get_selected_item_index(self) -> int | None:
        return self.qt_button_group.checkedId()

    def get_selected_item_text(self) -> str | None:
        if self.qt_button_group.checkedButton():
            return self.qt_button_group.checkedButton().text()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        font_sizes_and_fonts = {
            button.font().pixelSize(): button.font()
            for button in self.wrapped_qt_buttons_map.values()
        }
        smallest_font = font_sizes_and_fonts[min(font_sizes_and_fonts)]
        [button.setFont(smallest_font) for button in self.wrapped_qt_buttons_map.values()]


class GuiButtonSelectorH(GuiWidget):
    """Button group to select value, horizontal layout."""

    _qt_widget_class = ButtonGroupWidgetHorizontal

    @overload
    def __init__(
        self,
        title: str,
        content: tuple[str, ...],
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ): ...

    @overload
    def __init__(
        self,
        content: tuple[str, ...],
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ): ...

    def __init__(
        self,
        title_and_content: Any | tuple[Any, ...] = None,
        content: tuple[Any, ...] | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ):
        """
        **Overloads:**
            ``` python
            GuiButtonSelectorH(
                title: str,
                content: tuple[str, ...],
                *,
                color: str | tuple[int, int, int] | None = None,
                select: int | str | None = None
            )
            ```
            ``` python
            GuiButtonSelectorH(
                content: tuple[str, ...],
                *,
                color: str | tuple[int, int, int] | None = None,
                select: int | str | None = None
            )
            ```

        Args:
            title (Any): Widget's title
            content: Buttons' texts
            color: Selector button's text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            select: text or index of button to select initially
        """
        super().__init__(title_and_content, content, color=color, select=select)


class ButtonGroupWidgetVertical(ButtonGroupWidgetHorizontal):
    layout_class = QVBoxLayout


class GuiButtonSelectorV(GuiWidget):
    """Button group to select value, vertical layout."""

    _qt_widget_class = ButtonGroupWidgetVertical

    @overload
    def __init__(
        self,
        title: str,
        content: tuple[str, ...],
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ): ...

    @overload
    def __init__(
        self,
        content: tuple[str, ...],
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ): ...

    def __init__(
        self,
        title_and_content: Any | tuple[Any, ...] = None,
        content: tuple[Any, ...] | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ):
        """
        **Overloads:**
            ``` python
            GuiButtonSelectorV(
                title: str,
                content: tuple[str, ...],
                *,
                color: str | tuple[int, int, int] | None = None,
                select: int | str | None = None
            )
            ```
            ``` python
            GuiButtonSelectorV(
                content: tuple[str, ...],
                *,
                color: str | tuple[int, int, int] | None = None,
                select: int | str | None = None
            )
            ```

        Args:
            title (Any): Widget's title
            content: Buttons' texts
            color: Selector button's text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            select: text or index of button to select initially
        """
        super().__init__(title_and_content, content, color=color, select=select)
