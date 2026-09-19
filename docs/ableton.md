MIDI Scripter was originally created to overcome certain  limitations 
of Ableton Live without getting into its complex built-in MIDI remote scripts.

MIDI Scripter provides three ways to communicate directly with Ableton Live internals. 

## LiveAPI to OSC

[LiveAPI to OSC](https://github.com/Maboroshy/Max-for-Live-Devices/tree/main/LiveAPI%20to%20OSC) is a Max for Live device I developed specifically for interaction with Live. 

It uses OSC as a communication medium and can control anything Max for Live can. 

You place the device anywhere in your Live set 
and set up corresponding [`OscIO(7500, 7400)`][midiscripter.OscIO] port in your script. 

More details about OSC message protocol are available in the device description.

Example: [Select armed track script with LiveAPI to OSC](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_live_api_to_osc)

## AbletonOSC

If you can't use Max for Live the alternative is [AbletonOSC](https://github.com/ideoforms/AbletonOSC) which also uses OSC.

It has more limitations than LiveAPI to OSC but can do most of what is usually required. 

The AbletonOSC remote script should be installed to Ableton Live and enabled in its settings. 

On the MIDI Scripter side you set up an [`OscIO(11001, 11000)`][midiscripter.OscIO] port 
and follow message protocol in project description.

Example: [Select armed track script with AbletonOSC](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_ableton_osc)

## Ableton MIDI User Remote Script

This method uses MIDI as a communication medium with a pre-mapped Ableton Live user remote script. 

It's even more limited but can be easier to use for simple cases.

It uses the special [`AbletonIO`][midiscripter.AbletonIO],
[`AbletonIn`][midiscripter.AbletonIn] and [`AbletonOut`][midiscripter.AbletonOut] 
ports that are essentially MIDI ports.
The [`AbletonMsg`][midiscripter.AbletonMsg] messages they use are MIDI messages 
mapped to [`AbletonEvent`][midiscripter.AbletonEvent].

Check [`AbletonEvent`][midiscripter.AbletonEvent] documentation to understand this method's capabilities.

The user remote script can be installed using the action in the `Help` 
section of the MIDI Scripter GUI's menu bar. 

The `MIDI Scripter` user remote script should be assigned 
to the proxy ports you use in Ableton Live settings.

Example: [Select armed track script with Ableton MIDI Remote Script](https://github.com/Maboroshy/midi-scripter/blob/master/examples/ableton_select_armed_track_with_remote_script)