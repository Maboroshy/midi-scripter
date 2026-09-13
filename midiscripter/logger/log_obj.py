import collections
import datetime
import time
from typing import TYPE_CHECKING, Any

import midiscripter.shared

if TYPE_CHECKING:
    from collections.abc import Callable
    from midiscripter.base.port_base import Port, Output, Subscribable, SubscribedCall
    from midiscripter.base.msg_base import Msg


_time_start = time.time() - time.perf_counter()


class LogObjRef:
    __slots__ = ('text', 'color', 'link')
    text: str
    color: None | str
    link: None | str

    def __init__(self, obj: Any):
        self.text = str(obj)

        try:
            self.color = obj._log_color
        except AttributeError:
            self.color = None

        try:
            self.link = repr(obj) if obj._log_show_link else None
        except AttributeError:
            self.link = None


class LogEntry:
    __slots__ = ('timestamp', 'text', 'format_args', 'format_kwargs', 'color')
    timestamp: str
    text: str
    format_args: list[LogObjRef]
    format_kwargs: dict[str, LogObjRef]
    color: None | str

    def __init__(self, time_delta: float | None, text: str, args: Any, kwargs: Any) -> None:
        self.timestamp = self.__prepare_timestamp(time_delta) if time_delta is not None else ''
        self.text = str(text)
        self.color = kwargs.pop('_color', None)
        self.format_args = [LogObjRef(obj) for obj in args]
        self.format_kwargs = {arg: LogObjRef(obj) for arg, obj in kwargs.items()}

    @staticmethod
    def __prepare_timestamp(time_delta: float) -> str:
        precise_time = _time_start + time_delta
        struct = datetime.datetime.fromtimestamp(precise_time)
        mcs = struct.microsecond
        return f'{struct.hour:02d}:{struct.minute:02d}:{struct.second:02d}.{mcs // 1000:03d},{mcs % 1000:03d}'


