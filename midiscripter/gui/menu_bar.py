import pathlib
import platform

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.shared
import midiscripter.file_event
import midiscripter.gui.main_window
from .saved_state_controls import SavedCheckedAction


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
        script_menu.addAction('Run another', self.__run_another_script)
        script_menu.addAction('&Restart', QApplication.instance().restart, QKeySequence('Ctrl+R'))
        script_menu.addAction('&Quit', QApplication.instance().exit, QKeySequence('Ctrl+Q'))

        # Options
        options_menu = self.addMenu('Options')

        self.autostart = midiscripter.shared.AutostartManager()
        toggle_autostart = options_menu.addAction('Run at start up')
        toggle_autostart.setCheckable(True)
        toggle_autostart.setChecked(self.autostart._check_if_enabled())
        toggle_autostart.toggled.connect(self.__set_autostart)

        options_menu.insertAction(QAction(), QApplication.instance().single_instance_only)

        options_menu.addSeparator()

        self.always_on_top = SavedCheckedAction(
            'Window always on top',
            main_window.set_always_on_top,
            key_shortcut=QKeySequence('Ctrl+Space'),
        )
        options_menu.insertAction(QAction(), self.always_on_top)

        options_menu.addSeparator()

        self.watch_script_file = SavedCheckedAction(
            'Restart on script file change', self.__set_watching_script_file
        )
        self.watch_script_file.triggered.connect(main_window.ports_widget.repopulate)
        options_menu.insertAction(QAction(), self.watch_script_file)

        # Dock widgets
        widgets_menu = self.addMenu('Widgets')

        self.lock_dock_widgets = SavedCheckedAction(
            'Hide widgets &titles',
            main_window.set_dock_titles_visibility,
            key_shortcut=QKeySequence('Ctrl+T'),
        )
        widgets_menu.insertAction(QAction(), self.lock_dock_widgets)
        main_window.set_dock_titles_visibility(bool(self.lock_dock_widgets))

        widgets_menu.addSeparator()

        widgets_menu.aboutToShow.connect(
            lambda: widgets_menu.addActions(main_window.createPopupMenu().actions())
        )

        # Help
        help_menu = self.addMenu('Help')

        if platform.system() in ('Windows', 'Darwin'):
            help_menu.addAction(
                'Install Ableton remote script', self.__install_ableton_remote_script
            )
            help_menu.addSeparator()

        help_menu.addAction(
            'Homepage',
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/Maboroshy/midi-scripter')),
        )
        help_menu.addAction(
            'Documentation',
            lambda: QDesktopServices.openUrl(QUrl('https://maboroshy.github.io/midi-scripter')),
        )

    def __run_another_script(self) -> None:
        file_path_str = QFileDialog.getOpenFileName(
            self,
            'Select python script',
            str(pathlib.Path(midiscripter.shared.SCRIPT_PATH_STR).parent),
            'Python script (*.py)',
        )[0]
        if file_path_str:
            midiscripter.shared.SCRIPT_PATH_STR = file_path_str
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

    def __set_watching_script_file(self, state: bool) -> None:
        if state:
            self.file_watcher_port = midiscripter.file_event.FileEventIn(
                midiscripter.shared.SCRIPT_PATH_STR
            )
            self.file_watcher_port.subscribe(QApplication.instance().restart_at_file_change)
            self.file_watcher_port._open()
        else:
            self.file_watcher_port._close()

    def __install_ableton_remote_script(self) -> None:
        script_installed = midiscripter.shared.install_ableton_remote_script()

        target_path = midiscripter.shared.get_ableton_remote_script_path()
        script_exists = pathlib.Path(target_path / 'UserConfiguration.txt').is_file()

        if script_installed:
            QMessageBox.information(
                self,
                '',
                f'Ableton Live remote script {"re" if script_exists else ""}installed to: \n'
                f'{str(target_path)}.\n\n'
                f'Restart Ableton Live.',
            )
        else:
            QMessageBox.warning(
                self,
                '',
                "Can't install Ableton Live remote script.\n"
                'User remote scripts directory is unreachable',
            )
