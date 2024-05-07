import pathlib
import platform
import signal
import sys
import time
from typing import NoReturn

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.base.port_base
import midiscripter.base.shared
import midiscripter.file_event.file_event_msg
import midiscripter.gui.main_window
import midiscripter.midi.midi_ports_update


class ScripterGUI(QApplication):
    request_restart = Signal()

    RESTART_DELAY = 2
    widgets_to_add = []

    def __init__(self):
        super().__init__()
        self.setOrganizationName('MIDI Scripter')
        if midiscripter.base.shared.script_path:
            self.setApplicationName(pathlib.Path(midiscripter.base.shared.script_path).name)

        icon_path = pathlib.Path(midiscripter.__file__).parent / 'resources' / 'icon.ico'
        self.setWindowIcon(QIcon(str(icon_path)))

        self.__time_until_restart_sec = self.RESTART_DELAY
        self.request_restart.connect(self, self.restart)
        self.aboutToQuit.connect(self.__cleanup)

    def prepare_main_window(self, minimized_to_tray: bool = False) -> None:
        self.main_window = midiscripter.gui.main_window.MainWindow(self.widgets_to_add)

        if not minimized_to_tray:
            self.main_window.show_from_tray()
        else:
            self.main_window.close()

    def restart_at_file_change(
        self, msg: 'midiscripter.file_event.file_change_msg.FileEventMsg'
    ) -> None:
        if msg.type not in (
            midiscripter.file_event.file_event_msg.FileEventType.CREATED,
            midiscripter.file_event.file_event_msg.FileEventType.MODIFIED,
        ):
            return

        self.__time_until_restart_sec = self.RESTART_DELAY
        sleep_step_sec = 0.1

        while self.__time_until_restart_sec > 0:
            time.sleep(sleep_step_sec)
            self.__time_until_restart_sec -= sleep_step_sec

        self.request_restart.emit()

    def restart(self) -> NoReturn:
        if pathlib.Path(midiscripter.base.shared.script_path).is_file():
            # These settings saved only for restart
            self.processEvents()  # update win status to get correct status
            QSettings().setValue('restart win minimized', self.main_window.isMinimized())
            QSettings().setValue('restart closed to tray', not self.main_window.isVisible())
            self.exit(1467)

    def __cleanup(self) -> None:
        self.main_window.close()
        self.main_window.tray.hide()


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
    if not midiscripter.base.shared.script_path:
        raise RuntimeError('Starter can only be called from a script')

    """Starts the script and runs GUI. Logging goes to GUI Log widget."""
    midiscripter.base.shared._raise_current_process_cpu_priority()

    sigint_exit_code = {'Windows': -1073741510, 'Linux': 130, 'Darwin': 2}[platform.system()]
    signal.signal(signal.SIGINT, lambda *_: app_instance.exit(sigint_exit_code))

    signal_checker_dummy_timer = QTimer()  # runs python code from Qt to allow the signal to trigger
    signal_checker_dummy_timer.start(1000)
    signal_checker_dummy_timer.timeout.connect(lambda: None)  # dummy python code to run

    start_minimized_to_tray = '--tray' in sys.argv

    with midiscripter.base.port_base._all_opened():
        app_instance.prepare_main_window(start_minimized_to_tray)
        exit_status = app_instance.exec()

    if exit_status == 1467:  # exit status for restart request
        midiscripter.base.shared.restart_script()
    else:
        exit(exit_status)