class Log:
    """Prints log messages to GUI Log widget or console.
    Can print messages in different text colors and highlight object representations.

    Example:
        `log('message')` for new log entry

        `log.red('red message')` for log entry printed in red color

        `log('{call} received {msg}', call=call_function, msg=some_msg)`
        for log entry with highlighted object representations.
    """

    FLUSH_DELAY = 0.10

    ADD_SPACER_THRESHOLD_SEC = 2
    """Time in seconds after which an empty line is added to log to separate logged actions"""

    BUFFER_SIZE = 500
    """Max size of message buffer to flush to log widget when it becomes visible"""

    _formatter: 'Callable[list[LogEntry | None], str]'
    _sink: 'Callable[[str], None]'
    _accepts_messages: bool
    _flushing_is_enabled: bool

    def __init__(self):
        self._accepts_messages = True
        self.__flushing_is_enabled = False
        self.__buffer = collections.deque(maxlen=self.BUFFER_SIZE)
        self.__last_entry_time = 0

    def __call__(self, text: str | Any, *args: Any, **kwargs: Any):
        """Print log message.

        Args:
            text: Log entry to print. Use `.format` style string to insert kwargs
            args: Optional arguments to `.format` text with
            kwargs: Optional arguments to `.format` text with

        [inputs][midiscripter.base.port_base.Input],
        [outputs][midiscripter.base.port_base.Output],
        [messages][midiscripter.base.msg_base.Msg] and callable arguments are highlighted.
        """
        if self._accepts_messages:
            self.__buffer.append((time.perf_counter(), text, args, kwargs))

    @property
    def _flushing_is_enabled(self) -> bool:
        return self.__flushing_is_enabled

    @_flushing_is_enabled.setter
    def _flushing_is_enabled(self, state: bool) -> None:
        if not self._formatter or not self._sink:
            raise AttributeError('Set `log._formatter` and `log._sink` before enabling flushing')

        self.__flushing_is_enabled = state
        if state:
            time.sleep(self.FLUSH_DELAY * 2)  # time for previous thread to stop, for tight calls
            midiscripter.shared.thread_executor.submit(self._buffer_flush_worker)

    def _buffer_flush_worker(self) -> None:
        """Thread worker loop that flushes buffered messages"""
        while self.__flushing_is_enabled:
            if self.__buffer:
                self._flush()
            time.sleep(self.FLUSH_DELAY)

    def _flush(self) -> None:
        """Sends buffered messages to sink"""
        log_entries = []
        while self.__buffer:
            time_delta, text, args, kwargs = self.__buffer.popleft()  # for thread safety

            if time_delta - self.__last_entry_time > self.ADD_SPACER_THRESHOLD_SEC:
                log_entries.append(LogEntry(None, '', (), {}))
            self.__last_entry_time = time_delta

            log_entries.append(LogEntry(time_delta, text, args, kwargs))

        try:
            self._sink(self._formatter(log_entries))
        except (RuntimeError, AttributeError):  # ignore Qt error on widget destruction at app exit
            pass

    def _port_not_found(self, port_instance: 'Port') -> None:
        self("Can't find {port} {desc}. Check the port name.", port=port_instance, desc=port_instance._log_description)

    def _port_open(self, port_instance: 'Port', success: bool, *, custom_text: str = '', **log_call_kwargs) -> None:
        """Print port open message"""
        if custom_text:
            self(custom_text, **log_call_kwargs)
        elif success:
            if port_instance._is_virtual:
                self('Created and opened {port} virtual {desc}',
                    port=port_instance,
                    desc=port_instance._log_description,
                )
            else:
                self('Opened {port} {desc}', port=port_instance, desc=port_instance._log_description)
        else:
            self.red('Failed to open {port} {desc}', port=port_instance, desc=port_instance._log_description)

    def _port_close(self, port_instance: 'Port', success: bool, *, custom_text: str = '', **log_call_kwargs) -> None:
        """Print port close message"""
        if custom_text:
            self(custom_text, **log_call_kwargs)
        elif success:
            self('Closed {port} {desc}', port=port_instance, desc=port_instance._log_description)
        else:
            self.red('Failed to close {port} {desc}', port=port_instance, desc=port_instance._log_description)

    def _send_failed_port_is_closed(self, port_instance: 'Port', msg: 'Msg') -> None:
        self("Can't send message {msg} - {output} is not opened!", msg=msg, output=port_instance, _color='red')

    def _msg_received(self, subscribable_instance: 'Subscribable', msg: 'Msg') -> None:
        """Print message received message"""
        self('{subscribable} got message {msg}', subscribable=subscribable_instance, msg=msg)

    def _msg_sent(self, output: 'Output', msg: 'Msg') -> None:
        """Print message sent message"""
        self('{output} sent message {msg}', output=output, msg=msg)

    def _call_made(self, call: 'SubscribedCall') -> None:
        """Print subscribed callable called message"""
        if '._' not in str(call):
            self('Calling {call}', call=call)

    def red(self, text: str | Any, *args, **kwargs) -> None:
        """Print red log message"""
        self(text, *args, _color='red', **kwargs)

    def blue(self, text: str | Any, *args, **kwargs) -> None:
        """Print blue log message"""
        self(text, *args, _color='blue', **kwargs)

    def cyan(self, text: str | Any, *args, **kwargs) -> None:
        """Print cyan log message"""
        self(text, *args, _color='cyan', **kwargs)

    def magenta(self, text: str | Any, *args, **kwargs) -> None:
        """Print magenta log message"""
        self(text, *args, _color='magenta', **kwargs)

    def green(self, text: str | Any, *args, **kwargs) -> None:
        """Print green log message"""
        self(text, *args, _color='green', **kwargs)

    def yellow(self, text: str | Any, *args, **kwargs) -> None:
        """Print yellow log message"""
        self(text, *args, _color='yellow', **kwargs)
