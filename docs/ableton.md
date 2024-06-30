MIDI Scripter was originally created to overcome some limitations 
of Ableton Live without getting into rewriting its complex built-in MIDI remote scripts.

MIDI Scripter has two ways to communicate directly with Ableton Live internals. 
Both has some limitations, so some use cases may require to use both.

## 1. Ableton MIDI Remote Script

The idea behind this method is to use the existing Ableton Live remote 
script and communicate with it by MIDI. 
[Special remote script](https://github.com/Maboroshy/midi-scripter/tree/master/extra/Ableton%20Remote%20Script) should be 
installed to Ableton Live and assigned to virtual MIDI ports in its settings.

The script has its raw MIDI messages mapped to 
[`AbletonMsg`][midiscripter.AbletonMsg] objects with corresponding 
[`AbletonEvent`][midiscripter.AbletonEvent] as `type` attribute.
 
All available events are listed in [API documentation][midiscripter.AbletonEvent].

The messages are received and sent by [`AbletonIn`][midiscripter.AbletonIn] and 
[`AbletonOut`][midiscripter.AbletonOut] ports that are wrappers above virtual MIDI 
ports used for communication.

These ports should be declared with virtual MIDI port name as an argument.

Example: [Select armed track script with Ableton MIDI Remote Script](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_remote_script)

## 2. AbletonOSC

Another way is to use [AbletonOSC](https://github.com/ideoforms/AbletonOSC) 
remote script and OSC messages. The AbletonOSC remote script should be installed 
to Ableton Live and enabled in its settings.

This method doesn't use any special ports or messages. 
You should use [`OscIn`][midiscripter.OscIn], [`OscOut`][midiscripter.OscOut] 
and [`OscMsg`][midiscripter.OscMsg] with reference 
to AbletonOSC documentation for address and data attributes. 

AbletonOSC is more capable than the MIDI method in many ways, 
but it's current lack of track and clip index updates handling makes MIDI 
the preferred method for simple actions on tracks/clips.
AbletonOSC listeners send events with index the track/clip had 
when the listener was attached to it, while the track/clip 
can be already moved to another place in Ableton session. 

Example: [Select armed track script with AbletonOSC](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_osc)
