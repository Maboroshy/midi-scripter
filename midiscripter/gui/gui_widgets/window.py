import pathlib

from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.shared.util


class CustomIcon(QIcon):
    def __init__(self, color: str | tuple[int, int, int], char: str = ''):
        # storing pixmap, so it won't get garbage collected and crash the app
        self.__pixmap = QPixmap(40, 40)
        self.__pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(self.__pixmap)

        if char:
            font = painter.font()
            font.setPixelSize(38)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(color))
            painter.drawText(self.__pixmap.rect(), Qt.AlignmentFlag.AlignCenter, char)
        else:
            painter.setBrush(QColor(color))
            painter.drawEllipse(1, 1, 38, 38)

        painter.end()

        super().__init__(self.__pixmap)


class GuiWindow(metaclass=midiscripter.shared.util.SupressInitAutorun):
    _widgets_to_add = []
    __icon: QIcon | None = None
    __instance: 'GuiWindow' = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.__init__()
        return cls.__instance
    
    def __init__(self):
        super().__init__()

    @classmethod
    def add_qwidget(cls, qwidget: QWidget) -> None:
        """Add custom pyside6 QWidget to the GUI

        Args:
            qwidget: QWidget instance to add
        """
        if qwidget not in cls._widgets_to_add:
            cls._widgets_to_add.append(qwidget)

    @classmethod
    def _remove_qwidget(cls, qwidget: QWidget) -> None:
        """Remove custom pyside6 QWidget to the GUI"""
        try:
            cls._widgets_to_add.remove(qwidget)
        except ValueError:
            pass

    @classmethod
    def set_custom_icon_path(cls, path: pathlib.Path | str | None) -> None:
        """Set GUI window and tray icon path

        Args:
            path: Icon path, default icon if `None`
        """
        cls.__icon = QIcon(str(path)) if path else None
        QApplication.instance().set_icon.emit(cls._get_icon())

    @classmethod
    def set_led_icon(cls, color: str | tuple[int, int, int] | None, char: str = '') -> None:
        """Set custom GUI window and tray icon as colored LED or character

        Args:
            color: Icon color name or RGB value, default icon if `None`
            char: One or two characters to draw on the icon
        """
        cls.__icon = CustomIcon(color, char) if color else None
        QApplication.instance().set_icon.emit(cls._get_icon())

    @classmethod
    def _get_icon(cls) -> QIcon:
        # Default icon can't be set as a classvar because QIcon needs QApplication inited
        return cls.__icon or QIcon(str(pathlib.Path(midiscripter.__file__).parent / 'resources' / 'icon.ico'))
