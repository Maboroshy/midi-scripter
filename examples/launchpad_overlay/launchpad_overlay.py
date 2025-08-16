from midiscripter import *


# Settings
SCENES_CC = (89, 79, 69, 59)
LPX_CHANNEL = 1
OVERLAY_CHANNEL = 2
SELECTED_SCENE_PAD_COLOR = 21


lpx = MidiIO('LPX MIDI')
daw_lpx = MidiIO('DAW LPX', virtual=True)
ableton_osc = OscIO(11001, 11000)

daw_lpx.passthrough_out(lpx)  # proxies all MIDI feedback back to LPX

overlay_toggle = GuiToggleButton('LPX OVERLAY ON', toggle_state=True)


@ableton_osc.subscribe(CallOn.PORT_INIT)
@ableton_osc.subscribe(address='/live/startup')
def start_selected_scene_listener(_: OscMsg = None) -> None:
    """Sets selected scene listener on script start or Ableton Live start"""
    ableton_osc.send(OscMsg('/live/view/start_listen/selected_scene'))


@lpx.subscribe
def input_proxy(msg: MidiMsg) -> None:
    """A general MIDI input proxy that make selected pads send OSC messages instead of MIDI"""
    if msg.matches(MidiType.CONTROL_CHANGE, LPX_CHANNEL, SCENES_CC) and overlay_toggle.toggle_state:
        ableton_osc.send(OscMsg('/live/view/set/selected_scene', SCENES_CC.index(msg.data1)))
    else:
        daw_lpx.send(msg)


@ableton_osc.subscribe('/live/view/get/selected_scene')
def feedback_from_osc(msg: OscMsg) -> None:
    """Lights up selected scene pad based on selected scene listener OSC input"""
    for index, cc in enumerate(SCENES_CC):
        value = SELECTED_SCENE_PAD_COLOR if index == msg.data else 0
        lpx.send(MidiMsg(MidiType.CONTROL_CHANGE, LPX_CHANNEL, cc, value))


if __name__ == '__main__':
    start_gui()
