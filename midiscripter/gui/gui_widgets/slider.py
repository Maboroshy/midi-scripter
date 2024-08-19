from typing import overload, Any

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from .gui_widget_base import GuiWidget
from .mixins import WrappedQWidgetMixin, AdaptiveTextSizeMixin


class _WrappedSliderMixin(WrappedQWidgetMixin):
    label: QLabel
    slider: QAbstractSlider | QProgressBar

    _label_text: str
    """Current label"""

    def __init__(self):
        super().__init__()
        self.slider.valueChanged.connect(self.value_changed_signal)
        self.slider.valueChanged.connect(self._update_label)

    def _update_label(self) -> None:
        raise NotImplementedError

    def set_content(self, content: str) -> None:
        self._label_text = str(content)
        self._update_label()

    def get_value(self) -> float:
        return self.slider.value()

    def set_value(self, value: int) -> None:
        self.slider.setValue(value)

    def set_range(self, range: tuple[int, int]) -> None:
        self.slider.setRange(*range)


class _SliderLabel(AdaptiveTextSizeMixin, QLabel):
    def __init__(self, parent: QWidget):
        QLabel.__init__(self, parent)
        AdaptiveTextSizeMixin.__init__(self)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class KnobWidget(_WrappedSliderMixin, QDial):
    def __init__(self):
        QDial.__init__(self)

        self.slider = self
        self.setNotchesVisible(True)
        self.setStyleSheet('QDial {background-color: white}')

        self.label = _SliderLabel(self)
        self.label.show()

        _WrappedSliderMixin.__init__(self)

    def _update_label(self) -> None:
        self.label.setText(f'{self._label_text}\n{self.slider.value()}')

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qss_color = color if isinstance(color, str) else f'rgb{str(color)}'
        self.setStyleSheet(f'QDial {{ background-color: {qss_color} }}')

    def resizeEvent(self, event: QResizeEvent) -> None:
        QDial.resizeEvent(self, event)
        self.label.setFixedSize(self.size() / 2)
        self.label.move(self.rect().center() - self.label.rect().center())


class VerticalSliderWidget(_WrappedSliderMixin, QWidget):
    def __init__(self):
        QWidget.__init__(self)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.setLayout(layout)

        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setFixedWidth(30)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.slider, 3, Qt.AlignmentFlag.AlignHCenter)

        self.label = _SliderLabel(self)
        self.label.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label, 1)

        _WrappedSliderMixin.__init__(self)

    def _update_label(self) -> None:
        self.label.setText(f'{self._label_text}\n{self.slider.value()}')

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qss_color = color if isinstance(color, str) else f'rgb{str(color)}'
        self.slider.setStyleSheet(f'QSlider::handle {{ background-color: {qss_color} }}')


class HorizontalSliderWidget(_WrappedSliderMixin, QWidget):
    def __init__(self):
        QWidget.__init__(self)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.setLayout(layout)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setFixedHeight(30)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.slider, 2, Qt.AlignmentFlag.AlignVCenter)

        self.label = _SliderLabel(self)
        self.label.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label, 1)

        _WrappedSliderMixin.__init__(self)

    def _update_label(self) -> None:
        self.label.setText(f'{self._label_text}: {self.slider.value()}')

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qss_color = color if isinstance(color, str) else f'rgb{str(color)}'
        self.slider.setStyleSheet(f'QSlider::handle {{ background-color: {qss_color} }}')


class VerticalProgressBarWidget(_WrappedSliderMixin, QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setStyle(QStyleFactory.create('Fusion'))
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.slider = QProgressBar()
        layout.addWidget(self.slider, 6, Qt.AlignmentFlag.AlignHCenter)
        self.slider.setOrientation(Qt.Orientation.Vertical)
        self.slider.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.slider.setFormat('%v')

        self.label = _SliderLabel(self)
        self.label.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label, 1)

        _WrappedSliderMixin.__init__(self)

    # noinspection PyMethodOverriding
    def _update_label(self) -> None:
        self.label.setText(self._label_text)

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qcolor = QColor(color) if isinstance(color, str) else QColor(*color)

        palette = self.slider.palette()
        palette.setColor(QPalette.ColorRole.Highlight, qcolor)
        self.slider.setPalette(palette)


