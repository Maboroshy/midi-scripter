import collections
import contextlib
import copy
import traceback
from collections.abc import Callable, Hashable
from typing import TYPE_CHECKING, TypeVar

import midiscripter.base.shared
from midiscripter.logger import log

if TYPE_CHECKING:
    from midiscripter.base.msg_base import Msg


@contextlib.contextmanager
def _all_opened() -> None:
    for port in _PortRegistryMeta.instance_registry.values():
        port._open()

    for call in midiscripter.base.shared.run_after_ports_open_subscribed_calls:

        def __call_runner() -> None:
            try:
                log('Running {call}', call=call)  # noqa: B023
                call()  # noqa: B023
            except Exception as exc:
                log.red(''.join(traceback.format_exception(exc)))

        midiscripter.base.shared.thread_executor.submit(__call_runner)

    yield

    for port in _PortRegistryMeta.instance_registry.values():
        port._close()

    log._flush()
    log._sink = None
    midiscripter.base.shared.thread_executor.shutdown(wait=True)


class _PortRegistryMeta(type):
    """Metaclass that enforces one uid - one port instance (singleton) rule"""

    __singleton_instance_type = TypeVar('__singleton_instance_type', bound='Port')
    """Type for correct IDE recognition and code completion for returned port subclasses"""

    instance_registry: dict[tuple[str, Hashable], __singleton_instance_type] = {}
    """Declared ports register as port class name and port uid to port instance map"""

    def __call__(
        cls: type[__singleton_instance_type], *args, **kwargs
    ) -> __singleton_instance_type:
        """
        Args:
            *args: if the class' `_force_uid` attribute is `None` (default)
                   the metaclass uses the first argument as uid
            **kwargs: -

        Returns:
            The singleton class instance that has requested uid
        """
        uid = cls._force_uid or args[0]

        try:
            return cls.instance_registry[(cls.__name__, uid)]
        except KeyError:
            instance = super().__call__(*args, **kwargs)
            cls.instance_registry[(cls.__name__, uid)] = instance
            return instance


class Port(metaclass=_PortRegistryMeta):
    """Port base class

    Notes:
        Port declaration with `uid` of an already existing port
        will return the existing port (singleton)
    """

    is_enabled: bool
    """`True` if port is listening messages / ready to send messages"""

    _force_uid = None
    """UID override for classes that have can have only one instance per whole class,
       like keyboard port class which can have only one instance for the system.
       Object for these classe are declared without arguments.
    """

    def __init__(self, uid: Hashable):
        """
        Args:
            uid: Port's unique ID that will always lead to the same port instance
        """
        self._uid = uid
        self.is_enabled = False

        self.is_enabled: bool  # workaround for mkdocstrings issue #607
        """`True` if port is listening messages / ready to send messages"""

    def __repr__(self):
        if self._force_uid:
            return f'{self.__class__.__name__}()'
        else:
            return f'{self.__class__.__name__}({self._uid.__repr__()})'

    def __str__(self):
        return str(self._uid)

    @property
    def _is_available(self) -> bool:
        """Port is available and can be opened."""
        return True

    def _open(self) -> None:
        """Prepares and activates the port

        Notes:
            Supposed to be overridden in subclasses
            Should have a check against second opening
            Must set `is_enabled` parameter to `True`
        """
        self.is_enabled = True

    def _close(self) -> None:
        """Deactivates the port.

        Notes:
            Supposed to be overridden in subclasses
            Must set `is_enabled` parameter to `False`
        """
        self.is_enabled = False


class Input(Port):
    """Input port base class"""

    is_enabled: bool
    """`True` if port is listening and generating messages."""

    subscribed_calls: list[Callable]
    """Callables that will be called with incoming messages. Can be modified."""

    _call_statistics: dict[Callable, collections.deque[float]] = {}
    """Statistics for each call's execution time in milliseconds for the last 20 runs."""

    def __init__(self, uid: Hashable):
        super().__init__(uid)
        self.subscribed_calls: list[Callable] = []

        self.subscribed_calls: list[Callable]  # workaround for mkdocstrings issue #607
        """Callables that will be called with incoming messages. Can be modified."""

    # A Decorator
    def subscribe(self, function: Callable[['Msg'], None]) -> Callable:
        """Decorator to subscribe a callable to the input's messages

        ??? Example
            ``` python
            @input_instance.subscribe
            def function(msg: Msg) -> None:
                pass
            ```
            ``` python
            input_instance.subscribe(object.method)
            ```

        Args:
            function: A callable that takes the input port's message as the only argument.

        Returns:
            Subscribed callable.
        """
        if function not in self.subscribed_calls:
            self._call_statistics[function] = collections.deque(maxlen=20)
            self.subscribed_calls.append(function)
            log('{input} subscribed {call}', input=self, call=function)
        return function

    def _send_input_msg_to_calls(self, msg: 'Msg') -> None:
        """Sends the message received by the input port to subscribed calls.

        Notes:
            Not supposed to be overridden in subclasses.
            Supposed to be called from the listener thread started
            by the subclass implementation of `open` method.

        Args:
            msg: A message received by the input port to send to it's registered calls.
        """
        log('{input} got message {msg}', input=self, msg=msg)

        if self.is_enabled:
            # pre-copying messages to reduce jitter a little
            msg_copies = [copy.copy(msg) for _ in range(len(self.subscribed_calls))]
            midiscripter.base.shared.thread_executor.map(
                self.__call_worker, self.subscribed_calls, msg_copies
            )

    def __call_worker(self, function: Callable, msg: 'Msg') -> None:
        """Function called in thread for each subscribed call and each received message.

        Notes:
            Not supposed to be overridden in subclasses.
            Supposed to be called from `_send_input_msg_to_calls` method.

        Args:
            function: Subscribed callable.
            msg: Received message to use as callable only argument.
        """
        try:
            function(msg)
            self._call_statistics[function].append(msg._age_ms)
        except TypeError:
            function()
            self._call_statistics[function].append(msg._age_ms)
        except Exception as exc:
            log.red(''.join(traceback.format_exception(exc)))


class Output(Port):
    """Output port base class"""

    is_enabled: bool
    """`True` if port is ready to send messages"""

    def send(self, msg: 'Msg') -> None:
        """Send message using the output port.

        Args:
            msg: Message to send.
        """
        if not self._validate_msg_send(msg):
            return

        raise NotImplementedError

        # noinspection PyUnreachableCode
        self._log_msg_sent(msg)

    def _validate_msg_send(self, msg: 'Msg') -> bool:
        if not self.is_enabled:
            log.red("Can't send message {msg}. {output} is disabled!", msg=msg, output=self)
            return False
        return True

    def _log_msg_sent(self, msg: 'Msg') -> None:
        if msg.source:
            log(
                '{output} sent message {msg} received {age_ms} ms ago',
                output=self,
                msg=msg,
                age_ms=msg._age_ms,
            )
        else:
            log('{output} sent message {msg}', output=self, msg=msg)
