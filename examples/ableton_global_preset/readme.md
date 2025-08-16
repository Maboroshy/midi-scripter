# Global device presets for Ableton Live with OSC

![](/examples/ableton_global_preset/screenshot.png)

This script uses AbletonOSC to save, store and recall the parameters of 
Ableton Live devices which name starts with `>` as named presets.

Only top level devices in instrument tracks are supported, in-rack 
devices or send / master tracks are not supported.

The track name and device name should not change to recall the preset. 
Mind that track name with `#` is changing on reorder.


## Prerequisites

[AbletonOSC](https://github.com/ideoforms/AbletonOSC)
