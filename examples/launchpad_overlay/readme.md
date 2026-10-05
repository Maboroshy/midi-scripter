# Launchpad X mappable overlay for Ableton Live

![](/examples/launchpad_overlay/launchpad_overlay.png)

This script changes MIDI channel of Novation Launchpad X of individual pads in DAW mode,
so you can map them to anything in Ableton Live. Pads lighting and other pads still work in DAW mode.
Mappable pads are selected by a GUI widget. Settings are saved to json file near the script.

## Prerequisites

- Set `LPX Proxy` as an input for the Launchpad X control surface in Ableton Live settings, keep `LPX MIDI` as an output.
- Enable `Remote` input for `LPX Proxy` input port, so its messages can be mapped.
