# MIDI Scripter

MIDI Scripter is a framework for scripting MIDI, keyboard and Open Sound
Control (OSC) input and output with only a few lines of Python code.

MIDI Scripter listens to selected input ports and feed incoming messages to
subscribed callables (functions, methods, etc.). These callables or any
other Python code can send modified or brand-new messages with
output ports. MIDI Scripter can act as a proxy to filter and transform and
convert the input.

MIDI Scripter included customizable GUI that provides messages logging,
"ready to paste" port and message declarations and one line of code widgets for
monitoring / controlling scripts.

An octave transposer with GUI controls in 10 lines of code:

``` python
from midiscripter import *

midi_keyboard = MidiIn('MIDI Keyboard')  # GUI will provide you with port names
proxy_output = MidiOut('To DAW')  # using virtual port for output

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

[Scripting guide and API documentation available.](https://maboroshy.github.io/midi-scripter)

Currently MIDI Scripter is at "beta" development stage. It's fully
functional but needs more user feedback. It works on Windows and Linx and
should work on macOS.

## What it can do

For writing Python code:

- Prepare MIDI, OSC and keyboard inputs and outputs with a single line,
  without boilerplate code.
- Feed input messages to functions or any callables by "decorating" them.
- Work with common message objects instead of raw data different for each port
  type.
- Send MIDI, OSC and keyboard output messages.
- Create GUI widgets with one line and arrange them with mouse on your script's
  dashboard.

For live performance setups:

- Make extra layers to multiply MIDI controls.
- Organize mappings into sets / scenes with GUI dashboard.
- Make an extra overlay mappings on top of MIDI controller's DAW integration by
  using proxies.
- Create and map complex macros.

For MIDI related apps:

- Make custom sequencers or MIDI output generators.
- Make basic music training GUI applications based on MIDI input.

For software control and automation:

- Use MIDI controllers or keyboard shortcuts to run any Python code.
- Use keyboard macros to control apps.

## Installation

1. Install [Python 3.11+](https://www.python.org/downloads/) including pip.
2. Run `pip install midiscripter`.

Extra steps for Windows:

1. Enable `Add python .exe to PATH` option in Python installer.
2. Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
   and set required virtual MIDI ports inside it.

## Quick Start

1. Paste [script template](examples/script_template.py) to Python IDE or plain
   text editor. IDE is greatly recommended.
2. Run unaltered template script from IDE or by `python` command to open GUI for
   more info on available ports and their input.
3. Turn on available ports' checkboxes to enable them, and watch the log for
   input messages.
4. Click on port names and messages to copy their declarations to the clipboard.
   Paste the declarations to your script.
5. Write the functions you need. Subscribe them to input messages with
   `@input_port.subscribe` decorator. Use `log('messages')` for debugging.
   Use `output_port.send(msg)` to send modified or created messages from a
   function.
6. Restart the script from GUI to check how in works.
