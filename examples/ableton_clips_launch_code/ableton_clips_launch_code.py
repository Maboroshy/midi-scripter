import sys

from midiscripter import *


ableton_osc = OscIO(11001, 11000)

reset_clip_lister_button = GuiButton('Reset clip listener')


@ableton_osc.subscribe(CallOn.PORT_INIT)
@reset_clip_lister_button.subscribe(GuiEvent.TRIGGERED)
@ableton_osc.subscribe(address='/live/startup')
def set_clip_fire_listener() -> None:
    """Sets playing clip listener on script start or Ableton Live start"""
    try:
        track_count = ableton_osc.query('/live/song/get/num_tracks')
        for track_index in range(track_count):
            ableton_osc.send(OscMsg('/live/track/start_listen/playing_slot_index', track_index))
    except TimeoutError:
        log.red('Ableton OSC is not running')


@ableton_osc.subscribe('/live/track/get/playing_slot_index')
def clip_fired(msg: OscMsg) -> None:
    """Launches current module's function named like the first word of launched clip's name and other words as args"""
    if msg.data[1] == -1:  # no clip is playing
        return

    fired_clip_name = ableton_osc.query('/live/clip/get/name', msg.data)[2]

    if not fired_clip_name:
        return

    clip_name_words = fired_clip_name.split()
    function_name = clip_name_words[0].lower()
    function_args = [int(word) if word.isnumeric() else word for word in clip_name_words[1:]]

    try:
        getattr(sys.modules[__name__], function_name)(*function_args)
    except AttributeError:  # no function for clip name
        pass


def clip_1() -> None:
    log.green('Launched "clip_1"')


def clip_2(arg: int) -> None:
    log.green(f'Launched "clip_2" with arg: {arg}')


if __name__ == '__main__':
    start_gui()
