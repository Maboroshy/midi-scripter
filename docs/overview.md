MIDI Scripter scripts use 5 main elements:

```python
from midiscripter import *

# 1. Ports
midi_keyboard = MidiIn('MIDI Keyboard')
proxy_output = MidiOut('To DAW')

# 2. GUI widgets
octave_selector = GuiButtonSelectorH(('-2', '-1', '0', '+1', '+2'), select='0')

# 3. Calls
@midi_keyboard.subscribe
def transpose(msg: MidiMsg) -> None:

# 4. Messages
    if msg.type == MidiType.NOTE_ON or msg.type == MidiType.NOTE_OFF:
        msg.data1 += 12 * int(octave_selector.selected_item_text)
    proxy_output.send(msg)

# 5. Starter
if __name__ == '__main__':
    start_gui() 
```

## 1. Ports

There are two port types: input ports and output ports.

Port are typically declared as `port_class(name_or_adress)` or `port_class
()` for those that don't need a name. For detailed information 
on how to declare specific ports, refer to the API documentation.

On Linux and macOS it's possible to create virtual MIDI ports with 
`MidiIn('Virtual port name', virtual=True)`. On Windows you'll have to manually 
create virtual ports using [loopMIDI](https://www.tobias-erichsen.
de/software/loopmidi.html). 
Virtual MIDI ports can be used to write proxy scripts, like the one above.

Port declaration is all you need to use the port, the starter
function does the rest.

The starter function opens all declared ports, input ports start to feed 
incoming messages to subscribed callables.

Callables or any other Python code can use `output_port.send(msg)` to send 
messages.

Available ports:

- [MIDI](api/midi_port.md)
- [OSC](api/osc_port.md)
- [Keyboard](api/key_port.md)
- [Mouse](api/mouse_port.md)
- [Ableton Live Remote](api/ableton_port.md)
- [Metronome](api/metronome_port.md)
- [File System Events](api/fs_port.md)
- [Midi Ports Changes](api/midi_ports_changed.md)

## 2. GUI widgets

Declared GUI widgets appear in GUI window opened by 
[`start_gui`][midiscripter.start_gui] starter function.

Widgets are declared as `widget_class(title, content)` or `widget_class
(content)` (used in example above) where:

- title - widget title;
- content - widget's text or tuple of its items' text.

Widget's initial state can be set by keyword arguments specific for widget
class (`color`, `select`, `toggle_state`, etc.) like in the example above.

Widget's state can be read or set by reading or changing its properties.

For detailed information on how to declare widgets, 
refer to the API documentation.

GUI widgets can be rearranged by dragging their titles. 
At first run widget layout can be messy, but it's easy to
arrange it as you want. The GUI will save the widget layout for each script.

GUI widgets act like input ports. They can subscribe callables that will
receive [`GuiEventMsg`][midiscripter.GuiEventMsg] messages.

Custom PySide6 widgets can be added to the GUI by `add_qwidget(qwidget)`.

Available widgets:

- [`GuiText`][midiscripter.GuiText]
- [`GuiButton`][midiscripter.GuiButton]
- [`GuiToggleButton`][midiscripter.GuiToggleButton]
- [`GuiButtonSelectorH`][midiscripter.GuiButtonSelectorH]
- [`GuiButtonSelectorV`][midiscripter.GuiButtonSelectorV]
- [`GuiListSelector`][midiscripter.GuiListSelector]
- [`GuiKnob`][midiscripter.GuiKnob]
- [`GuiSliderH`][midiscripter.GuiSliderH]
- [`GuiSliderV`][midiscripter.GuiSliderV]
- [`GuiProgressBarH`][midiscripter.GuiProgressBarH]
- [`GuiProgressBarV`][midiscripter.GuiProgressBarV]
- [`GuiWidgetLayout`][midiscripter.GuiWidgetLayout]

## 3. Calls

Input ports subscribe functions, object methods or anything callable 
to call with incoming message object. Callables can have any name, 
must accept a message as their only argument or have no arguments at all,
and are not expected to return anything.

To subscribe a callable to the messages from an input port, use the 
`@input_port.subscribe` decorator. A single callable can be subscribed 
to multiple ports by stacking multiple decorators:

``` python
@input_port_1.subscribe
@input_port_2.subscribe
def do_something(msg: MidiMsg) -> None:
    log.green('This function receives messages from both ports')
```

