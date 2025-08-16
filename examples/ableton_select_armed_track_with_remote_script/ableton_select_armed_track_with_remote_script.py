from midiscripter import *


ableton = AbletonIO('Ableton Live', virtual=True)


@ableton.subscribe(AbletonEvent.TRACK_ARM, value=True)
def select_armed_track(msg: AbletonMsg) -> None:
    ableton.send(AbletonMsg(AbletonEvent.TRACK_SELECT, msg.index, True))


if __name__ == '__main__':
    start_gui()
