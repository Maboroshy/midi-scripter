import collections
import contextlib
import copy
import enum
import inspect
import itertools
import traceback
from typing import TYPE_CHECKING, TypeVar, ClassVar, Any
from collections.abc import Sequence

import midiscripter.shared
import midiscripter
from midiscripter.logger import log
from midiscripter.base.msg_base import Msg

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Container


class CallOn(enum.StrEnum):
    """Special conditions to use as `@input_port.subscribe(condition)`"""

    NOT_MATCHED_BY_ANY_CALL = 'NOT MATCHED BY ANY CALLS'
    """Call when a message is not matched by any other call"""

    PORT_INIT = 'PORT INIT'
    """Call after port is initially opened"""


@contextlib.contextmanager
def _all_opened() -> None:
    for port in itertools.chain(Input._subclass_instances, Output._subclass_instances):
        if not port.is_opened:
            port._open()

    for input_port in Input._subclass_instances:
        input_port._call_on_init()

    yield

    for port in Port._subclass_instances:
        if port.is_opened:
            port._close()

    log._flush()
    log._flushing_is_enabled = False
    midiscripter.shared.thread_executor.shutdown(wait=False, cancel_futures=True)


class SubscribedCall:
    """Wrapper object created for subscribed callable"""

    conditions: None | tuple[tuple, dict]
    """Message match conditions for call"""

    statistics: collections.deque
    """Last 20 call execution durations in milliseconds"""

    _log_color: str | None = 'cyan'
    _log_show_link: bool = False

    def __init__(
        self, conditions: 'None | tuple[tuple, dict]', callable_: 'Callable', owner: 'Subscribable'
    ):
        self.conditions = conditions
        self.statistics = collections.deque(maxlen=20)
        self.owner = owner
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

    def _print_exception_to_log(self, exc: Exception) -> None:
        traceback_text = ''.join(traceback.format_exception(exc, limit=-2)[1:])
        log.red(
            'Calling {call} subscribed to {port} raised exception:\n{traceback_text}',
            call=self,
            port=self.owner,
            traceback_text=traceback_text,
        )


class Subscribable:
    """Base class for object that calls can subscribe to"""

    _calls: list[None | CallOn | tuple[tuple, dict], list[SubscribedCall]]
    """Message match arguments and callables that will be called with matching incoming messages.
    `None` conditions matches any message."""

    __init_called: bool = False

    def __init__(self):
        self._calls: list[tuple[None | CallOn | tuple[tuple, dict], list[SubscribedCall]]] = []

        # workarounds for mkdocstrings issue #607
        self._calls: list[tuple[None | CallOn | tuple[tuple, dict], list[SubscribedCall]]]
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

        2. If condition equals the message's attribute value it matches the attribute.

        3. If condition is a container (list, tuple) and contains the message's attribute value,
        it matches the attribute.

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

            call = SubscribedCall(conditions, callable_, self)

            try:
                call_list_for_conditions = next(
                    entry[1] for entry in self._calls if entry[0] == conditions
                )
                call_list_for_conditions.append(call)
            except StopIteration:
                self._calls.append((conditions, [call]))

            return callable_

        if callable(msg_matches_args[0]):
            return wrapped_subscribe(msg_matches_args[0])

        return wrapped_subscribe

    def _send_input_msg_to_calls(self, msg: 'Msg') -> None:
        """Sends received messages to subscribed calls.

        Notes:
            Not supposed to be overridden in subclasses.
            Supposed to be called from the listener thread started
            by the subclass implementation of `open` method.

        Args:
            msg: A message received by the input port to send to its registered calls.
        """
        log._msg_received(self, msg)

        matched_calls = []
        not_matched_by_any_calls = []
        for conditions, call_list in self._calls:
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
        log._call_made(call)
        try:
            call(msg)
        except Exception as exc:
            call._print_exception_to_log(exc)

    def _call_on_init(self) -> None:
        """Called after input port is opened for the first time.

        Notes:
            Not supposed to be overridden in subclasses.
        """
        if self.__init_called:
            return
        self.__init_called = True

        for conditions, call_list in self._calls:
            if conditions == CallOn.PORT_INIT:
                for call in call_list:
                    midiscripter.shared.thread_executor.submit(self.__call_worker, call, Msg(''))


