# Ableton Live Sustain Holder

Ableton Live resets sustain position while starting session record 
which can be disturbing during live performance. 

This script preserves sustain position by listening to sustain value 
and sending it to Ableton Live as soon as session record starts.

## Prerequisites

- `From DAW` and `To DAW` virtual ports.
- [My fork of AbletonOSC](https://github.com/Maboroshy/AbletonOSC) 
to detect session record status.
- Set `To DAW` virtual port as an input in Ableton Live.
- Set `From DAW` virtual port as an output in Ableton Live.
- Put the virtual instrument you use to Instrument Rack 
and add External Instrument to the rack. Set it's MIDI To `From DAW`.
