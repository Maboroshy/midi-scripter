# Ableton Live Sustain Holder

Ableton Live resets sustain position while starting session record 
which can be disturbing during live performance. 

This script preserves sustain position by listening to sustain value 
and sending it to Ableton Live as soon as session record starts.

## Prerequisites

- `To DAW` virtual port.
- [My fork of AbletonOSC](https://github.com/Maboroshy/AbletonOSC) 
to detect session record status.
- Replace `'MIDI Keyboard'` with your MIDI controller port name.
- Set `To DAW` virtual port as an input in Ableton Live.
