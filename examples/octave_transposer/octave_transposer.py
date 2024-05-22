from midiscripter import *

midi_keyboard = MidiIn('MIDI Keyboard')  # GUI will provide you with port names
proxy_output = MidiOut('To DAW')  # using loopMIDI virtual port for output

# GUI controls in a single line
octave_selector = GuiButtonSelectorH(('-2', '-1', '0', '+1', '+2'), select='0')


@midi_keyboard.subscribe  # decorated function will receive port's messages
def transpose(msg: MidiMsg) -> None:
    if msg.type == MidiType.NOTE_ON or msg.type == MidiType.NOTE_OFF:  # filter
        msg.data1 += 12 * int(octave_selector.selected_item_text)  # modify
    proxy_output.send(msg)  # route


if __name__ == '__main__':  # combine multiple scripts by importing them
    start_gui()  # opens helpful customizable GUI
