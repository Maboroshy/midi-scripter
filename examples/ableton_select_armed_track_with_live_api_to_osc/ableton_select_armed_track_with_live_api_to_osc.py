from midiscripter import *
from midiscripter import CallOn


live_api_osc = OscIO(7500, 7400)

track_ids = []


@live_api_osc.subscribe(CallOn.PORT_INIT)
@live_api_osc.subscribe(address='/live_set/startup')
def set_observers() -> None:
    live_api_osc.send(OscMsg('/live_set/tracks/observe', 1))
    live_api_osc.send(OscMsg('/live_set/tracks/*/arm/observe', 1))


@live_api_osc.subscribe('/live_set/tracks')
def get_tracks_ids(msg: OscMsg) -> None:
    global track_ids
    track_ids = [item for item in msg.data if item != 'id']


@live_api_osc.subscribe(Glob('/live_set/tracks/*/arm'), 1)
def select_armed_track(msg: OscMsg) -> None:
    track_index = int(msg.address.split('/')[3])
    log.blue(f'Selecting track {track_index}')
    live_api_osc.send(OscMsg('/live_set/view/selected_track', ('id', track_ids[track_index])))


if __name__ == '__main__':
    start_gui()
