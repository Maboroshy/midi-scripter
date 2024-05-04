import pathlib
import platform
import plistlib
import sys

if platform.system() == 'Windows':
    import win32com.client

import midiscripter.base.shared


__autostart_shortcut_prefix = 'MIDI Scripter - '
__script_path = pathlib.Path(midiscripter.base.shared.script_path).resolve()
__shortcut_name = f'{__autostart_shortcut_prefix}{__script_path.stem}'


if platform.system() == 'Windows':
    __autostart_dir_path = (
        pathlib.Path.home() / 'AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup'
    )
    __shortcut_extension = 'lnk'
elif platform.system() == 'Linux' or platform.system() == 'Darwin':
    __autostart_dir_path = pathlib.Path.home() / '.config/autostart'
    __shortcut_extension = 'desktop'
elif platform.system() == 'Darwin':
    __autostart_dir_path = pathlib.Path.home() / 'Library/LaunchAgents'
    __shortcut_extension = 'plist'

__autostart_shortcut_path = __autostart_dir_path / f'{__shortcut_name}.{__shortcut_extension}'


def _check_if_enabled() -> bool:
    return __autostart_shortcut_path.is_file()


def __other_scripts_shortcuts() -> list[pathlib.Path]:
    return [
        path
        for path in __autostart_dir_path.iterdir()
        if (
            path.name.startswith(__autostart_shortcut_prefix)
            and path.is_file()
            and path != __autostart_shortcut_path.resolve()
        )
    ]


def _check_if_other_scripts_present() -> bool:
    return bool(__other_scripts_shortcuts())


def _enable():
    if platform.system() == 'Windows':
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(__autostart_shortcut_path.resolve()))
        shortcut.Targetpath = str(pathlib.Path(sys.executable).parent / 'pythonw.exe')
        shortcut.WorkingDirectory = str(__script_path.parent.resolve())
        shortcut.Arguments = f'"{__script_path}" "--tray"'
        shortcut.save()

    elif platform.system() == 'Linux':
        desktop_file_content = (
            '[Desktop Entry]\n'
            f'Name={__shortcut_name}\n'
            f'Exec=python "{__script_path}" --tray\n'
            'Type=Application\n'
            'Terminal=false\n'
        )
        __autostart_shortcut_path.write_text(desktop_file_content)

    elif platform.system() == 'Darwin':  # Not tested, help needed
        plist_file_content = {
            'Label': __shortcut_name,
            'RunAtLoad': True,
            'ProgramArguments': [sys.executable, str(__script_path), '--tray'],
        }
        __autostart_shortcut_path.write_bytes(plistlib.dumps(plist_file_content))


def _disable():
    __autostart_shortcut_path.unlink(missing_ok=True)


def _disable_others():
    for path in __other_scripts_shortcuts():
        path.unlink()
