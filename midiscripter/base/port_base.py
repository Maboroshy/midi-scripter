import collections
import contextlib
import copy
import inspect
import traceback
from typing import TYPE_CHECKING, TypeVar, ClassVar, Any

import midiscripter.shared
from midiscripter.logger import log

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Container
    from midiscripter.base.msg_base import Msg


@contextlib.contextmanager
def _all_opened() -> None:
    for port in _PortRegistryMeta.instance_registry.values():
        port._open()

    for call in midiscripter.shared.run_after_ports_open_subscribed_calls:

        def __call_runner() -> None:
            try:
                log('Running {call}', call=call)  # noqa: B023
                call()  # noqa: B023
            except Exception as exc:
                log.red(''.join(traceback.format_exception(exc)))

        midiscripter.shared.thread_executor.submit(__call_runner)

    yield

    for port in _PortRegistryMeta.instance_registry.values():
        port._close()

    log._flush()
    log._sink = None
    midiscripter.shared.thread_executor.shutdown(wait=False)


class _PortRegistryMeta(type):
    """Metaclass that enforces one declaration - one port instance (singleton) rule"""

    __singleton_instance_type = TypeVar('__singleton_instance_type', bound='Port')
    """Type for correct IDE recognition and code completion for returned port subclasses"""

    instance_registry: dict[tuple[str, 'Hashable'], __singleton_instance_type] = {}
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
        registry_key = (cls.__name__, uid)
        init_args = inspect.signature(cls.__init__).bind(cls, *args, **kwargs).arguments
        init_args.pop('self')

        try:
            instance = cls.instance_registry[registry_key]
            if instance._inited_with_args == init_args:
                return instance
            else:
                raise ValueError(
                    f'Init arguments for consecutive declarations '
                    f'for {cls.__name__} "{uid}" must match: {instance._inited_with_args}'
                )
        except KeyError:
            instance = super().__call__(*args, **kwargs)
            cls.instance_registry[registry_key] = instance
            instance._inited_with_args = init_args
            return instance


class Port(metaclass=_PortRegistryMeta):
    """Port base class

    Notes:
        Port declarations with the same arguments will return the same instance port (singleton)
    """

    _force_uid: ClassVar[None | str] = None
    """UID override for classes that have can have only one instance per whole class,
       like keyboard port classes. Object for these classes are declared without arguments.
    """

    is_enabled: bool
    """`True` if port is listening messages / ready to send messages"""

    _inited_with_args: dict
    """Arguments the port singleton was initialized with. Used by `_PortRegistryMeta`."""

    def __init__(self, uid: 'Hashable'):
        """
        Args:
            uid: Port's unique ID
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
    """`True` if port is listening and generating messages"""

    calls: list[None | tuple[tuple, dict], list['Callable']]
    """Message match arguments and callables that will be called with matching incoming messages.
    `None` conditions matches any message."""

    def __init__(self, uid: 'Hashable'):
        super().__init__(uid)
        self.calls: list[None | tuple[tuple, dict], list[Callable]] = []

        # workarounds for mkdocstrings issue #607
        self.calls: list[None | tuple[tuple, dict], list[Callable]]
        """Message match arguments and callables that will be called with matching incoming messages.
           `None` conditions matches any message."""

    def subscribe(
        self,
        *msg_matches_args: 'tuple[None | Container[Any] | Any]',
        **msg_matches_kwargs: 'dict[str, None | Container[Any] | Any]',
    ) -> 'Callable':
        """Decorator to subscribe a callable to the input's messages.

        Decorator without arguments subscribes a callable to all the input's messages.

        Decorator with arguments subscribes a callable to the input's messages
        that match conditions set by arguments.
        It works the same way as message's [`matches`][midiscripter.base.msg_base.Msg.matches] method:

        1. If condition is `None` or omitted it matches anything.

        2. If condition equals attribute it matches the attribute.

        3. If condition is a container and contains the attribute it matches the attribute.

        ??? Examples
            1. Calls function for all MIDI port's messages:
            ``` python
            @midi_input_instance.subscribe
            def function(msg: MidiMsg) -> None:
                pass
            ```
            2. Calls function for OSC messages from specific address:
            ``` python
            @osc_input_instance.subscribe(address='/live/song/get/track_data')
            def function(msg: OscMsg) -> None:
                pass
            ```
            3. Call object instance method for MIDI port's "note on" and "note off" messages:
            ``` python
            midi_input_instance.subscribe((MidiType.NOTE_ON, MidiType.NOTE_OFF))(object.method)
            ```

        Returns:
            Subscribed callable.
        """

        def wrapped_subscribe(call: 'Callable[[Msg], None]') -> 'Callable':
            if msg_matches_args[0] is call or not msg_matches_args and not msg_matches_kwargs:  # noqa: SIM108
                conditions = None
            else:
                conditions = (msg_matches_args, msg_matches_kwargs)

            try:
                call_list_for_conditions = next(
                    entry[1] for entry in self.calls if entry[0] == conditions
                )
                call_list_for_conditions.append(call)
            except StopIteration:
                self.calls.append((conditions, [call]))

            call.conditions = conditions
            call.statistics = collections.deque(maxlen=20)

            return call

        if callable(msg_matches_args[0]):
            return wrapped_subscribe(msg_matches_args[0])

        return wrapped_subscribe

    def _send_input_msg_to_calls(self, msg: 'Msg') -> None:
        """Sends the message received by the input port to subscribed calls.

        Notes:
            Not supposed to be overridden in subclasses.
            Supposed to be called from the listener thread started
            by the subclass implementation of `open` method.

        Args:
            msg: A message received by the input port to send to its registered calls.
        """
        log('{input} got message {msg}', input=self, msg=msg)

        if not self.is_enabled:
            return

        calls = []
        for conditions, call_list in self.calls:
            if conditions is None or msg.matches(*conditions[0], **conditions[1]):
                calls.extend(call_list)

        msg_copies = [copy.copy(msg) for _ in range(len(calls))]
        midiscripter.shared.thread_executor.map(self.__call_worker, calls, msg_copies)

    @staticmethod
    def __call_worker(call: 'Callable', msg: 'Msg') -> None:
        """Function called in thread for each subscribed call and each received message.

        Notes:
            Not supposed to be overridden in subclasses.
            Supposed to be called from `_send_input_msg_to_calls` method.

        Args:
            call: Subscribed callable.
            msg: Received message to use as callable only argument.
        """
        try:
            call(msg)
            call.statistics.append(msg._age_ms)
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
