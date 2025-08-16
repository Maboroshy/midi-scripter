import pathlib
import platform
import shutil


def get_ableton_remote_script_path() -> pathlib.Path | None:
    try:
        if platform.system() == 'Windows':
            _ableton_dir = pathlib.Path.home() / 'AppData/Roaming/Ableton'
            ableton_remote_script_dir = (
                sorted(_ableton_dir.glob('Live 1*'))[-1]
                / 'Preferences/User Remote Scripts/MIDI_Scripter'
            )
        elif platform.system() == 'Darwin':
            _ableton_dir = pathlib.Path.home() / 'Library/Preferences/Ableton'
            ableton_remote_script_dir = (
                sorted(_ableton_dir.glob('Live 1*'))[-1] / 'User Remote Scripts/MIDI_Scripter'
            )
        else:
            return None

        return ableton_remote_script_dir
    except (FileNotFoundError, IndexError):
        return None


def install_ableton_remote_script() -> bool:
    ableton_remote_script_path = get_ableton_remote_script_path()

    if not ableton_remote_script_path:
        return False

    try:
        import midiscripter

        remote_script_file_path = (
            pathlib.Path(midiscripter.__file__).parent / 'ableton_remote/UserConfiguration.txt'
        )
        ableton_remote_script_path.mkdir(exist_ok=True)
        shutil.copy(remote_script_file_path, ableton_remote_script_path / 'UserConfiguration.txt')
        return True
    except FileNotFoundError:
        return False
