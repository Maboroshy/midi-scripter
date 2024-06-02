# Changelog

## **v0.4.1** - 03.06.2024

### Fixed
- Greatly increased performance of GUI widgets text autoresize

## **v0.4** - 02.06.2024

### Added
- Added mouse support with input and output ports and message
- Input ports `subscribe` method now has arguments to subscribe only 
  matching messages
- Improved message `matches` method, implemented `Not(condition)` for 
  matching inversion
- `KeyIn` can now supress incoming input
- `MetronomeIn` sets `bpm` and count `number` to all messages it generates
- Reworked GUI log widget. It can exclude entries based on filter now.
- Midi ports now has `name` attribute

### Changed
- [BREAKING] Changed signatures for `MetronomeIn` and `GuiWidged` classes so 
  name/title comes first, for unification
- [BREAKING] Ports' `subscirbed_calls` renamed to `calls` for readability
- [BREAKING] Renamed `...EventType` enum names to `...Event` for less space 
  and readability 
- [BREAKING] Subsequent ports init requires all init attrs match

### Fixed
- Fixed and improved `GuiWidgetLayout`
- Fixed and improved example scripts

## **v0.3** - 07.05.2024

### Added

- Linux and macOS support.
- On Linux and macOS declaration of unavailable MIDI port will create a virtual
  port that show up in ports widget with `[v]` prefix.

### Fixed

- MIDI port send issues
- Sending with closed port behavior
- Port re-enabling behavior
- Running starter from IPython now raises exception.

## **v0.2** - 30.04.2024

Initial release
