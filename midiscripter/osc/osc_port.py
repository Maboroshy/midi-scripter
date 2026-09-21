import queue
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
    from midiscripter.base.match_conditions import MatchCondition


def _parse_ip_port(ip_port: str | int) -> tuple[str, int]:
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
        raise ValueError(f'Invalid OSC port address: {ip_port}')

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
        self.__listener_ip_port = _parse_ip_port(listener_ip_port)
        self.__dispatcher = pythonosc.osc_server.Dispatcher(False)
        self.__dispatcher.set_default_handler(self.__osc_server_msg_handler)

        self._query_queues_lock = threading.Lock()
        self._query_queues = []

    def __osc_server_msg_handler(self, address: str, *data) -> None:
        if not data:
            data = None
        elif len(data) == 1:
            data = data[0]
        input_msg = OscMsg(address, data)
        self._send_input_msg_to_calls(input_msg)

        if self._query_queues:
            with self._query_queues_lock:
                for queue_ in self._query_queues:
                    queue_.put(input_msg)

    def _open(self) -> None:
        try:
            self.__osc_server = pythonosc.osc_server.BlockingOSCUDPServer(self.__listener_ip_port, self.__dispatcher)
            midiscripter.shared.thread_executor.submit(self.__osc_server.serve_forever)
            self._is_opened = True
            log._port_open(self, True)
        except OSError:
            log._port_open(self, False)

    def _close(self) -> None:
        self.__osc_server.shutdown()
        self.__osc_server.server_close()
        self._is_opened = False
        log._port_close(self, True)

    @overload
    def subscribe(self, call: 'Callable[[OscMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        address: 'None | MatchCondition | Container | str' = None,
        data: 'None | MatchCondition | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        address: 'None | MatchCondition | Container | str' = None,
        data: 'None | MatchCondition | Container | str | bytes | bool | int | float | list | tuple' = None,
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
        self.__osc_client = pythonosc.udp_client.SimpleUDPClient(target_ip_address, target_port)

    def send(self, msg: OscMsg) -> None:
        """Send the OSC message.

        Args:
            msg: object to send
        """
        data = list(msg.data) if isinstance(msg.data, tuple) else msg.data
        self.__osc_client.send_message(msg.address, data)
        log._msg_sent(self, msg)


class OscIO(midiscripter.base.port_base.IoPort):
    """Open Sound Control input/output port that combines [`OscIn`][midiscripter.OscIn] and
    [`OscOut`][midiscripter.OscOut] ports.
    Produces and sends [`OscMsg`][midiscripter.OscMsg] objects.
    """
    _input_port: OscIn
    _output_port: OscOut

    _log_description: str = 'OSC i/o port'

    def __init__(self, input_listener_ip_port: str | int, output_target_ip_port: str | int):
        """
        Args:
            input_listener_ip_port: `'ip:port'` or local port to listen for incoming OSC messages
            output_target_ip_port: `'ip:port'` or local port to send output OSC messages to
        """
        input_port = OscIn(input_listener_ip_port)
        output_port = OscOut(output_target_ip_port)
        super().__init__(f'{input_listener_ip_port} > {output_target_ip_port}', input_port, output_port)

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
        log("Requesting '{address}' data from OSC {input}", address=address, input=self._input_port)

        query_queue = queue.SimpleQueue()
        query_queue_list = self._input_port._query_queues
        with self._input_port._query_queues_lock:
            query_queue_list.append(query_queue)
        self._output_port.send(OscMsg(address, data))

        while True:
            try:
                msg = query_queue.get(timeout=timeout_sec)
                if msg.address == address:
                    with self._input_port._query_queues_lock:
                        query_queue_list.remove(query_queue)
                    return msg.data
            except queue.Empty:
                with self._input_port._query_queues_lock:
                    query_queue_list.remove(query_queue)
                raise TimeoutError(f"OSC query to '{address}' got no response") from None

    @overload
    def subscribe(self, call: 'Callable[[OscMsg], None]') -> 'Callable': ...

    @overload
    def subscribe(
        self,
        address: 'None | MatchCondition | Container | str' = None,
        data: 'None | MatchCondition | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable': ...

    def subscribe(
        self,
        address: 'None | MatchCondition | Container | str' = None,
        data: 'None | MatchCondition | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> 'Callable':
        return self._input_port.subscribe(address, data)

    def send(self, msg: OscMsg) -> None:
        """Send the OSC message.

        Args:
            msg: object to send
        """
        self._output_port.send(msg)
