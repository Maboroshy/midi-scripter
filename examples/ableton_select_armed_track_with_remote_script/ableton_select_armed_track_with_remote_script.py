from midiscripter import *
from ableton_remote import *


ableton_in = AbletonIn('From Ableton Script')
ableton_out = AbletonOut('To Ableton Script')


@ableton_in.subscribe(AbletonEvent.TRACK_ARM, value=True)
def select_armed_track(msg: AbletonMsg) -> None:
    ableton_out.send(AbletonMsg(AbletonEvent.TRACK_SELECT, msg.index, True))


if __name__ == '__main__':
    start_gui()
