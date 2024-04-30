from midiscripter import *

midi_input_from_ableton = MidiIn('From DAW')
midi_output_to_ableton = MidiOut('To DAW')

ableton_osc_in = OscIn(11001)
ableton_osc_out = OscOut(11000)


sustain_value = 0  # A global variable


@run_after_ports_opened
@ableton_osc_in.subscribe
def start_listener(msg: OscMsg = None) -> None:
    """Sets session record listener on script start or Ableton Live start while script is running"""
    if msg is None or msg.address == '/live/startup':
        ableton_osc_out.send(OscMsg('/live/song/start_listen/session_record_status'))


@midi_input_from_ableton.subscribe
def get_midi_keyboard_sustain(msg: MidiMsg) -> None:
    """Puts sustain value to global variable"""
    if msg.matches(MidiType.CONTROL_CHANGE, None, 64):
        global sustain_value
        sustain_value = msg.data2
        log.blue(f'Sustain: {str(sustain_value)}')


@ableton_osc_in.subscribe
def session_record_started(msg: OscMsg) -> None:
    """Sends sustain message to Ableton Live as soon as session record starts"""
    if msg.matches('/live/song/get/session_record_status', 1):
        global sustain_value
        midi_output_to_ableton.send(ChannelMsg(MidiType.CONTROL_CHANGE, 1, 64, sustain_value))
        log.blue(f'Session record started. Sending sustain: {str(sustain_value)}.')


if __name__ == '__main__':
    start_gui()
