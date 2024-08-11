import time
from typing import overload

import midiscripter.base.port_base
import midiscripter.shared
from midiscripter.base.msg_base import Msg
from midiscripter.logger import log


class MetronomeIn(midiscripter.base.port_base.Input):
    """The input port that sends messages with set interval

    Notes:
        `Metronome` sets extra `bpm` and `number` attributes to any message it sends
    """

    @overload
    def __init__(self, name: str, bpm: float = 60, *, msg_to_send: Msg = Msg('Click')): ...  # noqa: B008

    @overload
    def __init__(self, bpm: float, *, msg_to_send: Msg = Msg('Click')): ...  # noqa: B008

    def __init__(
        self,
        name_or_bpm: str | float,
        bpm: float = 60,
        *,
        msg_to_send: Msg = Msg('Click'),  # noqa: B008
    ):
        """
        **Overloads:**
            ``` python
            MetronomeIn(name: str, bpm: float = 60, msg_to_send: Msg = Msg('Click'))
            ```
            ``` python
            MetronomeIn(bpm: float, *, msg_to_send: Msg = Msg('Click'))
            ```

        Args:
            name (str): Metronome name
            bpm: Message sending interval in beats per minute
            msg_to_send: Message the port will send
        """
        super().__init__(name_or_bpm)
        try:
            self.bpm = float(name_or_bpm)
        except ValueError:
            self.bpm = bpm

        self.msg_to_send = msg_to_send

    @property
    def bpm(self) -> float:
        """Message sending interval in beats per minute."""
        return 60 / self.__interval_sec

    @bpm.setter
    def bpm(self, bpm: float) -> None:
        self.__interval_sec = 60 / bpm

    def _open(self) -> None:
        self.is_enabled = True
        midiscripter.shared.thread_executor.submit(self.__send_clicks_worker)
        log('Started {input} at {bpm}', input=self, bpm=self.bpm)
        self._call_on_port_open()

    def __send_clicks_worker(self) -> None:
        msg_counter = 1
        while self.is_enabled:
            time.sleep(self.__interval_sec)

            self.msg_to_send.source = self
            self.msg_to_send.ctime = midiscripter.shared.precise_epoch_time()
            self.msg_to_send.bpm = self.bpm
            self.msg_to_send.number = msg_counter

            self._send_input_msg_to_calls(self.msg_to_send)

            msg_counter += 1

        log('Stopped {input}', input=self)

    def _close(self) -> None:
        self.is_enabled = False