class HorizontalProgressBarWidget(_WrappedSliderMixin, QWidget):
    orientation: Qt.Orientation = Qt.Orientation.Horizontal

    def __init__(self):
        QWidget.__init__(self)
        self.setStyle(QStyleFactory.create('Fusion'))

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.slider = QProgressBar()
        layout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignVCenter)
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        _WrappedSliderMixin.__init__(self)

    # noinspection PyMethodOverriding
    def _update_label(self) -> None:
        self.slider.setFormat(f'{self._label_text}: %v')

    def set_color(self, color: str | tuple[int, int, int]) -> None:
        qcolor = QColor(color) if isinstance(color, str) else QColor(*color)

        palette = self.slider.palette()
        palette.setColor(QPalette.ColorRole.Highlight, qcolor)
        self.slider.setPalette(palette)


class _GuiSliderWidgetBase(GuiWidget):
    _qt_widget_class: QWidget

    @overload
    def __init__(
        self,
        title: Any,
        content: Any,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ): ...

    @overload
    def __init__(
        self,
        content: Any,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ): ...

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ):
        super().__init__(title_and_content, content, color=color, value=value, range=range)


class GuiKnob(_GuiSliderWidgetBase):
    """Knob to set value."""

    _qt_widget_class = KnobWidget

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ):
        """
        **Overloads:**
            ``` python
            GuiKnob(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```
            ``` python
            GuiKnob(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```

        Args:
            title (Any): Widget's title
            content: Knob label
            color: Knob color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            range: Knob value range
        """
        super().__init__(title_and_content, content, color=color, value=value, range=range)


class GuiSliderV(_GuiSliderWidgetBase):
    """Vertical slider to set value."""

    _qt_widget_class = VerticalSliderWidget

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ):
        """
        **Overloads:**
            ``` python
            GuiSliderVertical(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```
            ``` python
            GuiSliderVertical(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```

        Args:
            title (Any): Widget's title
            content: Slider label
            color: Slider handle color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            range: Slider value range
        """
        super().__init__(title_and_content, content, color=color, value=value, range=range)


class GuiSliderH(_GuiSliderWidgetBase):
    """Horizontal slider to set value."""

    _qt_widget_class = HorizontalSliderWidget

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ):
        """
        **Overloads:**
            ``` python
            GuiSliderHorizontal(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```
            ``` python
            GuiSliderHorizontal(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```

        Args:
            title (Any): Widget's title
            content: Slider label
            color: Slider handle color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            range: Slider value range
        """
        super().__init__(title_and_content, content, color=color, value=value, range=range)


class GuiProgressBarH(_GuiSliderWidgetBase):
    """Horizontal slider to set value."""

    _qt_widget_class = HorizontalProgressBarWidget

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ):
        """
        **Overloads:**
            ``` python
            GuiProgressBarHorizontal(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```
            ``` python
            GuiProgressBarHorizontal(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```

        Args:
            title (Any): Widget's title
            content: Progress bar label
            color: Progress color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            range: Progress bar value range
        """
        super().__init__(title_and_content, content, color=color, value=value, range=range)


class GuiProgressBarV(_GuiSliderWidgetBase):
    """Horizontal slider to set value."""

    _qt_widget_class = VerticalProgressBarWidget

    def __init__(
        self,
        title_and_content: Any,
        content: Any | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        value: int = 0,
        range: tuple[int, int] = (0, 100),
    ):
        """
        **Overloads:**
            ``` python
            GuiProgressBarVertical(
                title: Any,
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```
            ``` python
            GuiProgressBarVertical(
                content: Any,
                *,
                color: str | tuple[int, int, int] | None = None,
                value: int = 0,
                range: tuple[int, int] = (0, 100)
            )
            ```

        Args:
            title (Any): Widget's title
            content: Progress bar label
            color: Progress color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            value: Initial value
            range: Progress bar value range
        """
        super().__init__(title_and_content, content, color=color, value=value, range=range)
