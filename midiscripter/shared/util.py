import os
import platform
import sys

import midiscripter.shared

if platform.system() == 'Windows':
    import win32api
    import win32con
    import win32process


class SupressInitAutorun(type):
    """Metaclass that suppresses class instance `__init__` autorun to run it manually in `__new__`"""
    def __call__(cls, *args, **kwargs):
        return cls.__new__(cls, *args, **kwargs)


def restart_script() -> None:
    """Restart the current script"""
    os.spawnl(os.P_DETACH, sys.executable, 'python', midiscripter.shared.SCRIPT_PATH_STR)
    sys.exit(0)


def raise_current_process_cpu_priority() -> None:
    """Sets HIGH process priority in Windows for current python process"""
    if platform.system() == 'Windows':
        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)


def unbracket_args_and_kwargs(args: tuple, kwargs: dict) -> str:
    args_repr = ', '.join([repr(arg) for arg in args])
    kwargs_repr = ', '.join([f'{key}={repr(value)}' for key, value in kwargs.items()])
    return f'{args_repr}{", " if args and kwargs else ""}{kwargs_repr}'