class Port:
    """Port base class.

    Notes:
        Port declarations with the same arguments will return the same instance port (singleton).
    """

    is_opened: bool = False
    """`True` if port is listening messages / ready to send messages"""

    _forced_uid: ClassVar[None | str] = None
    """UID override for classes that have can have only one instance per whole class,
       like keyboard port classes. Object for these classes are declared without arguments.
    """

    _wrapped_in: 'list[MultiPort]'
    """The MultiPort instances the port is wrapped in"""

    _is_virtual: bool = False
    """Is the port virtual. Used by MIDI ports."""

    __inited_with_args: dict
    """The arguments the port singleton was initialized with. Used by `__new__`."""

    __repr: str
    """Saved repr prepared by `__new__`"""

    __port_instance_type = TypeVar('__port_instance_type', bound='Port')
    """Type for correct IDE recognition and code completion for returned port subclasses"""

    _uid_to_instance: dict[str, __port_instance_type] = {}
    """Name to instances registry filled by `__new__`"""

    _class_instances: list[__port_instance_type] = []
    """Class instances filled by `__new__`"""

    _subclass_instances: list[__port_instance_type] = []
    """Subclasses instances filled by `__new__`"""

    _log_description: str = 'port'
    _log_color: str | None = None
    _log_show_link: bool = True

    def __init_subclass__(cls, **kwargs):
        cls._uid_to_instance = {}
        cls._class_instances = []
        cls._subclass_instances = []

    def __new__(cls, *args, **kwargs) -> __port_instance_type:
        init_bound_arguments = inspect.signature(cls.__init__).bind(cls, *args, **kwargs)
        init_bound_arguments.apply_defaults()
        uid = cls._forced_uid or init_bound_arguments.args[1]  # second after `self`
        init_args = init_bound_arguments.arguments
        init_args.pop('self')  # popping `arguments` breaks `.args`, keep the order

        try:
            instance = cls._uid_to_instance[uid]
            if instance.__inited_with_args == init_args:
                return instance
            else:
                raise ValueError(
                    f'Init arguments for consecutive declarations '
                    f'for {cls.__name__} "{uid}" must match: {instance.__inited_with_args}'
                )
        except KeyError:
            instance = super().__new__(cls)
            instance.__inited_with_args = init_args
            cls._uid_to_instance[uid] = instance

            args_repr = ', '.join([repr(arg) for arg in args])
            kwargs_repr = ', '.join([f'{key}={repr(value)}' for key, value in kwargs.items()])
            instance.__repr = (
                f'{cls.__name__}({args_repr}{", " if args and kwargs else ""}{kwargs_repr})'
            )

            cls._class_instances.append(instance)

            parent_class: Port
            for parent_class in cls.mro()[1:-1]:  # exclude `object`
                try:
                    parent_class._subclass_instances.append(instance)
                except AttributeError:  # not a Port subclass in mro
                    pass

            return instance

    def __init__(self, uid: 'Hashable | None' = None):
        """
        Args:
            uid: Port's unique ID
        """
        self._uid = uid or self._forced_uid
        self._wrapped_in = []

        self.is_opened: bool  # workaround for mkdocstrings issue #607
        """`True` if port is listening messages / ready to send messages"""

    def __repr__(self):
        return self.__repr

    def __str__(self):
        return str(self._uid)

    @property
    def _is_available(self) -> bool:
        """Port is available and can be opened"""
        return True

    def _open(self) -> None:
        """Prepares and activates the port

        Notes:
            Supposed to be overridden in subclasses.
            Must set `is_opened` parameter to `True` on success.
        """
        self.is_opened = True
        log._port_open(self, True)

    def _close(self) -> None:
        """Deactivates the port.

        Notes:
            Supposed to be overridden in subclasses.
            Must set `is_opened` parameter to `False`.
        """
        self.is_opened = False
        log._port_close(self, True)


