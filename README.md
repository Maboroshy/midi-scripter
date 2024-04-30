# MIDI Scripter

MIDI Scripter is a framework for scripting MIDI, keyboard and Open Sound Control (OSC) input and output with a few lines of Python code.

MIDI Scripter is intended for digital audio workstation (DAW) controls scripting but can also be used for general input conversion and automation. It fits where controller mappings are not enough but rewriting DAW controller integration is too much. 

An octave transposer with GUI controls in 10 lines of code:

``` python
from midiscripter import *  # safe * import with no bloat

midi_keyboard = MidiIn('Port name')  # GUI will provide you with port names
proxy_output = MidiOut('loopMIDI Port') # using loopMIDI virtual port for output

# GUI control in a single line, many widget available, custom widgets supported
octave_selector = GuiButtonSelectorH(('-2', '-1', '0', '+1', '+2'), select='0')

@midi_keyboard.subscribe  # decorated function will receive port's messages
def transpose(msg: MidiMsg) -> None:
	if msg.type == MidiType.NOTE_ON or msg.type == MidiType.NOTE_OFF:  # filter
		msg.data1 += 12 * int(octave_selector.selected_item_text)  # modify
		proxy_output.send(msg)  # route

if __name__ == '__main__':  # combine multiple scripts by importing them
	start_gui()  # opens helpful customizable GUI
```

![Screenshot](https://github.com/Maboroshy/midi-scripter/blob/master/examples/octave_transposer/screenshot.png?raw=true)

[Scripting guide and API documentation available](https://maboroshy.github.io/midi-scripter)

Easy tasks for MIDI Scripter:  
1. Filter, modify and route MIDI, OSC and keyboard messages in any way.  
2. Map MIDI, OSC and keyboard to each other.  
3. Map any Python code to input message.  
4. Make extra "shift" keys to multiply MIDI controls.  
5. Organize mappings into sets / scenes with GUI controls.  
6. Make an extra overlay mappings on top of MIDI controller's default DAW integration by using proxy.  

Complex tasks for MIDI Scripter:
1. Create and map complex macros involving multiple hardware or virtual MIDI controllers.
2. Make custom sequencer or MIDI input generator.
3. Make music education ot trainer GUI application based on MIDI input.

Currently MIDI Scripter is at "beta" development stage. It's fully functional but needs some more testing. It targets only Windows for now but Linux and macOS support will follow.

## Installation
1. [Python 3.11+](https://www.python.org/downloads/) with "Add python.exe to PATH" option.
2. [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) for virtual MIDI output ports on Windows.
3. `pip install midiscripter` in console.

## Setup
Run loopMIDI and add virtual ports you want to send MIDI messages. You can enable its autostart option.

Enable virtual MIDI output ports as MIDI inputs in DAW. 

## Quick Start
1. Paste [script template](examples/script_template.py) to Python IDE or plain text editor. IDE is greatly recommended.
2. Run unchanged template script from IDE or by `python .\script_template.py` to open GUI for more info on available ports and their input.
3. Turn on the ports' checkboxes to enable them and watch the log for input messages.
4. Click on port names and messages to copy their declarations to the clipboard. Paste the declarations to your script.
5. Write the functions you need. Subscribe them to messages with `@input_port.subscribe` decorator. Use `log('messages')` for debugging. Use `output_port.send(msg)` to send modified or created messages from a function.
6. Restart the script from GUI.
