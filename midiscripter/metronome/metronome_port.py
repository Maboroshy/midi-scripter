import time
from typing import overload

import midiscripter.base.port_base
import midiscripter.shared
from midiscripter.base.msg_base import Msg
from midiscripter.base.port_base import Output
from midiscripter.logger import log
from .click_msg import ClickMsg


class MetronomeIn(midiscripter.base.port_base.Input):
    """The input port that sends messages with set interval.

    **Overloads:**
    ``` python
    MetronomeIn(name: str, bpm: float = 60, msg_to_send: Msg = ClickMsg())
    ```
    ``` python
    MetronomeIn(bpm: float, *, msg_to_send: Msg = ClickMsg())
    ```
    """

    @overload
    def __init__(self, name: str, bpm: float = 60, msg_to_send: Msg = ClickMsg()): ...  # noqa: B008

    @overload
    def __init__(self, bpm: float, *, msg_to_send: Msg = ClickMsg()): ...  # noqa: B008

    def __init__(self, name_or_bpm: str | float, bpm: float = 60, msg_to_send: Msg = ClickMsg()):  # noqa: B008
        """
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
        self.msg_to_send.source = self

        self.attached_passthrough_outs: list[Output] = []
        """[`Output`][midiscripter.base.port_base.Output] ports attached 
           as pass-through ports to send metronome messages"""

    @property
    def bpm(self) -> float:
        """Message sending interval in beats per minute."""
        return 60 / self.__interval_sec

    @bpm.setter
    def bpm(self, bpm: float) -> None:
        self.__interval_sec = 60 / bpm

    def passthrough_out(self, output: Output) -> None:
        """Attach output port as a pass-through port to send metronome messages.
        The output port should be compatible to send `msg_to_send` messages.

        Args:
            output: [`Output`][midiscripter.base.port_base.Output] port to use for pass-through
        """
        if output not in self.attached_passthrough_outs:
            self.attached_passthrough_outs.append(output)
            log('{input} input will pass through {output}', input=self, output=output)

    def _open(self) -> None:
        self.is_enabled = True
        midiscripter.shared.thread_executor.submit(self.__send_clicks_worker)
        log(f'Started metronome at {self.bpm} bpm')

    def __send_clicks_worker(self) -> None:
        msg_counter = 1
        while self.is_enabled:
            time.sleep(self.__interval_sec)

            self.msg_to_send.bpm = self.bpm
            self.msg_to_send.number = msg_counter
            self.msg_to_send.ctime = midiscripter.shared.precise_epoch_time()

            for output in self.attached_passthrough_outs:
                output.send(self.msg_to_send)

            self._send_input_msg_to_calls(self.msg_to_send)

            msg_counter += 1

        log(f'Stopped metronome at {self.bpm} bpm')

    def _close(self) -> None:
        self.is_enabled = False
