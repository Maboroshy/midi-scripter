import collections
import contextlib
import copy
import enum
import inspect
import traceback
from typing import TYPE_CHECKING, TypeVar, ClassVar, Any

import midiscripter.shared
from midiscripter.logger import log
from midiscripter.base.msg_base import Msg

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Container


class CallOn(enum.StrEnum):
    """Special conditions to use as `@input_port.subscribe(argument)`"""

    NOT_MATCHED_BY_ANY_CALL = 'NOT MATCHED BY ANY CALLS'
    """Call when a message is not matched by any other call"""

    PORT_OPEN = 'PORT OPEN'
    """Call after port is opened"""


@contextlib.contextmanager
def _all_opened() -> None:
    for port in Port._instances:
        port._open()

    yield

    for port in Port._instances:
        port._close()

    midiscripter.shared.thread_executor.shutdown(wait=False)


class SubscribedCall:
    """Wrapper object created for subscribed callable"""

    conditions: None | tuple[tuple, dict]
    """Message match conditions for call"""

    statistics: collections.deque
    """Last 20 call execution durations in milliseconds"""

    _gui_color: str = 'cyan'
    _log_show_link: bool = False

    def __init__(self, conditions: 'None | tuple[tuple, dict]', callable_: 'Callable'):
        self.conditions = conditions
        self.statistics = collections.deque(maxlen=20)
        self.__callable = callable_
        self.__required_parameter_count = len(inspect.signature(callable_).parameters)

    def __call__(self, msg: 'Msg' = None) -> None:
        msg = msg or Msg('')
        if self.__required_parameter_count == 0:
            self.__callable()
        else:
            self.__callable(msg)
        self.statistics.append(msg._age_ms)

    def __str__(self):
        return self.__callable.__qualname__


class Port:
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
    """The arguments the port singleton was initialized with. Used by `_PortRegistryMeta`."""

    __port_instance_type = TypeVar('__port_instance_type', bound='Port')
    """Type for correct IDE recognition and code completion for returned port subclasses"""

    _name_to_instance: dict[str, __port_instance_type] = {}
    """Name to instances registry filled by `__new__`"""

    _instances: list['Port'] = []
    """Class and subclasses instances filled by `__new__`"""

    def __init_subclass__(cls, **kwargs):
        cls._name_to_instance = {}
        cls._instances = []

    def __new__(cls, *args, **kwargs) -> __port_instance_type:
        uid = cls._force_uid or args[0]
        init_args = inspect.signature(cls.__init__).bind(cls, *args, **kwargs).arguments
        init_args.pop('self')

        try:
            instance = cls._name_to_instance[uid]
            if instance._inited_with_args == init_args:
                return instance
            else:
                raise ValueError(
                    f'Init arguments for consecutive declarations '
                    f'for {cls.__name__} "{uid}" must match: {instance._inited_with_args}'
                )
        except KeyError:
            instance = super().__new__(cls)
            instance._inited_with_args = init_args
            cls._name_to_instance[uid] = instance

            for parent_class in cls.mro()[:-1]:  # exclude `object`
                try:
                    parent_class._instances.append(instance)
                except AttributeError:  # not a Port subclass in mro
                    pass

            return instance

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

    calls: list[None | tuple[tuple, dict], list[SubscribedCall]]
    """Message match arguments and callables that will be called with matching incoming messages.
    `None` conditions matches any message."""

    _gui_color: str = 'green'
    _log_show_link: bool = True

    def __init__(self, uid: 'Hashable'):
        super().__init__(uid)
        self.calls: list[None | tuple[tuple, dict], list[SubscribedCall]] = []

        # workarounds for mkdocstrings issue #607
        self.calls: list[None | tuple[tuple, dict], list[SubscribedCall]]
        """Message match arguments and callables that will be called with matching incoming messages.
           `None` conditions matches any message."""

    def subscribe(
        self,
        *msg_matches_args: 'None | Container[Any] | Any',
        **msg_matches_kwargs: 'str, None | Container[Any] | Any',
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

        def wrapped_subscribe(
            callable_: 'Callable[[Msg], None] | Callable[[], None]',
        ) -> 'Callable':
            if msg_matches_args[0] in CallOn:
                conditions = msg_matches_args[0]
            elif (
                msg_matches_args[0] is callable_ or not msg_matches_args and not msg_matches_kwargs
            ):  # noqa: SIM108
                conditions = None
            else:
                conditions = (msg_matches_args, msg_matches_kwargs)

            call = SubscribedCall(conditions, callable_)

            try:
                call_list_for_conditions = next(
                    entry[1] for entry in self.calls if entry[0] == conditions
                )
                call_list_for_conditions.append(call)
            except StopIteration:
                self.calls.append((conditions, [call]))

            return callable_

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

        matched_calls = []
        not_matched_by_any_calls = []
        for conditions, call_list in self.calls:
            if conditions == CallOn.NOT_MATCHED_BY_ANY_CALL:
                not_matched_by_any_calls = call_list
            elif isinstance(conditions, str) and conditions in CallOn:
                continue
            elif conditions is None or msg.matches(*conditions[0], **conditions[1]):
                matched_calls.extend(call_list)

        calls = matched_calls or not_matched_by_any_calls

        msg_copies = [copy.copy(msg) for _ in range(len(calls))]
        midiscripter.shared.thread_executor.map(self.__call_worker, calls, msg_copies)

    @staticmethod
    def __call_worker(call: SubscribedCall, msg: 'Msg') -> None:
        """Function called in thread for each subscribed call and each received message.

        Notes:
            Not supposed to be overridden in subclasses.
            Supposed to be called from `_send_input_msg_to_calls` method.

        Args:
            call: Subscribed callable.
            msg: Received message to use as callable only argument.
        """
        log('Calling {call}', call=call)
        try:
            call(msg)
        except Exception as exc:
            log.red(''.join(traceback.format_exception(exc)))

    def _call_on_port_open(self) -> None:
        for conditions, call_list in self.calls:
            if conditions == CallOn.PORT_OPEN:
                for call in call_list:

                    def __call_runner() -> None:
                        try:
                            log('Running {call}', call=call)  # noqa: B023
                            call()  # noqa: B023
                        except Exception as exc:
                            log.red(''.join(traceback.format_exception(exc)))

                    midiscripter.shared.thread_executor.submit(__call_runner)

    def _open(self) -> None:
        """Prepares and activates the port

        Notes:
            Supposed to be overridden in subclasses.
            Should have a check against second opening.
            Must set `is_enabled` parameter to `True`.
            Must run `_call_on_port_open`.
        """
        self.is_enabled = True
        self._call_on_port_open()


class Output(Port):
    """Output port base class"""

    is_enabled: bool
    """`True` if port is ready to send messages"""

    _gui_color: str = 'magenta'
    _log_show_link: bool = True

    def send(self, msg: Msg) -> None:
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
            log.red("Can't send message {msg} - {output} is disabled!", msg=msg, output=self)
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
