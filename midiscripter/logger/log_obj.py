import collections
import time
from typing import TYPE_CHECKING, NamedTuple, Any

import midiscripter.shared

if TYPE_CHECKING:
    from collections.abc import Callable


class LogObjRef:
    __slots__ = ('text', 'color', 'link')
    text: str
    color: None | str
    link: None | str

    def __init__(self, obj: Any):
        self.text = str(obj)
        try:
            self.color = obj._gui_color
            self.link = repr(obj) if obj._log_show_link else None
        except AttributeError:
            self.color = None
            self.link = None


class LogEntry(NamedTuple):
    text: str
    format_args: tuple[LogObjRef, ...]
    format_kwargs: dict[str, LogObjRef]
    timestamp: str
    color: None | str


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

    _formatter: 'Callable[list[[LogEntry | None]], str]'
    _sink: 'Callable[[str], None]'
    _accepts_messages: bool
    _flushing_is_enabled: bool

    def __init__(self):
        self._accepts_messages = True
        self.__flushing_is_enabled = False

        self.__buffer: collections.deque[LogEntry]
        self.__buffer = collections.deque(maxlen=self.BUFFER_SIZE)
        self.__last_entry_time = time.time()

    def __call__(self, text: str, *args, **kwargs):
        """Print log message.

        Args:
            text: Log entry to print. Use `.format` style string to insert kwargs
            args: Optional arguments to `.format` text with
            kwargs: Optional arguments to `.format` text with

        [inputs][midiscripter.base.port_base.Input],
        [outputs][midiscripter.base.port_base.Output],
        [messages][midiscripter.base.msg_base.Msg] and callables arguments are highlighted.
        """
        if not self._accepts_messages:
            return

        try:
            entry_color = kwargs.pop('_color')
        except KeyError:
            entry_color = None

        format_args = tuple(LogObjRef(obj) for obj in args)
        format_kwargs = {arg: LogObjRef(obj) for arg, obj in kwargs.items()}

        now_time = midiscripter.shared.precise_epoch_time()
        timestamp = self._get_precise_timestamp(now_time)

        log_entry = LogEntry(text, format_args, format_kwargs, timestamp, entry_color)

        if now_time - self.__last_entry_time > self.ADD_SPACER_THRESHOLD_SEC:
            self.__buffer.append(LogEntry('', (), {}, timestamp, entry_color))
        self.__last_entry_time = now_time

        self.__buffer.append(log_entry)

    @property
    def _flushing_is_enabled(self) -> bool:
        return self.__flushing_is_enabled

    @_flushing_is_enabled.setter
    def _flushing_is_enabled(self, state: bool) -> None:
        if not self._formatter or not self._sink:
            raise AttributeError('Set `log._formatter` and `log._sink` before enabling flushing')

        self.__flushing_is_enabled = state
        if state:
            midiscripter.shared.thread_executor.submit(self._buffer_flush_worker)

    def _buffer_flush_worker(self) -> None:
        """Thread worker loop that flushes buffered messages"""
        while self.__flushing_is_enabled:
            if self.__buffer:
                self._flush()
            time.sleep(self.FLUSH_DELAY)

    def _flush(self) -> None:
        """Sends buffered messages to sink"""
        output_entries = []
        while self.__buffer:
            output_entries.append(self.__buffer.popleft())  # for thread safety

        try:
            self._sink(self._formatter(output_entries))
        except RuntimeError:  # ignore Qt error on widget destruction at app exit
            pass

    @staticmethod
    def _get_precise_timestamp(precise_epoch_time: None | float = None) -> str:
        """Returns current timestamp with microsecond precision as a string
        The argument is to don't get current time two times during log call"""
        precise_time = precise_epoch_time or midiscripter.shared.precise_epoch_time()
        time_string = time.strftime('%H:%M:%S', time.localtime(precise_time))

        # >1.5 times faster than datetime
        after_dot = repr(precise_time).split('.')[1][:6].ljust(6, '0')
        milisec_part = after_dot[:3]
        microsec_part = after_dot[3:]
        return f'{time_string}.{milisec_part},{microsec_part}'

    def red(self, text: str, *args, **kwargs) -> None:
        """Print red log message."""
        self(text, *args, _color='red', **kwargs)

    def blue(self, text: str, *args, **kwargs) -> None:
        """Print blue log message."""
        self(text, *args, _color='blue', **kwargs)

    def cyan(self, text: str, *args, **kwargs) -> None:
        """Print cyan log message."""
        self(text, *args, _color='cyan', **kwargs)

    def magenta(self, text: str, *args, **kwargs) -> None:
        """Print magenta log message."""
        self(text, *args, _color='magenta', **kwargs)

    def green(self, text: str, *args, **kwargs) -> None:
        """Print green log message."""
        self(text, *args, _color='green', **kwargs)

    def yellow(self, text: str, *args, **kwargs) -> None:
        """Print yellow log message."""
        self(text, *args, _color='yellow', **kwargs)
