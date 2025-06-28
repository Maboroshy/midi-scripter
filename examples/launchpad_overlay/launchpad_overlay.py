from midiscripter import *


# Settings
SCENES_CC = (89, 79, 69, 59)
LPX_CHANNEL = 1
OVERLAY_CHANNEL = 2
SELECTED_SCENE_PAD_COLOR = 21

send_to_overlay_msg_conditions = (MidiType.CONTROL_CHANGE, LPX_CHANNEL, SCENES_CC)


from_LPX = MidiIn('LPX MIDI')
to_LPX = MidiOut('LPX MIDI')

to_daw_lpx = MidiOut('To DAW LPX', virtual=True)
from_daw_lpx = MidiIn('From DAW LPX', virtual=True)

ableton_osc_in = OscIn(11001)
ableton_osc_out = OscOut(11000)

from_daw_lpx.passthrough_out(to_LPX)  # proxies all MIDI feedback back to LPX

overlay_toggle = GuiToggleButton('LPX OVERLAY ON', toggle_state=True)


@ableton_osc_in.subscribe(CallOn.PORT_INIT)
@ableton_osc_in.subscribe(address='/live/startup')
def start_selected_scene_listener(_: OscMsg = None) -> None:
    """Sets selected scene listener on script start or Ableton Live start while script is running"""
    ableton_osc_out.send(OscMsg('/live/view/start_listen/selected_scene'))


@from_LPX.subscribe
def input_proxy(msg: MidiMsg) -> None:
    """A general MIDI input proxy that make selected pads send OSC messages instead of MIDI"""
    if msg.matches(*send_to_overlay_msg_conditions) and overlay_toggle.toggle_state:
        ableton_osc_out.send(OscMsg('/live/view/set/selected_scene', SCENES_CC.index(msg.data1)))
    else:
        to_daw_lpx.send(msg)


@ableton_osc_in.subscribe('/live/view/get/selected_scene')
def feedback_from_osc(msg: OscMsg) -> None:
    """Lights up selected scene pad based on selected scene listener OSC input"""
    for index, cc in enumerate(SCENES_CC):
        value = SELECTED_SCENE_PAD_COLOR if index == msg.data else 0
        to_LPX.send(MidiMsg(MidiType.CONTROL_CHANGE, LPX_CHANNEL, cc, value))


if __name__ == '__main__':
    start_gui()
