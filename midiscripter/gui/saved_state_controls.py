from typing import TYPE_CHECKING

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

if TYPE_CHECKING:
    from collections.abc import Callable


class SavedCheckedStateMixin:
    def __init__(
        self,
        name: str,
        func_for_state: 'Callable | None' = None,
        *,
        checked_func: 'Callable | None' = None,
        unchecked_func: 'Callable | None' = None,
        default_state: bool = False,
        key_shortcut: 'QKeySequence | None' = None,
        shared: bool = False,
    ):
        super().__init__(name)
        self.__func_for_state = func_for_state
        self.__checked_func = checked_func
        self.__unchecked_func = unchecked_func
        self.__default_state = default_state
        self.__setting_name = f'{name} state'

        if key_shortcut:
            self.setShortcut(key_shortcut)

        if shared:
            self.__qsettings_args = (QApplication.instance().organizationName(), 'Shared')
        else:
            self.__qsettings_args = (None,)

        self.setCheckable(True)
        # replaces force _state_changed that causes widgets toggled by action to pop up
        self.setChecked(default_state)
        self.toggled.connect(self.__state_changed)
        self.setChecked(bool(self))

    def __bool__(self):
        return QSettings(*self.__qsettings_args).value(
            self.__setting_name, self.__default_state, type=bool
        )

    def __state_changed(self, state: bool) -> None:
        QSettings(*self.__qsettings_args).setValue(self.__setting_name, state)

        if self.__func_for_state:
            self.__func_for_state(state)

        if state is True and self.__checked_func:
            self.__checked_func()
        if state is False and self.__unchecked_func:
            self.__unchecked_func()


class SavedCheckedAction(SavedCheckedStateMixin, QAction):
    pass


class SavedToggleButton(SavedCheckedStateMixin, QPushButton):
    pass
