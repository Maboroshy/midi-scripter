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
        Use `GuiText('⬤', color='green')` for a toggleable "LED indicator".
    """

    _qt_widget_class = AdaptableLabelWidget

    def __init__(
        self,
        content: str | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        toggle_state: bool = True,
        title: str | None = None,
    ):
        """
        Args:
            content: Widget's text
            color: Text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            toggle_state: False to "grey out" text
            title: Title for dock widget and position saving, set by content or type if `None`
        """
        super().__init__(content, color=color, toggle_state=toggle_state, title=title)


class AdaptableLineEditWidget(AdaptiveTextSizeMixin, WrappedQWidgetMixin, QLineEdit):
    def __init__(self):
        QLineEdit.__init__(self)
        WrappedQWidgetMixin.__init__(self)
        AdaptiveTextSizeMixin.__init__(self)

        self.__last_text: str = ''

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrame(False)
        self.textChanged.connect(self._make_text_size_fit_widget_size)
        self.editingFinished.connect(self.__editing_finished)

    def __editing_finished(self) -> None:
        if self.text() != self.__last_text:
            self.content_changed_signal.emit()
            self.__last_text = self.text()

        self.clearFocus()

    def get_content(self) -> str:
        return self.text()

    def set_content(self, content: str) -> None:
        self.setText(str(content))
        self.__last_text = self.text()

    def get_toggle_state(self) -> bool:
        return self.isEnabled()

    def set_toggle_state(self, state: bool) -> None:
        self.setEnabled(state)

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qcolor = QColor(color) if isinstance(color, str) else QColor(*color)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Text, qcolor)
        self.setPalette(palette)


class GuiEditableText(GuiWidget):
    """Editable text widget"""

    _qt_widget_class = AdaptableLineEditWidget
    qt_widget: AdaptableLineEditWidget

    def __init__(
        self,
        content: str | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        toggle_state: bool = True,
        title: str | None = None,
    ):
        """
        Args:
            content: Widget's text
            color: Text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            toggle_state: False to disable and "grey out" text
            title: Title for dock widget and position saving, set by content or type if `None`
        """
        super().__init__(content, color=color, toggle_state=toggle_state, title=title)

    @property
    def content(self) -> str:
        return self.qt_widget.text()

    @content.setter
    def content(self, content: str) -> None:
        self.qt_widget.set_content_signal.emit(content)
        self.qt_widget.content_changed_signal.emit()
