import queue

from midiscripter.logger import log
from midiscripter.osc.osc_msg import OscMsg
from midiscripter.osc.osc_port import OscIn, OscOut


class OscQueryMaker:
    """The helper class to handle OSC request - response queries."""

    def __init__(self, osc_in: OscIn, osc_out: OscOut):
        """
        Args:
            osc_in: OscIn port for incoming responses.
            osc_out: OscOut port to send requests to.
        """
        self.__osc_in = osc_in
        self.__osc_out = osc_out
        self.__query_register: dict[str, queue.SimpleQueue] = {}
        osc_in.subscribe(self.__osc_query_maker_in)

    def __osc_query_maker_in(self, msg: OscMsg) -> None:
        try:
            self.__query_register[msg.address].put(msg.data)
        except KeyError:
            pass

    def query(
        self, address: str, timeout_sec: float = 2
    ) -> str | bytes | bool | float | list | tuple:
        """Query data by sending the request to OSC address
           and returning the response from that address

        Args:
            address: OSC address to send request to
            timeout_sec: time for response until raising TimeoutError

        Returns:
            Response OSC message data
        """
        result_queue = queue.SimpleQueue()
        self.__query_register[address] = result_queue
        log("Requesting '{address}' data from {input}", address=address, input=self.__osc_in)
        self.__osc_out.send(OscMsg(address))

        try:
            result = result_queue.get(timeout=timeout_sec)
            self.__query_register.pop(address)
            return result
        except queue.Empty:
            self.__query_register.pop(address)
            raise TimeoutError from None