Callable subscription can have conditions provided as 
`@input_port.subscribe(conditions)`. Conditions can be 
[message `.matches` arguments](#message-matching) 
or a [`CallOn` enum value][midiscripter.CallOn].

MIDI Scripter includes  its own [logger](api/logging.md) for debugging or feedback. 
Print log messages with `log('message')` or `log.red('colored message')`. 
The color methods are `red`, `yellow`, `green`, `cyan`, `blue` and `magenta`.

Each call runs in its own thread, but all calls run in the same process.
So if a call performs some heavy computing it can increase latency and 
jitter for the whole script. It's recommended to move heavy computing out 
of the main process with Python's
[`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html) module.

Each callable receives its own copy of the input message it can modify 
without affecting other calls' work.

Getting exception in a call won't affect other calls or the script's work.
Exception details are printed to log.

You can check call execution time statistics in the Ports GUI widget by
hovering mouse over a call item.

## 4. Messages

Messages are data objects generated by input ports or created in the
script's code. Messages can be sent with an output port of the corresponding 
type.

Each message stores the source port instance as `source` attribute and its
creation time in epoch format as `ctime` attribute.

The time since message creation (in milliseconds) can be checked by
its `age_ms` attribute.

[MIDI message][midiscripter.MidiMsg] objects attributes meanings depending
on [MIDI message type][midiscripter.MidiType]:

| `type`                    | `channel`                               | `data1`                       | `data2`                     | `combined_data`                      |
|---------------------------|-----------------------------------------|-------------------------------|-----------------------------|--------------------------------------|
| `MidiType.NOTE_ON`        | **Channel**<br>(1-16)                   | **Note**<br>(0-127)           | **Velocity**<br>(0-127)     | useless                              |
| `MidiType.NOTE_OFF`       | **Channel**<br>(1-16)                   | **Note**<br>(0-127)           | **Velocity**<br>(0-127)     | useless                              |
| `MidiType.CONTROL_CHANGE` | **Channel**<br>(1-16)                   | **Controller**<br>(0-127)     | **Value**<br>(0-127)        | useless                              |
| `MidiType.POLYTOUCH`      | **Channel**<br>(1-16)                   | **Note**<br>(0-127)           | **Pressure**<br>(0-127)     | useless                              |
| `MidiType.AFTERTOUCH`     | **Channel**<br>(1-16)                   | **Pressure**<br>(0-127)       | useless                     | useless                              |
| `MidiType.PROGRAM_CHANGE` | **Channel** <br>(1-16)                  | **Program**<br>(0-127)        | useless                     | useless                              |
| `MidiType.PITCH_BEND`     | **Channel**<br>(1-16)                   | useless                       | useless                     | **Pitch**<br>(0-16383)               |
| `MidiType.SYSEX`          | **Manufacturer ID** <br>(ints in tuple) | **Sub ID**<br>(ints in tuple) | **Data**<br>(ints in tuple) | **Whole message**<br>(ints in tuple) | 

The common attribute names and their defaults allows to safely change
message's `type`:

```python
# This type of message doesn't use the `data2` attribute
>>> msg = ChannelMsg(MidiType.PROGRAM_CHANGE, 1, 10)

# But it still has the default value for `data2` it doesn't use
>>> msg.data2
64

# So when you change its `type` the message is still valid to send
>>> msg.type = MidiType.CONTROL_CHANGE 
>>> msg
ChannelMsg(MidiType.CONTROL_CHANGE, 1, 10, 128)  
```

Other message types are simpler. Check the API documentation for their 
description.

Available message types:

- [`MidiMsg`][midiscripter.MidiMsg] ([`ChannelMsg`][midiscripter.ChannelMsg],
[`SysexMsg`][midiscripter.SysexMsg])
- [`OscMsg`][midiscripter.OscMsg]
- [`KeyMsg`][midiscripter.KeyMsg]
- [`MouseMsg`][midiscripter.MouseMsg]
- [`AbletonMsg`][midiscripter.AbletonMsg]
- [`GuiEventMsg`][midiscripter.GuiEventMsg]
- [`FileEventMsg`][midiscripter.FileEventMsg]

## 5. Starter

Starter is a function that should be called after ports, widgets and
calls are set up. Starter opens all the ports, keeps input message
listening loops running and handles logging.

There are 3 starter functions:

- [`start_gui`][midiscripter.start_gui] - starts the script with GUI and routes
  log messages to its Log widget. The preferred starter.
- [`start_silent`][midiscripter.start_silent] - starts the script with no
  logging or GUI. The fastest.
- [`start_cli_debug`][midiscripter.start_cli_debug] - starts the script with
  logging to console. That increases latency and jitter. Use only while
  debugging the script with no access to GUI.

## Message matching

Message objects can be filtered in callables by their attribute values as in 
the example above, but they also have more powerful 
[`matches`][midiscripter.Msg.matches] method.

This method takes conditions for each message object attribute in the 
order of message object's `__init__`.

This matching uses the simplified 
[schema](https://github.com/keleshev/schema)-like approach:

1. If condition is `None` or omitted, it matches anything.
2. If condition equals attribute, it matches the attribute.
3. If condition is a container and contains the attribute, it matches the 
attribute.

Use `Not(condition)` to invert condition matching.

``` python
>>> msg = MidiMsg(MidiType.NOTE_ON, 1, 61, 80)

>>> msg.matches(
    (MidiType.NOTE_ON, MidiType.NOTE_OFF),  # only "note on" or "note off"
    None,  # any channel
    range(60, 120)  # note value between 60 and 120
)  # no velocity value provided - matches any velocity
True

>>> msg.matches(
    MidiType.NOTE_ON,  # only "note on"
    data2=Not(range(60, 128))  # velocity less than 60 won't match
)  
False
```

The same matching patter can be used as the arguments for 
`@input_port_subscribe` decorator. Only matching messages will go to the calls:

``` python
@input_port.subscribe(MidiType.SYSEX)
def only_sysex(msg: MidiMsg) -> None: 
    log('Only the sysex messages will go here')
```

Using `subscribe` arguments where possible improves the script's efficiency, 
since no calls are made for non-matching messages.

The one-line filtered message proxy using matching `subscribe`:
``` python
MidiIn('MIDI Controller').subscribe(MidiType.SYSEX)(MidiOut('To DAW').send)
```

## Combining multiple scripts

A single combined script is much easier to manage than running multiple
scripts in parallel.

To combine multiple atomic scripts to run as a single one you can simply 
import them.

To manage that easier port declaration with the same arguments returns 
the same port object instance (singleton):

``` python
>>> MidiIn('Port name') is MidiIn('Port name')
True

>>> GuiButton('Ok') is GuiButton('Ok')
True
```

It's advised to put starter into `if __name__ == '__main__':` clause, like in
the example scripts. This allows to safely combine standalone scripts later by
importing them:

```python
from midiscripter import *

# Scripts with starter in `if __name__ == '__main__':` are safe to import 
import my_first_script
import my_second_script

if __name__ == '__main__':
    # Uses setups from both scripts and runs them as a single script
    start_gui() 
```
