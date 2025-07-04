import music21.chord
import music21.key
import music21.note
import music21.roman

from midiscripter import *


midi_input_from_daw = MidiIn('From DAW', virtual=True)  # MIDI input from (after) DAW

pressed_notes_midi_data = []  # A global variable

# Setting GUI widgets
root_selector = GuiButtonSelectorV(('C', 'D', 'E', 'F', 'G', 'A', 'B'), select='C')
root_alteration_selector = GuiButtonSelectorV(('b', '♮', '#'), select='♮')
mode_selector = GuiButtonSelectorV(('Major', 'Minor'), select='Major')
buttons_layout = GuiWidgetLayout('Settings', [root_selector, [root_alteration_selector, 
                                                              mode_selector]])  # fmt: skip
chord_degree_label = GuiText('Degree')
chord_name_label = GuiText('Chord Name')
labels_layout = GuiWidgetLayout('Info', chord_degree_label, 
                                        chord_name_label)  # fmt: skip


@midi_input_from_daw.subscribe((MidiType.NOTE_ON, MidiType.NOTE_OFF))
def show_chord_info(msg: MidiMsg) -> None:
    """Gathers pressed notes and prints chord info to GUI widgets"""
    global pressed_notes_midi_data

    # Clear chord on first note off
    if msg.type == MidiType.NOTE_OFF:
        pressed_notes_midi_data = []

    if msg.type == MidiType.NOTE_ON:
        # Gather pressed notes data
        pressed_notes_midi_data.append(msg.data1)
        if len(pressed_notes_midi_data) < 3:  # Wait for chord
            return

        # Get settings from GUI selector widgets
        if root_alteration_selector.selected_item_text == '♮':
            key = root_selector.selected_item_text
        else:
            key = root_selector.selected_item_text + root_alteration_selector.selected_item_text

        # Get chord and key into music21 library objects
        chord = music21.chord.Chord(pressed_notes_midi_data)
        key = music21.key.Key(key, mode_selector.selected_item_text)

        # Print info to GUI widgets
        chord_name_label.content = chord.pitchedCommonName
        chord_degree_label.content = music21.roman.romanNumeralFromChord(chord, key).figure.upper()

        # If the chord is out of key its degree will be printed red
        if not all(key.getScaleDegreeFromPitch(pitch) for pitch in chord.pitches):
            chord_degree_label.color = 'red'
        else:
            chord_degree_label.color = 'black'


if __name__ == '__main__':
    start_gui()
