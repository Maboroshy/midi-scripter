import collections
import threading
import time
from typing import TYPE_CHECKING

import midiscripter.shared

if TYPE_CHECKING:
    from collections.abc import Callable
    from midiscripter.logger.console_sink import ConsoleSink
    from midiscripter.logger.html_sink import HtmlSink


class Log:
    """Prints log messages to GUI Log widget or console.
    Can print messages in different text colors and highlight object representations.

    Example:
        `log('message')` for new log entry

        `log.red('red message')` for log entry printed in red color

        `log('{call} received {msg}', call=call_function, msg=some_msg)`
        for log entry with highlighted object representations.
    """

    FLUSH_DELAY = 0.05

    ADD_SPACER_THRESHOLD_SEC = 2
    """Time in seconds after which an empty line is added to log to separate logged actions"""

    BUFFER_SIZE = 200
    """Max size of message buffer to flush to log widget when it becomes visible"""

    def __init__(self):
        self.__sink_call = None
        self.is_enabled = True

        self.__buffer = collections.deque(maxlen=self.BUFFER_SIZE)
        self.__last_entry_time = time.time()

    def __call__(self, text: str, **kwargs):
        """Print log message.

        Args:
            text: Log entry to print. Use `.format` style string to insert kwargs.
            **kwargs: Optional variables to `.format` text with.
                      Passed [inputs][midiscripter.base.port_base.Input],
                      [outputs][midiscripter.base.port_base.Output],
                      [messages][midiscripter.base.msg_base.Msg] and callables are highlighted.
        """
        if not self.is_enabled:
            return

        now_time = midiscripter.shared.precise_epoch_time()
        kwargs['_ctime_str'] = self._get_precise_time_stamp(now_time)

        if now_time - self.__last_entry_time > self.ADD_SPACER_THRESHOLD_SEC:
            self.__buffer.append(('', {}))
        self.__last_entry_time = now_time

        self.__buffer.append((str(text), kwargs))

    @property
    def _sink(self) -> 'Callable':
        """A callable that receives a list of log strings to print them for user.
        Set by starter. Can be altered to customize the logger."""
        return self.__sink_call

    @_sink.setter
    def _sink(
        self, sink_obj: 'None | HtmlSink | ConsoleSink | Callable[[list[str]], None]'
    ) -> None:
        self.__sink_call = sink_obj
        if self.__sink_call:
            self.__start_buffer_flush_thread()

    def __start_buffer_flush_thread(self) -> None:
        threading.Thread(target=self._buffer_flush_worker, daemon=True).start()

    def _buffer_flush_worker(self) -> None:
        """Thread worker loop that flushes buffered messages"""
        while self._sink:
            if self.__buffer:
                self._flush()
            time.sleep(self.FLUSH_DELAY)

    def _flush(self) -> None:
        """Sends buffered messages to sink"""
        if not self.__sink_call:
            return

        output_entries = []

        while self.__buffer:
            output_entries.append(self.__buffer.popleft())  # for thread safety

        try:
            self._sink(output_entries)
        except RuntimeError:  # ignore Qt error on widget destruction at app exit
            pass

    @staticmethod
    def _get_precise_time_stamp(precise_epoch_time: None | float = None) -> str:
        """Returns current timestamp with microsecond precision as a string

        The argument is there to not get current time two times during log call"""
        precise_time = precise_epoch_time or midiscripter.shared.precise_epoch_time()
        time_string = time.strftime('%H:%M:%S', time.localtime(precise_time))

        # >1.5 times faster than datetime
        after_dot = repr(precise_time).split('.')[1][:6].ljust(6, '0')
        milisec_part = after_dot[:3]
        microsec_part = after_dot[3:]
        return f'{time_string}.{milisec_part},{microsec_part}'

    def red(self, text: str, **kwargs) -> None:
        """Print red log message."""
        self(text, _color='red', **kwargs)

    def blue(self, text: str, **kwargs) -> None:
        """Print blue log message."""
        self(text, _color='blue', **kwargs)

    def cyan(self, text: str, **kwargs) -> None:
        """Print cyan log message."""
        self(text, _color='cyan', **kwargs)

    def magenta(self, text: str, **kwargs) -> None:
        """Print magenta log message."""
        self(text, _color='magenta', **kwargs)

    def green(self, text: str, **kwargs) -> None:
        """Print green log message."""
        self(text, _color='green', **kwargs)

    def yellow(self, text: str, **kwargs) -> None:
        """Print yellow log message."""
        self(text, _color='yellow', **kwargs)
