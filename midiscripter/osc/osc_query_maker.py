import threading

from midiscripter.logger import log
from midiscripter.osc.osc_msg import OscMsg
from midiscripter.osc.osc_port import OscIn, OscOut


class OscQueryMaker:
    """The helper class to handle OSC request - response queries.
    Should be a permanent object rather than created for each request.
    """

    def __init__(self, osc_in: OscIn, osc_out: OscOut):
        """
        Args:
            osc_in: OscIn port for incoming responses.
            osc_out: OscOut port to send requests to.
        """
        self.__osc_in = osc_in
        self.__osc_out = osc_out

        self.__last_msg = OscMsg('')
        self.__new_msg_condition = threading.Condition()

        osc_in.subscribe(self.__osc_query_listener)

    def __osc_query_listener(self, msg: OscMsg) -> None:
        with self.__new_msg_condition:
            self.__last_msg = msg
            self.__new_msg_condition.notify_all()

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
            timeout_sec: time for response until raising TimeoutError

        Returns:
            Response OSC message data
        """
        with self.__new_msg_condition:
            log(
                "Requesting '{address}' data from OSC {input}", address=address, input=self.__osc_in
            )
            self.__osc_out.send(OscMsg(address, data))

            if self.__new_msg_condition.wait_for(
                lambda: self.__last_msg.address == address, timeout=timeout_sec
            ):
                return self.__last_msg.data
            else:
                log.red(f"OSC query to '{address}' got no response")
