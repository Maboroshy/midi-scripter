from typing import overload, Any

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .gui_widget_base import GuiWidget
from .mixins import AdaptiveTextSizeMixin, WrappedQWidgetMixin


class AdaptableLabelWidget(AdaptiveTextSizeMixin, WrappedQWidgetMixin, QLabel):
    def __init__(self):
        QLabel.__init__(self)
        WrappedQWidgetMixin.__init__(self)
        AdaptiveTextSizeMixin.__init__(self)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_content(self, content: str) -> None:
        self.setText(str(content))

    def get_toggle_state(self) -> bool:
        return self.isEnabled()

    def set_toggle_state(self, state: bool) -> None:
        self.setEnabled(state)


class GuiText(GuiWidget):
    """Text widget. Goes grey on toggle off.

    Tip:
        Use `GuiText('⬤', 'LED 1', 'green')` for a toggleable "LED indicator".
    """

    _qt_widget_class = AdaptableLabelWidget

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
        toggle_state: bool = False,
    ):
        """
        **Overloads:**
            ``` python
            GuiText(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                toggle_state: bool = False
            )
            ```
            ``` python
            GuiText(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                toggle_state: bool = False
            )
            ```

        Args:
            title (Any): Widget's title
            content: Widget's text
            color: Text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            toggle_state: Text "grey out" state
        """
        super().__init__(title_and_content, content, color=color, toggle_state=toggle_state)
