import subprocess

from midiscripter import *


# Settings
DAW_PATH_STR = r'C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe'
DAW_PROJECT_PATH_STR = r'C:\Users\user\Music\Ableton Project\song.als'
DAW_START_MIDI_MSG_CONDITIONS = (MidiType.CONTROL_CHANGE, 1, 1, 0)


midi_controller = MidiIn('MIDI Controller')


@midi_controller.subscribe(*DAW_START_MIDI_MSG_CONDITIONS)
def daw_launcher(msg: MidiMsg) -> None:
    log.green('Running DAW...')
    subprocess.Popen(
        [DAW_PATH_STR, DAW_PROJECT_PATH_STR],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
    )


if __name__ == '__main__':
    start_gui()
