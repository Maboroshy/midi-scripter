import pynput.mouse
from typing import TYPE_CHECKING, overload, ClassVar

import midiscripter.base.port_base
from midiscripter.mouse.mouse_msg import MouseEvent, MouseMsg
from midiscripter.logger import log

if TYPE_CHECKING:
    from collections.abc import Container, Callable


pynput_buttons_to_msg_type_map = {
    pynput.mouse.Button.left: (MouseEvent.LEFT_RELEASE, MouseEvent.LEFT_PRESS),
    pynput.mouse.Button.middle: (MouseEvent.MIDDLE_RELEASE, MouseEvent.MIDDLE_PRESS),
    pynput.mouse.Button.right: (MouseEvent.RIGHT_RELEASE, MouseEvent.RIGHT_PRESS),
}


scroll_event_to_args_map = {
    MouseEvent.SCROLL_UP: (0, -1),
    MouseEvent.SCROLL_DOWN: (0, 1),
    MouseEvent.SCROLL_LEFT: (-1, 0),
    MouseEvent.SCROLL_RIGHT: (1, 0),
}


class MouseIn(midiscripter.base.port_base.Input):
    """Mouse input port. Produces [`MouseMsg`][midiscripter.MouseMsg] objects.

    Warning:
        Transparent `MouseIn` -> `MouseOut` proxy won't work, since it will react to its own output.

        Use `MouseOut` only for one-time movements.
    """

    _force_uid: ClassVar[str] = 'Mouse In'

    def __init__(self):
        """"""
        super().__init__(self._force_uid)
        self.__pynput_listener = None

    def __on_move(self, x: int, y: int) -> None:
        if not self.is_enabled:
            return

        self._send_input_msg_to_calls(MouseMsg(MouseEvent.MOVE, x, y, source=self))

    def __on_click(self, x: int, y: int, button: pynput.mouse.Button, pressed: bool) -> None:
        if not self.is_enabled:
            return

        try:
            msg_type = pynput_buttons_to_msg_type_map[button][pressed]
        except KeyError:
            msg_type = f'{button.name.upper()}_{("RELEASE", "PRESS")[pressed]}'

        self._send_input_msg_to_calls(MouseMsg(msg_type, x, y, source=self))

    def __on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self.is_enabled:
            return

        if dy == -1:
            self._send_input_msg_to_calls(MouseMsg(MouseEvent.SCROLL_UP, x, y, source=self))
        elif dy == 1:
            self._send_input_msg_to_calls(MouseMsg(MouseEvent.SCROLL_DOWN, x, y, source=self))

        if dx == -1:
            self._send_input_msg_to_calls(MouseMsg(MouseEvent.SCROLL_LEFT, x, y, source=self))
        elif dx == 1:
            self._send_input_msg_to_calls(MouseMsg(MouseEvent.SCROLL_RIGHT, x, y, source=self))

    def _open(self) -> None:
        if self.__pynput_listener:
            self.is_enabled = True
            return

        self.__pynput_listener = pynput.mouse.Listener(
            self.__on_move, self.__on_click, self.__on_scroll
        )
        self.__pynput_listener.start()
        self.__pynput_listener.wait()
        self.is_enabled = True
        log('Started mouse input listener')
        self._call_on_port_open()

    def _close(self) -> None:
        self.__pynput_listener.stop()
        self.is_enabled = False
        log('Stopped mouse input listener')

    @overload
    def subscribe(self, call: 'Callable[[MouseMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        type: 'None | Container[MouseEvent] | MouseEvent' = None,
        x: 'None | Container[int] | int' = None,
        y: 'None | Container[int] | int' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        type: 'None | Container[MouseEvent] | MouseEvent' = None,
        x: 'None | Container[int] | int' = None,
        y: 'None | Container[int] | int' = None,
    ) -> 'Callable':
        return super().subscribe(type, x, y)


class MouseOut(midiscripter.base.port_base.Output):
    """Mouse output port. Sends [`MouseMsg`][midiscripter.MouseMsg] objects.

    Warning:
        Transparent `MouseIn` -> `MouseOut` proxy won't work since it will react to its own output.

        Use `MouseOut` only for one-time movements.
    """

    _force_uid: ClassVar[str] = 'Mouse Output'

    def __init__(self):
        """"""
        super().__init__(self._force_uid)
        self.__pynput_controller = pynput.mouse.Controller()

    def send(self, msg: MouseMsg) -> None:
        """Send the mouse input.

        Args:
            msg: object to send
        """
        if not self._validate_msg_send(msg):
            return

        # Log messages sent before actual sending, so receive messages for sent keys
        # won't be displayed before the message
        self._log_msg_sent(msg)

        self.__pynput_controller.position = (msg.x, msg.y)

        if msg.type == MouseEvent.MOVE:
            return

        try:
            self.__pynput_controller.scroll(*scroll_event_to_args_map[msg.type])
            return
        except KeyError:
            pass

        try:
            button_name, button_action = msg.type.split('_')
            button = getattr(pynput.mouse.Button, button_name.lower())

            if button_action == 'PRESS':
                self.__pynput_controller.press(button)
            elif button_action == 'RELEASE':
                self.__pynput_controller.release(button)
            elif button_action == 'CLICK':
                self.__pynput_controller.click(button)

        except AttributeError:
            log.red(f'Invalid MouseMsg type: {msg.type}')
