import threading
from typing import TYPE_CHECKING, overload

import pythonosc.osc_server
import pythonosc.udp_client

import midiscripter.base.port_base
import midiscripter.shared
import midiscripter.osc.osc_msg
from midiscripter.logger import log
from midiscripter.osc.osc_msg import OscMsg

if TYPE_CHECKING:
    from collections.abc import Container, Callable


def _parse_ip_port(ip_port: str | int) -> (str, int):
    """Parses 'ip:port' or local port to get ip and port

    Args:
        ip_port: 'ip:port' or local port
    Returns:
        ip, port number
    """
    if isinstance(ip_port, int) or ip_port.isdigit():
        ip_address = '127.0.0.1'
        port = int(ip_port)
    elif ':' in ip_port:
        ip_address, port = ip_port.split(':')
        port = int(port)
    else:
        raise AttributeError(f'Invalid OSC port address: {ip_port}')

    return ip_address, port


class OscIn(midiscripter.base.port_base.Input):
    """Open Sound Control input port. Produces [`OscMsg`][midiscripter.OscMsg] objects."""

    _log_description: str = 'OSC input'

    def __init__(self, listener_ip_port: str | int):
        """
        Args:
            listener_ip_port: `'ip:port'` or local port to listen for incoming OSC messages
        """
        super().__init__(listener_ip_port)
        self.listener_ip_address, self.listener_port = _parse_ip_port(listener_ip_port)
        self.__dispatcher = pythonosc.osc_server.Dispatcher()
        self.__dispatcher.set_default_handler(self.__osc_server_msg_handler)

    def __osc_server_msg_handler(self, address: str, *data) -> None:
        if len(data) == 1:
            data = data[0]
        input_msg = OscMsg(address, data, source=self)
        self._send_input_msg_to_calls(input_msg)

    def _open(self) -> None:
        self._osc_server = pythonosc.osc_server.BlockingOSCUDPServer(
            (self.listener_ip_address, self.listener_port), self.__dispatcher
        )
        midiscripter.shared.thread_executor.submit(self._osc_server.serve_forever)
        self.is_opened = True
        log._port_open(self, True)

    def _close(self) -> None:
        self._osc_server.server_close()
        self.is_opened = False
        log._port_close(self, True)

    @overload
    def subscribe(self, call: 'Callable[[OscMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        address: 'None | Container | str' = None,
        data: 'None | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        address: 'None | Container | str' = None,
        data: 'None | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable':
        return super().subscribe(address, data)


class OscOut(midiscripter.base.port_base.Output):
    """Open Sound Control output port. Sends [`OscMsg`][midiscripter.OscMsg] objects."""

    _log_description: str = 'OSC output'

    def __init__(self, target_ip_port: str | int):
        """
        Args:
            target_ip_port: `'ip:port'` or local port to send output OSC messages to
        """
        super().__init__(target_ip_port)
        target_ip_address, target_port = _parse_ip_port(target_ip_port)
        self._osc_client = pythonosc.udp_client.SimpleUDPClient(target_ip_address, target_port)

    def send(self, msg: OscMsg) -> None:
        """Send the OSC message.

        Args:
            msg: object to send
        """
        if not self._validate_msg_send(msg):
            return

        data = list(msg.data) if isinstance(msg.data, tuple) else msg.data
        self._osc_client.send_message(msg.address, data)
        log._msg_sent(self, msg)


class OscIO(midiscripter.base.port_base.MultiPort):
    """Open Sound Control input/output port that combines [`OscIn`][midiscripter.OscIn] and
    [`OscOut`][midiscripter.OscOut] ports.
    Produces and sends [`OscMsg`][midiscripter.OscMsg] objects.
    """

    _log_description: str = 'OSC i/o port'

    def __init__(self, input_listener_ip_port: str | int, output_target_ip_port: str | int):
        """
        Args:
            input_listener_ip_port: `'ip:port'` or local port to listen for incoming OSC messages
            output_target_ip_port: `'ip:port'` or local port to send output OSC messages to
        """
        input_port = OscIn(input_listener_ip_port)
        output_port = OscOut(output_target_ip_port)
        super().__init__(
            f'{input_listener_ip_port} > {output_target_ip_port}', input_port, output_port
        )

        self.__new_msg_condition = threading.Condition()
        self.__last_msg = OscMsg('')
        input_port.subscribe(self.__osc_query_listener)

    def query(
        self,
        address: str,
        data: str | bytes | bool | int | float | list | tuple = None,
        *,
        timeout_sec: float = 1,
    ) -> str | bytes | bool | float | list | tuple:
        """Queries data by sending the request to OSC address
           and returns the data of response from that address

        Args:
            address: OSC address to send request to
            data: data to send request with, not used to match response
            timeout_sec: time for response until raising `TimeoutError`

        Raises:
            TimeoutError: on query timeout

        Returns:
            Response OSC message data
        """
        with self.__new_msg_condition:
            self.__last_msg = OscMsg('')

            log(
                "Requesting '{address}' data from OSC {input}",
                address=address,
                input=self._input_ports[0],
            )
            self._output_ports[0].send(OscMsg(address, data))

            if self.__new_msg_condition.wait_for(
                lambda: self.__last_msg.address == address, timeout=timeout_sec
            ):
                return self.__last_msg.data
            else:
                raise TimeoutError(f"OSC query to '{address}' got no response")

    def __osc_query_listener(self, msg: OscMsg) -> None:
        with self.__new_msg_condition:
            self.__last_msg = msg
            self.__new_msg_condition.notify_all()

    @overload
    def subscribe(self, call: 'Callable[[OscMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        address: 'None | Container | str' = None,
        data: 'None | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        address: 'None | Container | str' = None,
        data: 'None | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable':
        return self._input_ports[0].subscribe(address, data)

    def send(self, msg: OscMsg) -> None:
        """Send the OSC message.

        Args:
            msg: object to send
        """
        self._output_ports[0].send(msg)
