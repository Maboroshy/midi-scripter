MIDI Scripter was originally created to overcome some limitations 
of Ableton Live without getting into rewriting its complex built-in MIDI remote scripts.

MIDI Scripter has two ways to communicate directly with Ableton Live internals. 
Both have their own limitations, so some use cases may require to use both.

## Ableton MIDI User Remote Script

The idea behind this method is to use pre-mapped Ableton Live user remote 
script and communicate with it using MIDI. 

It uses the special [`AbletonIO`][midiscripter.AbletonIO],
[`AbletonIn`][midiscripter.AbletonIn] and [`AbletonOut`][midiscripter.AbletonOut] 
ports that are essentially proxy MIDI ports.
[`AbletonMsg`][midiscripter.AbletonMsg] messages they use are MIDI messages 
mapped to [`AbletonEvent`][midiscripter.AbletonEvent].

The user remote script can be installed using action in the `Help` 
section of MIDI Scripter GUI's menubar. After installation the `MIDI Scripter` 
user remote script should be assigned to the proxy ports you use in Ableton 
Live settings. The script uses MIDI channel 15.

Example: [Select armed track script with Ableton MIDI Remote Script](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_remote_script)

## AbletonOSC

Another way is to use [AbletonOSC](https://github.com/ideoforms/AbletonOSC) 
remote script and OSC messages. The AbletonOSC remote script should be installed 
to Ableton Live and enabled in its settings.

This method doesn't use any special ports or messages. 
You should use [`OscIO`][midiscripter.OscIO] or [`OscIn`][midiscripter.OscIn]
and [`OscOut`][midiscripter.OscOut] with reference 
to AbletonOSC documentation for address and data attributes. 

AbletonOSC is more capable than the MIDI method in many ways, 
but it's current lack of track and clip index updates makes MIDI 
the preferred method for simple actions.

AbletonOSC listeners send events with index the track/clip had 
when the listener was attached to it, while the track/clip 
can be already moved to another place in Ableton session. 

Example: [Select armed track script with AbletonOSC](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_osc)
