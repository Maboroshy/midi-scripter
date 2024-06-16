import concurrent.futures
import os
import platform
import sys
import time

import __main__

if platform.system() == 'Windows':
    import win32api
    import win32con
    import win32process

from shared.autostart import AutostartManager


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
