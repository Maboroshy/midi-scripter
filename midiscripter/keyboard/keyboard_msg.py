from typing import TYPE_CHECKING
from collections.abc import Iterable

import pynput.keyboard

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container
    from midiscripter.keyboard.keyboard_port import KeyIn


MODIFIER_KEYS = {
    pynput.keyboard.Key.alt,
    pynput.keyboard.Key.cmd,
    pynput.keyboard.Key.ctrl,
    pynput.keyboard.Key.shift,
}


MODIFIER_KEYS_VARIATIONS = {
    pynput.keyboard.Key.alt_gr: pynput.keyboard.Key.alt,
    pynput.keyboard.Key.alt_l: pynput.keyboard.Key.alt,
    pynput.keyboard.Key.cmd_l: pynput.keyboard.Key.cmd,
    pynput.keyboard.Key.cmd_r: pynput.keyboard.Key.cmd,
    pynput.keyboard.Key.ctrl_l: pynput.keyboard.Key.ctrl,
    pynput.keyboard.Key.ctrl_r: pynput.keyboard.Key.ctrl,
    pynput.keyboard.Key.shift_l: pynput.keyboard.Key.shift,
    pynput.keyboard.Key.shift_r: pynput.keyboard.Key.shift,
}


class KeyEventType(midiscripter.base.msg_base.AttrEnum):
    KEY_PRESS = 'KEY_PRESS'
    KEY_RELEASE = 'KEY_RELEASE'
    KEY_TAP = 'KEY_TAP'
    """Key press and release. Isn't assigned by [`KeyIn`][midiscripter.KeyIn]. 
       Use it for message declarations in calls."""


class KeyMsg(midiscripter.base.msg_base.Msg):
    """Keyboard event message"""

    __match_args__ = ('type', 'shortcut')

    type: KeyEventType
    """Keyboard event type"""

    keycodes: list[pynput.keyboard.Key]
    """Keycodes in the order they were pressed. Use when press order matters."""

    source: 'None | KeyIn'

    def __init__(
        self,
        type: KeyEventType,
        shortcut_or_keycodes: str | Iterable[pynput.keyboard.Key],
        *,
        source: 'None | KeyIn' = None,
    ):
        """
        Args:
            type: Keyboard event type
            shortcut_or_keycodes: keyboard shortcut description or event key codes
            source (KeyIn): The [`KeyIn`][midiscripter.KeyIn] instance that generated the message

        Tip:
            Run GUI and Enable keyboard input. Use log to get messages with shortcuts you need.
        """
        super().__init__(type, source)
        self.__shortcut_cache = ''
        self.__cached_keycodes = None

        if isinstance(shortcut_or_keycodes, str):
            self.shortcut = shortcut_or_keycodes.lower()
        elif isinstance(shortcut_or_keycodes, Iterable):
            self.keycodes = list(shortcut_or_keycodes)
        else:
            raise TypeError

    @property
    def shortcut(self) -> str:
        """Keyboard shortcut description like `'ctrl+shift+t'`.
        Stays the same for any key press order."""
        if self.__cached_keycodes != self.keycodes:
            modifiers = []
            non_mod_keys = []
            for keycode in self.keycodes:
                keycode = MODIFIER_KEYS_VARIATIONS.get(keycode, keycode)
                if keycode in MODIFIER_KEYS:
                    modifiers.append(str(keycode))
                else:
                    non_mod_keys.append(str(keycode))

            modifiers.sort()
            non_mod_keys.sort()
            key_strings = modifiers + non_mod_keys

            keys_descr = (key_str.rpartition('.')[-1].replace("'", '') for key_str in key_strings)
            shortcut = '+'.join(keys_descr)

            self.__cached_keycodes = self.keycodes
            self.__shortcut_cache = shortcut

        return self.__shortcut_cache

    @shortcut.setter
    def shortcut(self, shortcut: str) -> None:
        self.keycodes = []
        for key in shortcut.split('+'):
            if len(key) == 1:
                key = pynput.keyboard.KeyCode.from_char(key)
            else:
                key = getattr(pynput.keyboard.Key, key)
            self.keycodes.append(key)

    def matches(
        self,
        type: 'None | Container[KeyEventType] | KeyEventType' = None,
        shortcut: 'None | Container[str] | str' = None,
    ) -> bool:
        return super().matches(type, shortcut)