class Input(Subscribable, Port):
    """Input port base class"""

    _log_description: str = 'input'
    _log_color: str | None = 'green'

    def __init__(self, uid: 'Hashable | None' = None):
        Port.__init__(self, uid)
        Subscribable.__init__(self)


class Output(Port):
    """Output port base class"""

    _log_description: str = 'output'
    _log_color: str | None = 'magenta'

    def send(self, msg: Msg) -> None:
        """Send message using the output port.

        Args:
            msg: Message to send.

        Notes:
            Supposed to be overridden in subclasses.
            Should use `self._validate_msg_send(msg)` before sending
            and `log._msg_sent(self, msg)` after.
        """
        if not self._validate_msg_send(msg):
            return

        raise NotImplementedError

        # noinspection PyUnreachableCode
        log._msg_sent(self, msg)

    def _validate_msg_send(self, msg: 'Msg') -> bool:
        if not self.is_opened:
            log.red("Can't send message {msg} - {output} is disabled!", msg=msg, output=self)
            return False
        return True


class MultiPort(Port):
    """
    Multiport wrapper class. Combines [`Input`][midiscripter.base.port_base.Input]
    and [`Output`][midiscripter.base.port_base.Output] ports to a single i/o port.
    """

    _log_description: str = 'i/o port'

    def __init__(
        self,
        uid: str,
        input_ports: 'Input | Sequence[Input]',
        output_ports: 'Output | Sequence[Output]',
    ):
        """
        Args:
            uid: Port's unique ID
            input_ports: input ports to wrap
            output_ports: output ports to wrap
        """
        super().__init__(uid)
        self._input_ports = input_ports if isinstance(input_ports, Sequence) else [input_ports]
        self._output_ports = output_ports if isinstance(output_ports, Sequence) else [output_ports]
        self._wrapped_ports = self._input_ports + self._output_ports

        for port in self._wrapped_ports:
            port._wrapped_in.append(self)

    def _open(self) -> None:
        for port in self._wrapped_ports:
            if not port.is_opened:
                port._open()

    def _close(self) -> None:
        for port in self._wrapped_ports:
            if port.is_opened:
                port._close()

    @property
    def _calls(self) -> list[tuple[None | CallOn | tuple[tuple, dict], list[SubscribedCall]]]:
        calls = []
        for input_port in self._input_ports:
            calls.extend(input_port._calls)
        return calls

    @property
    def is_opened(self) -> bool:
        return all(port.is_opened for port in self._wrapped_ports)

    def subscribe(
        self,
        *msg_matches_args: 'None | Container[Any] | Any',
        **msg_matches_kwargs: 'str, None | Container[Any] | Any',
    ) -> 'Callable':
        """Decorator to subscribe a callable to all the wrapped inputs' messages.

        Decorator without arguments subscribes a callable to all the input's messages.

        Decorator with arguments subscribes a callable to the input's messages
        that match conditions set by arguments.
        It works the same way as message's [`matches`][midiscripter.base.msg_base.Msg.matches] method:

        1. If condition is `None` or omitted it matches anything.

        2. If condition equals the message's attribute value it matches the attribute.

        3. If condition is a container (list, tuple) and contains the message's attribute value,
        it matches the attribute.

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
        if not self._input_ports:
            raise AttributeError(f"Can't subscribe to {self}. It has no input ports.")

        call = None
        for input_port in self._input_ports:
            call = input_port.subscribe(*msg_matches_args, **msg_matches_kwargs)
        return call

    def send(self, msg: Msg) -> None:
        """Send message using wrapped output ports

        Args:
            msg: Message to send.
        """
        for output_port in self._output_ports:
            output_port.send(msg)
