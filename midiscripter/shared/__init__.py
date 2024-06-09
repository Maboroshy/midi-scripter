import concurrent.futures
import os
import platform
import sys
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import __main__

if platform.system() == 'Windows':
    import win32api
    import win32con
    import win32process

from midiscripter.base.port_base import SubscribedCall
from shared.autostart import AutostartManager

if TYPE_CHECKING:
    from midiscripter.base.msg_base import Msg


try:
    script_path = __main__.__file__
except AttributeError:  # in subprocess or IPython
    script_path = None


thread_executor = concurrent.futures.ThreadPoolExecutor(100)


_precise_time_delta = time.time() - time.perf_counter()


def precise_epoch_time() -> float:
    """current time in epoch format with nanosecond precision"""
    return _precise_time_delta + time.perf_counter()


def restart_script() -> None:
    """Exit and restart the current script"""
    os.execv(sys.executable, ['python', script_path])
    exit(0)


def _raise_current_process_cpu_priority() -> None:
    """Sets HIGH process priority in Windows for current python process"""
    if platform.system() == 'Windows':
        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)


run_after_ports_open_subscribed_calls = []


# A Decorator
def run_after_ports_opened(callable_: 'Callable[[Msg], None] | Callable[[], None]') -> Callable:
    """Decorator to subscribe a callable to run after all ports are opened at the script start


    Args:
        callable_: A callable with single argument or no arguments.

    Notes:
        Single argument callables are called with dummy message object.

        That hack allows the same callable to be also used for port's subscription
        where the message is real.

    Returns:
        Subscribed callable.
    """
    run_after_ports_open_subscribed_calls.append(SubscribedCall(None, callable_))
    return callable_
