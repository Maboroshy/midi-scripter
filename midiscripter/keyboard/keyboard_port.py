import pynput.keyboard
from typing import TYPE_CHECKING, overload, ClassVar

import midiscripter.base.port_base
from midiscripter.keyboard.keyboard_msg import KeyEvent, KeyMsg
from midiscripter.logger import log

if TYPE_CHECKING:
    from collections.abc import Container, Callable


class KeyIn(midiscripter.base.port_base.Input):
    """Keyboard input port. Produces [`KeyMsg`][midiscripter.KeyMsg] objects."""

    __supress_input: bool
    """Prevent the input events from being passed to the rest of the system
    
    Warning: 
        Enable with caution! 
        You'll loose the keyboard input unless you're proxying it to [KeyOut][midiscripter.KeyOut]
    """

    pressed_keys: list[pynput.keyboard.Key]
    """Currently pressed keys"""

    _force_uid: ClassVar[str] = 'Keyboard In'

    def __init__(self, *, supress_input: bool = False):
        """
        Args:
            supress_input: Prevent the input events from being passed to the rest of the system
        """
        super().__init__(
            self._force_uid,
        )
        self.__pynput_listener = None
        self.__supress_input = supress_input
        self.pressed_keys = []

    def __on_press(self, key: pynput.keyboard.Key) -> None:
        if not self.is_enabled:
            return

        if type(key) is pynput.keyboard.KeyCode:
            key = self.__pynput_listener.canonical(key)

        if key not in self.pressed_keys:
            self.pressed_keys.append(key)

        msg = KeyMsg(KeyEvent.PRESS, self.pressed_keys.copy(), source=self)
        self._send_input_msg_to_calls(msg)

    def __on_release(self, key: pynput.keyboard.Key) -> None:
        if not self.is_enabled:
            return

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
        if self.__pynput_listener:
            self.is_enabled = True
            return

        self.__pynput_listener = pynput.keyboard.Listener(
            self.__on_press, self.__on_release, suppress=self.__supress_input
        )
        self.__pynput_listener.start()
        self.__pynput_listener.wait()
        self.is_enabled = True
        log('Started keyboard input listener')
        self._call_on_port_open()

    def _close(self) -> None:
        self.__pynput_listener.stop()
        self.is_enabled = False
        log('Stopped keyboard input listener')

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

    _force_uid: ClassVar[str] = 'Keyboard Output'

    def __init__(self):
        """"""
        super().__init__(self._force_uid)
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
        self._log_msg_sent(msg)

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
        self.__pynput_controller.type(string_to_type)
