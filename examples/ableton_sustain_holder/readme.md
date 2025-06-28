# Ableton Live Sustain Holder

This script is one of the reason I wrote this library.

Ableton Live resets sustain position while starting session record 
which can be disturbing during live performance. 

This script preserves sustain position by listening to sustain value 
and sending it to Ableton Live as soon as session record starts.

## Prerequisites

- [AbletonOSC](https://github.com/ideoforms/AbletonOSC)
- Replace `'MIDI Keyboard'` with your MIDI controller port name.
- Set `To DAW` virtual port as an input in Ableton Live.
