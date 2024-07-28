from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.shared
import midiscripter.gui.log_widget
import midiscripter.gui.menu_bar
import midiscripter.gui.ports_widget
import midiscripter.gui.message_sender


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent: 'MainWindow' = None):
        super().__init__(icon, parent)
        self.setToolTip(QApplication.instance().applicationDisplayName())
        self.activated.connect(self.__activated)

        menu = QMenu(parent)
        menu.setDefaultAction(menu.addAction('Open GUI', parent.showNormal))
        self.restart_act = menu.addAction('Restart script', QApplication.instance().restart)
        menu.addAction('Quit', QApplication.instance().exit)
        self.setContextMenu(menu)

    def __activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.parent().isVisible():
                self.parent().close()
            else:
                self.parent().show_from_tray()

        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.restart_act.trigger()


class MainWindow(QMainWindow):
    dock_widgets: list[QDockWidget] = []

    def __init__(self, widgets_to_add: list[QWidget]):
        super().__init__()
        self.__normal_flags = self.windowFlags()
        self.__always_on_top_flags = self.__normal_flags | Qt.WindowStaysOnTopHint

        self.setDockNestingEnabled(True)

        self.setStyleSheet("""
            QMainWindow::separator:hover, QMainWindow::separator:pressed {background: cyan}
        """)

        self.__prepare_dock_widgets(widgets_to_add)

        self.menu_bar = midiscripter.gui.menu_bar.MenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.tray = TrayIcon(self.windowIcon(), self)
        self.tray.show()

        self.__load_state()

    def set_dock_titles_visibility(self, are_hidden: bool) -> None:
        # Can't make full lock with setFixedSize due to AdaptiveTextSizeWidgets
        # that has "Ignore" size policy and always restore at maximum size after that
        for dock in self.dock_widgets:
            dock_title_widget = QWidget() if are_hidden else None
            dock.setTitleBarWidget(dock_title_widget)

        if are_hidden:
            self.setStyleSheet("""
                QMainWindow::separator:hover, QMainWindow::separator:pressed {background: cyan}
            """)
        else:
            self.setStyleSheet("""
                QMainWindow::separator { background: lightgrey }
                QMainWindow::separator:hover, QMainWindow::separator:pressed {background: cyan}
            """)

    def set_always_on_top(self, state: bool) -> None:
        if state:
            self.setWindowFlags(self.__always_on_top_flags)
        else:
            self.setWindowFlags(self.__normal_flags)
        self.show()

    def show_from_tray(self) -> None:
        if QSettings().value('win maximized', False, type=bool):
            self.showMaximized()
        else:
            self.showNormal()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()

        QSettings().setValue('win state', self.saveState())
        QSettings().setValue('win maximized', self.isMaximized())

        if not self.isMaximized():
            QSettings().setValue('win size', self.size())
            QSettings().setValue('win position', self.pos())

        self.hide()

    def __prepare_dock_widgets(self, widgets_to_add: list[QWidget]) -> None:
        self.ports_widget = midiscripter.gui.ports_widget.PortsWidget()
        self.log_widget = midiscripter.gui.log_widget.LogWidget()
        self.message_sender_widget = midiscripter.gui.message_sender.MessageSender()

        self.__add_widget_as_dock(self.ports_widget, fix_width=True)
        self.__add_widget_as_dock(self.log_widget)
        self.__add_widget_as_dock(self.message_sender_widget, hidden_by_default=True)

        for widget in widgets_to_add:
            self.__add_widget_as_dock(widget)

    def __add_widget_as_dock(
        self, widget: QWidget, *, fix_width: bool = False, hidden_by_default: bool = False
    ) -> None:
        dock = QDockWidget(self)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        dock.setObjectName(widget.objectName())
        dock.setWindowTitle(widget.objectName())
        dock.setWidget(widget)
        dock.setMinimumSize(QSize(30, 30))

        if fix_width:
            dock.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)
        self.dock_widgets.append(dock)

        if hidden_by_default:
            dock.hide()

    def __load_state(self) -> None:
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.restoreState(QSettings().value('win state'))
        self.resize(QSettings().value('win size', QSize(800, 500)))
        self.move(QSettings().value('win position', self.__get_screen_center()))

    def __get_screen_center(self) -> QPoint:
        return (
            self.screen().geometry().center()
            - QRect(QPoint(), self.frameGeometry().size()).center()
        )
