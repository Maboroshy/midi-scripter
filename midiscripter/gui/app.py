import pathlib
import platform
import signal
import socket
import sys
import time
from typing import NoReturn

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.base.port_base
import midiscripter.file_event
import midiscripter.gui.main_window
from .color_theme import enable_dark_mode
from .saved_state_controls import SavedCheckedAction


class ScripterGUI(QApplication):
    main_window: 'midiscripter.gui.main_window.MainWindow'
    request_restart = Signal()

    RESTART_DELAY = 2
    widgets_to_add = []

    def __init__(self):
        super().__init__()
        self.setOrganizationName('MIDI Scripter')
        if midiscripter.shared.SCRIPT_PATH_STR:
            self.setApplicationName(pathlib.Path(midiscripter.shared.SCRIPT_PATH_STR).name)

        self.setApplicationDisplayName(f'{self.applicationName()} - {self.organizationName()}')

        icon_path = pathlib.Path(midiscripter.__file__).parent / 'resources' / 'icon.ico'
        self.setWindowIcon(QIcon(str(icon_path)))

        self.set_theme()

        self.__time_until_restart_sec = self.RESTART_DELAY
        self.request_restart.connect(self.restart)
        self.aboutToQuit.connect(self.__cleanup)

        # Action to use before main window creation
        self.single_instance_only = SavedCheckedAction('Single instance only', shared=True)
        self.__single_instance_socket = socket.socket()
        if self.single_instance_only:
            self.__terminate_if_second_instance()

    def set_theme(self) -> None:
        # self.styleHints().setColorScheme(Qt.ColorScheme.Dark)

        self.setStyle('Fusion')
        dark_mode_enabled = self.styleHints().colorScheme() == Qt.ColorScheme.Dark
        enable_dark_mode(dark_mode_enabled)

        if dark_mode_enabled:
            self.setStyleSheet('QPushButton:checked { border: 1px solid grey; }')

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, palette.color(QPalette.ColorRole.Base))
        self.setPalette(palette)

    def prepare_main_window(self, minimized_to_tray: bool = False) -> None:
        self.main_window = midiscripter.gui.main_window.MainWindow(self.widgets_to_add)

        if minimized_to_tray or QSettings().value('restart closed to tray', False, type=bool):
            QSettings().setValue('restart closed to tray', False)
            self.main_window.close()
        elif QSettings().value('restart win minimized', False, type=bool):
            self.main_window.showMinimized()
            # 'win minimized' set by restart request, cleared for the next normal start
            QSettings().setValue('restart win minimized', False)
        else:
            self.main_window.show_from_tray()

    def restart_at_file_change(self, msg: midiscripter.file_event.FileEventMsg) -> None:
        if msg.type not in (
            midiscripter.file_event.FileEvent.CREATED,
            midiscripter.file_event.FileEvent.MODIFIED,
        ):
            return

        self.__time_until_restart_sec = self.RESTART_DELAY
        sleep_step_sec = 0.1

        while self.__time_until_restart_sec > 0:
            time.sleep(sleep_step_sec)
            self.__time_until_restart_sec -= sleep_step_sec

        self.request_restart.emit()

    def restart(self) -> None:
        if pathlib.Path(midiscripter.shared.SCRIPT_PATH_STR).is_file():
            # These settings saved only for restart
            self.processEvents()  # update win status to get correct status
            QSettings().setValue('restart win minimized', self.main_window.isMinimized())
            QSettings().setValue('restart closed to tray', not self.main_window.isVisible())
            self.exit(1467)

    def __terminate_if_second_instance(self) -> None:
        try:
            self.__single_instance_socket.bind(('127.0.0.1', 1337))
        except OSError:
            print(
                f'"{self.single_instance_only.text()}" option is enabled.\n'
                "Second instance won't be started."
            )
            sys.exit(1)

    def __cleanup(self) -> None:
        self.main_window.close()
        self.main_window.tray.hide()

        self.__single_instance_socket.close()


# Creating app at import to allow QWidget instance init in other modules
app_instance = ScripterGUI()


def add_qwidget(qwidget: QWidget) -> None:
    """Add custom pyside6 QWidget to the GUI"""
    if qwidget not in midiscripter.gui.app.ScripterGUI.widgets_to_add:
        midiscripter.gui.app.ScripterGUI.widgets_to_add.append(qwidget)


def remove_qwidget(qwidget: QWidget) -> None:
    """Remove custom pyside6 QWidget to the GUI"""
    try:
        midiscripter.gui.app.ScripterGUI.widgets_to_add.remove(qwidget)
    except ValueError:
        pass


def start_gui() -> NoReturn:
    """Starts the script and runs GUI. Logging goes to GUI Log widget"""
    if not midiscripter.shared.SCRIPT_PATH_STR:
        raise RuntimeError('Starter can only be called from a script')

    midiscripter.shared.raise_current_process_cpu_priority()

    sigint_exit_code = {'Windows': -1073741510, 'Linux': 130, 'Darwin': 130}[platform.system()]
    signal.signal(signal.SIGINT, lambda *_: app_instance.exit(sigint_exit_code))
    sigterm_exit_code = {'Windows': 3, 'Linux': 143, 'Darwin': 143}[platform.system()]
    signal.signal(signal.SIGTERM, lambda *_: app_instance.exit(sigterm_exit_code))

    signal_checker_dummy_timer = QTimer()  # runs python code from Qt to allow the signal to trigger
    signal_checker_dummy_timer.start(1000)
    signal_checker_dummy_timer.timeout.connect(lambda: None)  # dummy python code to run

    start_minimized_to_tray = '--tray' in sys.argv

    with midiscripter.base.port_base._all_opened():
        app_instance.prepare_main_window(start_minimized_to_tray)
        exit_status = app_instance.exec()

    if exit_status == 1467:  # restart request, can't do sys.exit() while Qt app works
        midiscripter.shared.restart_script()
    else:
        sys.exit(exit_status)
