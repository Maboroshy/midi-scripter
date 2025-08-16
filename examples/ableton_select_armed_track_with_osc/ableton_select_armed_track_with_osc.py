from midiscripter import *


ableton_osc = OscIO(11001, 11000)

reset_track_lister_button = GuiButton('Reset track listener')


@ableton_osc.subscribe(CallOn.PORT_INIT)
@reset_track_lister_button.subscribe(GuiEvent.TRIGGERED)
@ableton_osc.subscribe(address='/live/startup')
def set_armed_track_listener() -> None:
    """Sets armed track listener on script start or Ableton Live start"""
    try:
        track_count = ableton_osc.query('/live/song/get/num_tracks')
        for track_index in range(track_count):
            ableton_osc.send(OscMsg('/live/track/start_listen/arm', track_index))
    except TimeoutError:
        log.red('Ableton OSC is not running')


@ableton_osc.subscribe('/live/track/get/arm')
def select_first_armed_track(msg: OscMsg) -> None:
    track_index, is_armed = msg.data
    if is_armed:
        ableton_osc.send(OscMsg('/live/view/set/selected_track', track_index))
        log.blue(f'Selecting track {track_index}')


if __name__ == '__main__':
    start_gui()
