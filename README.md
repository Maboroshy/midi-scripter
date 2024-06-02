# <img src="docs/icon.svg" width="24"/> MIDI Scripter

MIDI Scripter is a framework for filtering, modifying, routing and any other
scripting for MIDI, Open Sound Control (OSC), keyboard and mouse input and
output with Python.

MIDI Scripter listens to the input ports and feeds incoming messages to
subscribed callables (functions, methods, etc.). These callables or any
other Python code can send modified or created messages with output ports. 
MIDI Scripter can act as a proxy to filter, transform and convert the input.

MIDI Scripter includes customizable GUI for message logging, coding
assistance and GUI controls and indicators to use in scripts.

An octave transposer with GUI controls in 10 lines of code:

``` python
from midiscripter import *

midi_keyboard = MidiIn('MIDI Keyboard')  # GUI will provide you with port names
proxy_output = MidiOut('To DAW')  # using virtual proxy port for output

# GUI control in a single line
octave_selector = GuiButtonSelectorH(('-2', '-1', '0', '+1', '+2'), select='0')

@midi_keyboard.subscribe  # decorated function will receive port's messages
def transpose(msg: MidiMsg) -> None:
	if msg.type == MidiType.NOTE_ON or msg.type == MidiType.NOTE_OFF:  # filter
		msg.data1 += 12 * int(octave_selector.selected_item_text)  # modify
	proxy_output.send(msg)  # route

if __name__ == '__main__':  # combine multiple scripts by importing them
	start_gui()  # opens helpful customizable GUI
```

![Screenshot after some widget arrangement](https://github.com/Maboroshy/midi-scripter/blob/master/examples/octave_transposer/screenshot.png?raw=true)

[You can find more examples here.](https://github.com/Maboroshy/midi-scripter/tree/master/examples)

[Overview and API documentation available.](https://maboroshy.github.io/midi-scripter)

The average measured roundtrip latency for the script above is less than 0.25 
milliseconds.

Currently MIDI Scripter is at "beta" development stage. It's fully
functional but needs more user feedback. It works on Windows and Linux and
should work on macOS.

## What it can do

The basics:

- Receive MIDI, OSC, keyboard and mouse input messages.
- Filter, modify and do anything Python can with the messages.
- Send out modified or generated MIDI, OSC, keyboard and mouse messages.

For performance MIDI setups:

- Make extra banks and layers to multiply MIDI controls.
- Organize mappings into sets / scenes with GUI dashboard.
- Make an extra overlay mappings on top of MIDI controller's DAW integration by
  using proxies.

For software control and automation:

- Map or convert the messages to each other with any conditions and logic.
- Use MIDI controllers or keyboard shortcuts to run any Python code.
- Use keyboard and mouse macros.

For writing MIDI related Python code:

- Prepare MIDI, OSC keyboard and mouse inputs and outputs with a single line,
  without boilerplate code.
- Feed input messages to functions or any callables by decorators.
- Work with message objects instead of raw data different for each input type.
- Create GUI widgets with a single line and arrange them with mouse.
- Write basic MIDI related GUI applications with very little Python code.

## Installation

1. Install [Python 3.11+](https://www.python.org/downloads/) including pip.
2. Run `pip install midiscripter`.

Extra steps for Windows:

1. Enable `Add python .exe to PATH` option in Python installer.
2. Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
   and set required virtual MIDI ports inside it.

## Quick Start

1. Paste [script template](examples/script_template.py) to Python IDE or plain
   text editor. IDE is recommended.
2. Run template script as-is from IDE or by `python your_script.py` command to
   open GUI for more info on available ports and incoming input.
3. Turn on available ports' checkboxes to enable them, watch the log for
   input messages.
4. Click on port names and messages in log to copy their declarations to the
   clipboard. Paste the declarations to your script.
5. Modify the template function to make it do what you want.
   Use `log('messages')` for debugging.
6. Restart the script from GUI to check how in works.
7. Write more complex scripts. Use more inputs, outputs and functions
   (callables). Subscribe callables to input messages with
   `@input_port.subscribe` decorator.
