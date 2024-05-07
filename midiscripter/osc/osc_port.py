import pythonosc.osc_server
import pythonosc.udp_client

import midiscripter.base.port_base
import midiscripter.base.shared
import midiscripter.osc.osc_msg
from midiscripter.logger import log
from midiscripter.osc.osc_msg import OscMsg


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

    def __init__(self, listener_ip_port: str | int):
        """
        Args:
            listener_ip_port: 'ip:port' or local port to listen for incoming OSC messages
        """
        super().__init__(listener_ip_port)
        self.listener_ip_address, self.listener_port = _parse_ip_port(listener_ip_port)
        self.__dispatcher = None

    def __osc_server_msg_handler(self, address: str, *data) -> None:
        if not self.is_enabled:
            return

        if len(data) == 1:
            data = data[0]
        input_msg = OscMsg(address, data, source=self)
        self._send_input_msg_to_calls(input_msg)

    def _open(self) -> None:
        if self.__dispatcher:
            self.is_enabled = True
            return

        self.__dispatcher = pythonosc.osc_server.Dispatcher()
        self.__dispatcher.set_default_handler(self.__osc_server_msg_handler)
        self._osc_server = pythonosc.osc_server.BlockingOSCUDPServer(
            (self.listener_ip_address, self.listener_port), self.__dispatcher
        )

        midiscripter.base.shared.thread_executor.submit(self._osc_server.serve_forever)
        self.is_enabled = True
        log('Opened {input}', input=self)

    def _close(self) -> None:
        self._osc_server.shutdown()
        self.is_enabled = False
        log('Stopped {input}', input=self)


class OscOut(midiscripter.base.port_base.Output):
    """Open Sound Control output port. Sends [`OscMsg`][midiscripter.OscMsg] objects."""

    def __init__(self, target_ip_port: str | int):
        """
        Args:
            target_ip_port: 'ip:port' or local port to send output OSC messages to
        """
        super().__init__(target_ip_port)
        target_ip_address, target_port = _parse_ip_port(target_ip_port)
        self._osc_client = pythonosc.udp_client.SimpleUDPClient(target_ip_address, target_port)
        self.is_enabled = True

    def send(self, msg: OscMsg) -> None:
        """Send the OSC message

        Args:
            msg: object to send
        """
        if not self._validate_msg_send(msg):
            return

        data = list(msg.data) if isinstance(msg.data, tuple) else msg.data
        self._osc_client.send_message(msg.address, data)

        self._log_msg_sent(msg)
