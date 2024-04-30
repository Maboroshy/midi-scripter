# Chord Info

![](/examples/chord_info/screenshot.png)

This script gets input from a set MIDI input port 
and shows the chord name and its degree in GUI. 

Scale selector and major/minor toggle are available.

Degree for chords out of scale will be printed red.

## Prerequisites
- music21 library: `pip install music21` in console.
- [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) app with 'From DAW' virtual port for input.
- Set 'loopMIDI In' virtual port as an output from your DAW.
- Arrange the widgets in script's GUI.

## Notes
The script shouldn't be a proxy since music21 introduces too much latency. 

The latency can be reduced to normal by using passthrough 
and moving music21 functions to another Python process, 
but using after-DAW MIDI input is much easier. 
