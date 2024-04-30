from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.base.shared
import midiscripter.gui.log_widget
import midiscripter.gui.menu_bar
import midiscripter.gui.ports_widget


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent: 'MainWindow' = None):
        super().__init__(icon, parent)
        self.setToolTip(QApplication.instance().applicationName())
        self.activated.connect(self.__activated)

        menu = QMenu(parent)
        menu.setDefaultAction(menu.addAction('Open GUI', parent.showNormal))
        self.restart_act = menu.addAction('Restart script', QApplication.instance().restart)
        menu.addAction('Quit', QApplication.instance().exit)
        self.setContextMenu(menu)

    def __activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.parent().isVisible():
                self.parent().close()
            else:
                self.parent().show_from_tray()

        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.restart_act.trigger()


class MainWindow(QMainWindow):
    dock_names: set[str] = set()
    dock_widgets: list[QDockWidget] = []

    def __init__(self, widgets_to_add: list[QWidget]):
        super().__init__()
        self.__normal_flags = self.windowFlags()
        self.__always_on_top_flags = self.__normal_flags | Qt.WindowStaysOnTopHint

        app_name = QApplication.instance().organizationName()
        script_name = QApplication.instance().applicationName()
        self.setWindowTitle(f'{app_name} - {script_name}')

        self.setDockNestingEnabled(True)

        self.add_widget_as_dock(midiscripter.gui.ports_widget.PortsWidget())
        self.add_widget_as_dock(midiscripter.gui.log_widget.LogWidget())

        for widget in widgets_to_add:
            self.add_widget_as_dock(widget)

        self.menu_bar = midiscripter.gui.menu_bar.MenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.tray = TrayIcon(self.windowIcon(), self)
        self.tray.show()

    def add_widget_as_dock(self, widget: QWidget):
        dock = QDockWidget(self)
        dock.setObjectName(widget.objectName())
        dock.setWindowTitle(widget.objectName())
        dock.setWidget(widget)

        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)
        self.dock_widgets.append(dock)

    def set_dock_titles_visibility(self, are_hidden: bool):
        # Can't make full lock with setFixedSize due to AdaptiveTextSizeWidgets
        # that has "Ignore" size policy and always restore at maximum size after that
        for dock in self.dock_widgets:
            if are_hidden:
                dock.setTitleBarWidget(QWidget())
            else:
                dock.setTitleBarWidget(None)

    def show_from_tray(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.resize(QSettings().value('win size', QSize(800, 500)))
        self.move(QSettings().value('win position', self.__get_screen_center()))
        self.restoreState(QSettings().value('win state'))

        if QSettings().value('restart win minimized', False):
            self.showMinimized()
            # 'win minimized' set by restart request, cleared for the next normal start
            QSettings().setValue('restart win minimized', 0)
        elif QSettings().value('win maximized', False):
            self.showMaximized()
        else:
            self.show()

        # Somewhere in window preparation the window size changes, second resize makes it stick.
        self.resize(QSettings().value('win size', QSize(800, 500)))
        self.move(QSettings().value('win position', self.__get_screen_center()))

        # 'win visible' set by restart request, cleared for the next normal start
        if QSettings().value('restart closed to tray', False):
            QSettings().setValue('restart closed to tray', 0)
            self.close()

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        QSettings().setValue('win state', self.saveState())
        QSettings().setValue('win maximized', int(self.isMaximized()))

        if not self.isMaximized():
            QSettings().setValue('win size', self.size())
            QSettings().setValue('win position', self.pos())

        self.hide()

    def set_always_on_top(self, state: bool):
        if state:
            self.setWindowFlags(self.__always_on_top_flags)
        else:
            self.setWindowFlags(self.__normal_flags)
        self.show()

    def __get_screen_center(self) -> QPoint:
        return (
            self.screen().geometry().center()
            - QRect(QPoint(), self.frameGeometry().size()).center()
        )
