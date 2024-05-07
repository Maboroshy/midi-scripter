import pathlib
from typing import TYPE_CHECKING

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.base.shared
import midiscripter.file_event
import midiscripter.gui.main_window
import midiscripter.midi.midi_ports_update

if TYPE_CHECKING:
    from collections.abc import Callable
    from base.msg_base import Msg


class SavedCheckedStateAction(QAction):
    def __init__(
        self,
        name: str,
        func_for_state: 'Callable | None' = None,
        *,
        checked_func: 'Callable | None' = None,
        unchecked_func: 'Callable | None' = None,
        default_state: bool = False,
        key_shortcut: 'QKeySequence | None' = None,
    ):
        super().__init__(name)
        self.__func_for_state = func_for_state
        self.__checked_func = checked_func
        self.__unchecked_func = unchecked_func
        self.__default_state = default_state
        self.__setting_name = f'action {name}'

        if key_shortcut:
            self.setShortcut(key_shortcut)

        self.setCheckable(True)
        # replaces force _state_changed that causes widgets toggled by action to pop up
        self.setChecked(default_state)
        self.toggled.connect(self.__state_changed)
        self.setChecked(bool(self))

    def __bool__(self):
        return bool(QSettings().value(self.__setting_name, self.__default_state, type=bool))

    def __state_changed(self, state: bool) -> None:
        QSettings().setValue(self.__setting_name, state)

        if self.__func_for_state:
            self.__func_for_state(state)

        if state is True and self.__checked_func:
            self.__checked_func()
        if state is False and self.__unchecked_func:
            self.__unchecked_func()


class MenuBar(QMenuBar):
    autostart_path = (
        pathlib.Path.home() / 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup'
    )
    autostart_shortcut_prefix = 'MIDI Scripter - '

    def __init__(self, main_window: 'midiscripter.gui.main_window.MainWindow'):
        super().__init__(main_window)
        self.setObjectName('Menu Bar')

        # Script
        script_menu = self.addMenu('Script')
        script_menu.addAction('Run another', self._run_another_script)
        script_menu.addAction('&Restart', QApplication.instance().restart, QKeySequence('Ctrl+R'))
        script_menu.addAction('&Quit', QApplication.instance().exit, QKeySequence('Ctrl+Q'))

        # Options
        options_menu = self.addMenu('Options')

        self.autostart = midiscripter.base.shared.AutostartManager()
        toggle_autostart = options_menu.addAction('Run at start up')
        toggle_autostart.setCheckable(True)
        toggle_autostart.setChecked(self.autostart._check_if_enabled())
        toggle_autostart.toggled.connect(self.__set_autostart)

        self.always_on_top = SavedCheckedStateAction(
            'Window always on top',
            main_window.set_always_on_top,
            key_shortcut=QKeySequence('Ctrl+Space'),
        )
        options_menu.insertAction(QAction(), self.always_on_top)

        options_menu.addSeparator()

        self.watch_script_file = SavedCheckedStateAction(
            'Restart on script file change', self.__set_watching_script_file
        )
        options_menu.insertAction(QAction(), self.watch_script_file)

        self.watch_midi_ports = SavedCheckedStateAction(
            'Restart on MIDI port changes', self.__set_watching_midi_ports
        )
        options_menu.insertAction(QAction(), self.watch_midi_ports)

        # Dock widgets
        widgets_menu = self.addMenu('Widgets')

        self.lock_dock_widgets = SavedCheckedStateAction(
            'Hide widgets titles',
            main_window.set_dock_titles_visibility,
            key_shortcut=QKeySequence('Ctrl+T'),
        )
        widgets_menu.insertAction(QAction(), self.lock_dock_widgets)
        widgets_menu.addSeparator()
        widgets_menu.aboutToShow.connect(
            lambda: widgets_menu.addActions(main_window.createPopupMenu().actions())
        )

        # Help
        script_menu = self.addMenu('Help')
        script_menu.addAction(
            'Homepage',
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/Maboroshy/midi-scripter')),
        )
        script_menu.addAction(
            'Documentation',
            lambda: QDesktopServices.openUrl(QUrl('https://maboroshy.github.io/midi-scripter')),
        )

    def _run_another_script(self) -> None:
        file_path_str = QFileDialog.getOpenFileName(
            self,
            'Select python script',
            str(pathlib.Path(midiscripter.base.shared.script_path).parent),
            'Python script (*.py)',
        )[0]
        if file_path_str:
            midiscripter.base.shared.script_path = file_path_str
            QApplication.instance().restart()

    @Slot(bool)
    def __set_autostart(self, state: bool) -> None:
        if self.autostart._check_if_other_scripts_present():
            remove_other_dialog = QMessageBox()
            remove_other_dialog.setText(
                'There are other scripts with enabled autostart. Disable them?'
            )
            remove_other_dialog.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            remove_other_dialog_pressed_button = remove_other_dialog.exec()

            if remove_other_dialog_pressed_button == QMessageBox.Cancel:
                return
            elif remove_other_dialog_pressed_button == QMessageBox.Yes:
                self.autostart._disable_others()

        if state:
            self.autostart._enable()
        else:
            self.autostart._disable()

    def __set_watching_script_file(self, new_status: bool) -> None:
        if new_status:
            self.file_watcher_port = midiscripter.file_event.FileEventIn(
                midiscripter.base.shared.script_path
            )
            self.file_watcher_port.subscribe(QApplication.instance().restart_at_file_change)
            self.file_watcher_port._open()
        else:
            self.file_watcher_port.is_enabled = False

    def __set_watching_midi_ports(self, new_status: bool) -> None:
        if new_status:
            self.midi_port_watcher_port = midiscripter.midi.midi_ports_update.MidiPortsChangedIn()

            @self.midi_port_watcher_port.subscribe
            def restart_on_midi_port_change(_: 'Msg') -> None:
                QApplication.instance().request_restart.emit()

            self.midi_port_watcher_port._open()
        else:
            self.midi_port_watcher_port.is_enabled = False
