import concurrent.futures
import os
import pathlib
import platform
import plistlib
import sys
import time
from collections.abc import Callable

import __main__

if platform.system() == 'Windows':
    import win32api
    import win32con
    import win32process
    import win32com.client


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
    """Exit and restart current script"""
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
def run_after_ports_opened(function: Callable[[], None]) -> Callable:
    """Decorator to subscribe a callable to run after all ports are opened at the script start

    Args:
        function: A callable with no arguments

    Returns:
        Subscribed callable.
    """
    if function not in run_after_ports_open_subscribed_calls:
        run_after_ports_open_subscribed_calls.append(function)
    return function


class AutostartManager:
    def __init__(self):
        self.__autostart_shortcut_prefix = 'MIDI Scripter - '
        self.__script_path = pathlib.Path(script_path).resolve()
        self.__shortcut_name = f'{self.__autostart_shortcut_prefix}{self.__script_path.stem}'

        if platform.system() == 'Windows':
            self.__autostart_dir_path = (
                pathlib.Path.home()
                / 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup'
            )
            __shortcut_extension = 'lnk'
        elif platform.system() == 'Linux' or platform.system() == 'Darwin':
            self.__autostart_dir_path = pathlib.Path.home() / '.config/autostart'
            __shortcut_extension = 'desktop'
        elif platform.system() == 'Darwin':
            self.__autostart_dir_path = pathlib.Path.home() / 'Library/LaunchAgents'
            __shortcut_extension = 'plist'

        self.__autostart_shortcut_path = (
            self.__autostart_dir_path / f'{self.__shortcut_name}.{__shortcut_extension}'
        )

    def _check_if_enabled(self) -> bool:
        return self.__autostart_shortcut_path.is_file()

    def __other_scripts_shortcuts(self) -> list[pathlib.Path]:
        return [
            path
            for path in self.__autostart_dir_path.iterdir()
            if (
                path.name.startswith(self.__autostart_shortcut_prefix)
                and path.is_file()
                and path != self.__autostart_shortcut_path.resolve()
            )
        ]

    def _check_if_other_scripts_present(self) -> bool:
        return bool(self.__other_scripts_shortcuts())

    def _enable(self) -> None:
        if platform.system() == 'Windows':
            shell = win32com.client.Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(self.__autostart_shortcut_path.resolve()))
            shortcut.Targetpath = str(pathlib.Path(sys.executable).parent / 'pythonw.exe')
            shortcut.WorkingDirectory = str(self.__script_path.parent.resolve())
            shortcut.Arguments = f'"{self.__script_path}" "--tray"'
            shortcut.save()

        elif platform.system() == 'Linux':
            desktop_file_content = (
                '[Desktop Entry]\n'
                f'Name={self.__shortcut_name}\n'
                f'Exec=python "{self.__script_path}" --tray\n'
                'Type=Application\n'
                'Terminal=false\n'
            )
            self.__autostart_shortcut_path.write_text(desktop_file_content)

        elif platform.system() == 'Darwin':  # Not tested, help needed
            plist_file_content = {
                'Label': self.__shortcut_name,
                'RunAtLoad': True,
                'ProgramArguments': [sys.executable, str(self.__script_path), '--tray'],
            }
            self.__autostart_shortcut_path.write_bytes(plistlib.dumps(plist_file_content))

    def _disable(self) -> None:
        self.__autostart_shortcut_path.unlink(missing_ok=True)

    def _disable_others(self) -> None:
        for path in self.__other_scripts_shortcuts():
            path.unlink()
