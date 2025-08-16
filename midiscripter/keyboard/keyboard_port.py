from typing import TYPE_CHECKING, overload, ClassVar
import pynput.keyboard

import midiscripter.base.port_base
from midiscripter.logger import log
from midiscripter.keyboard.keyboard_msg import KeyEvent, KeyMsg

if TYPE_CHECKING:
    from collections.abc import Container, Callable


class KeyIn(midiscripter.base.port_base.Input):
    """Keyboard input port. Produces [`KeyMsg`][midiscripter.KeyMsg] objects."""

    __supress_input: bool
    """Prevent the input events from being passed to the rest of the system"""

    pressed_keys: list[pynput.keyboard.Key]
    """Currently pressed keys"""

    _forced_uid: ClassVar[str] = 'Keyboard In'
    _log_description: str = 'keyboard input listener'

    def __init__(self, *, supress_input: bool = False):
        """
        Args:
            supress_input: Prevent the input events from being passed to the rest of the system

        Warning:
            Use `supress_input` with caution!
            You'll lose the keyboard input unless you're proxying it to an output port.
        """
        super().__init__()
        self.__pynput_listener = None
        self.__supress_input = supress_input
        self.pressed_keys = []

        self.pressed_keys: list[pynput.keyboard.Key]  # workaround for mkdocstrings issue #607
        """Currently pressed keys"""

    def __on_press(self, key: pynput.keyboard.Key) -> None:
        if type(key) is pynput.keyboard.KeyCode:
            key = self.__pynput_listener.canonical(key)

        if key not in self.pressed_keys:
            self.pressed_keys.append(key)

        msg = KeyMsg(KeyEvent.PRESS, self.pressed_keys.copy(), source=self)
        self._send_input_msg_to_calls(msg)

    def __on_release(self, key: pynput.keyboard.Key) -> None:
        if type(key) is pynput.keyboard.KeyCode:
            key = self.__pynput_listener.canonical(key)

        try:
            pressed_keys_for_msg = self.pressed_keys.copy()
            self.pressed_keys.remove(key)

            msg = KeyMsg(KeyEvent.RELEASE, pressed_keys_for_msg, source=self)
            self._send_input_msg_to_calls(msg)
        except ValueError:
            pass

    def _open(self) -> None:
        self.__pynput_listener = pynput.keyboard.Listener(
            self.__on_press, self.__on_release, suppress=self.__supress_input
        )
        self.__pynput_listener.start()
        self.__pynput_listener.wait()
        self.is_opened = True
        log._port_open(self, True)

    def _close(self) -> None:
        self.__pynput_listener.stop()
        self.__pynput_listener = None
        self.is_opened = False
        log._port_close(self, True)

    @overload
    def subscribe(self, call: 'Callable[[KeyMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container[KeyEvent] | KeyEvent' = None,
        shortcut: 'None | Container[str] | str' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container[KeyEvent] | KeyEvent' = None,
        shortcut: 'None | Container[str] | str' = None,
    ) -> 'Callable':
        return super().subscribe(type, shortcut)


class KeyOut(midiscripter.base.port_base.Output):
    """Keyboard output port. Sends [`KeyMsg`][midiscripter.KeyMsg] objects."""

    _forced_uid: ClassVar[str] = 'Keyboard Out'
    _log_description: str = 'keyboard output'

    def __init__(self):
        """"""
        super().__init__()
        self.__pynput_controller = pynput.keyboard.Controller()

    def send(self, msg: KeyMsg) -> None:
        """Send the keyboard input.

        Args:
            msg: object to send
        """
        if not self._validate_msg_send(msg):
            return

        # Log messages sent before actual sending, so receive messages for sent keys
        # won't be displayed before the message
        log._msg_sent(self, msg)

        if msg.type is KeyEvent.PRESS:
            for keycode in msg.keycodes:
                self.__pynput_controller.press(keycode)

        elif msg.type is KeyEvent.RELEASE:
            for keycode in msg.keycodes:
                self.__pynput_controller.release(keycode)

        elif msg.type is KeyEvent.TAP:
            for keycode in msg.keycodes:
                self.__pynput_controller.press(keycode)
            for keycode in reversed(msg.keycodes):
                self.__pynput_controller.release(keycode)

    def type_in(self, string_to_type: str) -> None:
        """Type in the text as a keyboard"""
        self.__pynput_controller.type(string_to_type)


class KeyIO(midiscripter.base.port_base.MultiPort):
    """Keyboard input/output port that combines [`KeyIn`][midiscripter.KeyIn] and
    [`KeyOut`][midiscripter.KeyOut] ports.
    Produces and sends [`KeyMsg`][midiscripter.KeyMsg] objects.
    """

    _forced_uid: ClassVar[str] = 'Keyboard'
    _log_description: str = 'keyboard i/o'

    def __init__(self, *, supress_input: bool = False):
        """
        Args:
            supress_input: Prevent the input events from being passed to the rest of the system

        Warning:
            Use `supress_input` with caution!
            You'll lose the keyboard input unless you're proxying it to an output port.
        """
        if supress_input:
            super().__init__('Keyboard', KeyIn(supress_input=supress_input), KeyOut())
        else:
            super().__init__('Keyboard', KeyIn(), KeyOut())  # For better MIDI port repr in log

    @property
    def pressed_keys(self) -> list[pynput.keyboard.Key]:
        """Currently pressed keys"""
        return self._input_ports[0].pressed_keys

    @overload
    def subscribe(self, call: 'Callable[[KeyMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container[KeyEvent] | KeyEvent' = None,
        shortcut: 'None | Container[str] | str' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container[KeyEvent] | KeyEvent' = None,
        shortcut: 'None | Container[str] | str' = None,
    ) -> 'Callable':
        return self._input_ports[0].subscribe(type, shortcut)

    def send(self, msg: KeyMsg) -> None:
        """Send the keyboard input.

        Args:
            msg: object to send
        """
        self._output_ports[0].send(msg)

    def type_in(self, string_to_type: str) -> None:
        """Type in the text as a keyboard"""
        self._output_ports[0].type(string_to_type)
