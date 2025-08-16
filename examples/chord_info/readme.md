# Chord Info

![](/examples/chord_info/screenshot.png)

Script that gets input from a set MIDI input port
and shows the chord name and its degree in GUI.

Scale selector and major/minor toggle are available.

Degree for chords out of scale will be printed red.

## Prerequisites

- music21 library: `pip install music21` in console.
- Replace `'DAW'` with your MIDI controller port name to get input
  directly **or** set 'DAW' virtual port as an output from your DAW.
- Arrange the widgets in the script's GUI.

## Notes

The script shouldn't be a proxy because music21 introduces too much latency.

The latency can be reduced to normal by using `.passthrough`
and moving music21 functions to another Python process,
but using after-DAW MIDI input is easier. 
