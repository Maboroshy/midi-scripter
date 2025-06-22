from midiscripter import *


ableton_osc_in = OscIn(11001)
ableton_osc_out = OscOut(11000)
osc_query = OscQueryMaker(ableton_osc_in, ableton_osc_out)

reset_track_lister_button = GuiButton('Reset track listener')


@ableton_osc_in.subscribe(CallOn.PORT_INIT)
@reset_track_lister_button.subscribe(GuiEvent.TRIGGERED)
@ableton_osc_in.subscribe(address='/live/startup')
def set_armed_track_listener() -> None:
    """Sets session record listener on script start or Ableton Live start while script is running"""
    try:
        track_count = osc_query.query('/live/song/get/num_tracks')
        for track_index in range(track_count):
            ableton_osc_out.send(OscMsg('/live/track/start_listen/arm', track_index))
    except TimeoutError:
        log.red('Ableton OSC is not running')


@ableton_osc_in.subscribe('/live/track/get/arm')
def select_first_armed_track(msg: OscMsg) -> None:
    track_index, is_armed = msg.data
    if is_armed:
        ableton_osc_out.send(OscMsg('/live/view/set/selected_track', track_index))
        log.blue(f'Selecting track {track_index}')


if __name__ == '__main__':
    start_gui()
