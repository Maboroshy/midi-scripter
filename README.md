
# <img src="https://raw.githubusercontent.com/Maboroshy/midi-scripter/master/docs/icon.svg" width="23"/> MIDI Scripter
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/midiscripter?style=flat-square&logo=python&logoColor=yellow)](https://pypi.org/project/midiscripter/) ![GitHub License](https://img.shields.io/github/license/maboroshy/midi-scripter?style=flat-square&color=darkgreen) ![For](https://img.shields.io/badge/for-Windows%20|%20macOS%20|%20Linux-darkmagenta?style=flat-square)

MIDI Scripter is a Python framework for filtering, modifying, routing and any other
handling of MIDI, Open Sound Control (OSC), keyboard and mouse input and output.

MIDI Scripter listens to input ports and sends incoming messages to subscribed callables such as functions or methods. 
These callables, along with other Python code, can send modified or new messages through output ports. 
MIDI Scripter can serve as a proxy that filters, transforms and converts incoming messages.

In addition, MIDI Scripter features a customizable graphical user interface (GUI) 
that provides logging, coding assistance, various controls and indicators to use in the script.

All that with no boilerplate and only a few lines of code.

An octave transposer with GUI controls in 10 lines of code:

``` python
from midiscripter import *

midi_keyboard = MidiIn('MIDI Keyboard')  # GUI will provide you the port names
proxy_output = MidiOut('To DAW', virtual=True)  # virtual proxy port for output

# GUI widget in a single line
octave_selector = GuiButtonSelectorH(('-2', '-1', '0', '+1', '+2'), select='0')

@midi_keyboard.subscribe  # decorated function will receive port's messages
def transpose(msg: MidiMsg) -> None:
	if msg.type == MidiType.NOTE_ON or msg.type == MidiType.NOTE_OFF:  # filter
		msg.data1 += 12 * int(octave_selector.selected_item_text)  # modify
	proxy_output.send(msg)  # route

if __name__ == '__main__':
	start_gui()  # opens helpful customizable GUI
```

Screenshot with only `octave_selector` widget enabled:

![Screenshot with only octave_selector widget enabled](
https://github.com/Maboroshy/midi-scripter/blob/master/examples/octave_transposer/screenshot_widget.png?raw=true)

Screenshot with service Ports and Log and Message Sender widgets:

![Screenshot with all the widgets visible](
https://github.com/Maboroshy/midi-scripter/blob/master/examples/octave_transposer/screenshot_full.png?raw=true)

The average latency for the script above is less than 0.25 milliseconds.

Currently, MIDI Scripter is at "beta" development stage. 
It is fully functional but needs more user feedback. 

## Use cases

- Programming MIDI input/output handling scripts 
  that may also use OSC, keyboard and mouse input/output.
- Mapping your MIDI controller in your own custom way, 
  from simple MIDI message filtering or conversion to mostly anything you can imagine.
- Controlling Ableton Live with Python, without diving into 
  it's complex MIDI remote scripting or Max for Live.

## Examples 
- [Launch an app or run any Python code with a MIDI message.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/start_daw_by_midi)
- [Show pressed chord description.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/chord_info)
- Control Ableton Live with [remote script](https://github.com/Maboroshy/midi-scripter/tree/master/examples/ableton_select_armed_track_with_remote_script) or [AbletonOSC.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/ableton_select_armed_track_with_osc)
- [Make custom mapping overlay on top of Ableton Live built-in MIDI controller integration.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/launchpad_overlay)
- [Run Python code with Ableton Live clips.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/ableton_clips_launch_code)
- [Save and load global presets for Ableton Live devices.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/ableton_global_preset)
- [Add extra banks to MIDI controller.](https://github.com/Maboroshy/midi-scripter/tree/master/examples/controls_banks)

## Documentation

MIDI Scripter has fully documented and type hinted API.  
[Overview and API documentation is available here.](https://maboroshy.github.io/midi-scripter)

## Installation

1. Install [Python 3.11+](https://www.python.org/downloads/) including pip.
2. Run `pip install midiscripter`.

Extra steps for Windows:

1. Enable `Add python .exe to PATH` option in Python installer.
2. Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) for virtual MIDI port support.

## Quick Start Guide

1. Paste the [script template](examples/script_template.py) into your Python IDE or a plain text editor. Using IDE is recommended.
2. Run the template script directly from the IDE or by `python your_script.py`. 
   This will open the GUI, providing information about available ports and incoming input.
3. Ensure that the “Show Unused Ports” button located under the port list is activated. 
   Enable the checkboxes for any available ports to open them. Monitor the log for incoming messages.
4. Click on the port names and messages in the log or port list to copy their declarations to the clipboard. 
   You can paste the declarations into your script.
5. Rewrite the template function to achieve desired functionality. Use `log('messages')` for debugging purposes.
6. Restart the script from the GUI to see how it performs.
7. Develop more complex scripts by utilizing additional inputs, outputs and functions (callables). 
   Subscribe new callables to input messages using the `@input_port.subscribe` decorator.

## License 
MIDI Scripter assets and code is under LGPL 3.0 license.  
The code that use it can have any license.
