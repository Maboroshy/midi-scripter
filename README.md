# <img src="https://raw.githubusercontent.com/Maboroshy/midi-scripter/master/docs/icon.svg" width="23"/> MIDI Scripter

MIDI Scripter is a framework for filtering, modifying, routing and any other
scripting of MIDI, Open Sound Control (OSC), keyboard and mouse input and
output with Python.

MIDI Scripter monitors input ports and processes incoming messages 
by sending them to subscribed callables such as functions or methods. 
These callables, along with any other Python code, can send out modified 
or newly created messages through output ports. Essentially, MIDI Scripter 
serves as a proxy that can filter, transform, and convert incoming data.

In addition, MIDI Scripter features a customizable graphical user interface (GUI) 
that provides message logging, coding assistance, 
and various controls and indicators to use in the script.

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

The average measured roundtrip latency for the script above is less than 0.25 
milliseconds.

Currently MIDI Scripter is at "beta" development stage. It's fully
functional but needs more user feedback. It works on Windows and Linux and
should work on macOS.

## Documentation and Examples

[Overview and full API documentation is available here.](https://maboroshy.github.io/midi-scripter)

[You can find more examples here.](https://github.com/Maboroshy/midi-scripter/tree/master/examples)


## Features

#### Basic Functionality:

- Receive input messages from MIDI, OSC, keyboard and mouse.
- Filter, modify, and manipulate messages using Python.
- Send modified or newly generated MIDI, OSC, keyboard, and mouse messages.

#### For Music Performance MIDI Setups:

- Create additional banks and layers to enhance MIDI controllers.
- Organize mappings into sets or scenes using with GUI dashboard.
- Add overlay mappings on top of your MIDI controller’s DAW integration using proxies.
- Combine multiple MIDI controllers into a single unit with any logic.
- Control Ableton Live through a [special remote script or AbletonOSC]().

#### For Software Control and Automation:

- Map or convert messages to one another based on specific conditions and logic.
- Use MIDI controllers or keyboard shortcuts to run any Python code.
- Implement keyboard and mouse macros.

#### For Writing MIDI-Related Python Code:

- Prepare MIDI, OSC, keyboard, and mouse inputs and outputs with a single line of code, without boilerplate code.
- Use decorators to feed input messages to functions or other callables.
- Work with message objects rather than raw data, which varies by port type.
- Create GUI widgets with just one line of code and arrange them with mouse.
- Fully type-annotated API for better code clarity.

## Installation

1. Install [Python 3.11+](https://www.python.org/downloads/) including pip.
2. Run `pip install midiscripter`.

Extra steps for Windows:

1. Enable `Add python .exe to PATH` option in Python installer.
2. Install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
   and set required virtual MIDI ports inside it.

## Quick Start Guide

1. Paste the [script template](examples/script_template.py) into your Python IDE or a plain text editor. Using an IDE is recommended.
2. Run the template script directly from the IDE or by `python your_script.py`. This will open the GUI (as shown in the screenshot below), providing information about available ports and incoming input.
3. Ensure that the “Show Unused Ports” button located under the port list is activated. Enable the checkboxes for any available ports to activate them, monitor the log for incoming messages.
4. Click on the port names and messages in the log to copy their 
   declarations to the clipboard. Paste the declarations into your script.
5. Adjust the template function to achieve desired functionality. Use `log('messages')` for debugging purposes.
6. Restart the script from the GUI to see how it performs.
7. Develop more complex scripts by utilizing additional inputs, outputs, and functions (callables). Subscribe callables to input messages using the `@input_port.subscribe` decorator.

![Screenshot](https://github.com/Maboroshy/midi-scripter/blob/master/docs/screenshot.png?raw=true)
