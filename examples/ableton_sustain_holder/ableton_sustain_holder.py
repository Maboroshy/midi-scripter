from midiscripter import *

piano = MidiIn('MIDI Keyboard')
midi_output_to_ableton = MidiOut('To DAW')
piano.passthrough_out(midi_output_to_ableton)

ableton_osc_in = OscIn(11001)
ableton_osc_out = OscOut(11000)


sustain_value = 0  # A global variable


@ableton_osc_in.subscribe(CallOn.PORT_INIT)
@ableton_osc_in.subscribe(address='/live/startup')
def start_listener() -> None:
    """Sets session record listener on script start or Ableton Live start while script is running"""
    ableton_osc_out.send(OscMsg('/live/song/start_listen/session_record_status'))


@piano.subscribe(MidiType.CONTROL_CHANGE, None, 64)
def get_midi_keyboard_sustain(msg: MidiMsg) -> None:
    """Puts sustain value to global variable"""
    global sustain_value
    sustain_value = msg.data2
    log.blue(f'Sustain: {str(sustain_value)}')


@ableton_osc_in.subscribe('/live/song/get/session_record_status', 1)
def session_record_started(_: OscMsg) -> None:
    """Sends sustain message to Ableton Live as soon as session record starts"""
    global sustain_value
    midi_output_to_ableton.send(ChannelMsg(MidiType.CONTROL_CHANGE, 1, 64, sustain_value))
    log.cyan(f'Session record started. Sending sustain: {str(sustain_value)}.')


if __name__ == '__main__':
    start_gui()
