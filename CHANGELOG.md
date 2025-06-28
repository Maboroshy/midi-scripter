# Changelog

## **v0.7** - 29.06.2025

### Fixed
- OscQueryMaker stability
- GUI logging issues
- `Show Unused Ports` button state loading
- Errors introduced by using newer pyside6 and Qt versions
- Leaving open sockets after script close
- Script restart stability issues

### Added
- MIDI ports changes detection and handling in GUI
- Virtual MIDI port creation on Windows
- `log` can now print representation of an object passed as an argument

### Changed
- [BREAKING] Reimplemented Ableton port with a User Remote Script 
  because previously used script wasn't feature complete
- [BREAKING] Replaced `CallOn.PORT_OPEN` flag with `CallOn.PORT_INIT`
- Reimplemented MIDI ports' opening/closing
- Reimplemented virtual MIDI ports
- `AbletonIn` creates message with `AbletonEvent.UNSUPPORTED` instead 
  of throwing an exception

## **v0.6** - 19.08.2024

### Fixed
- Log filter spaces handling
- Log history and separators handling while using log filters
- Log entry object representations are prepared on log call, not display
- OSC message representation in log
- AbletonMsg representation in log
- Autostart imports issues
- MIDI port's broken status is now reset after successful opening
- Port instance registry handling
- Window state handling

### Added
- Message Sender widget 
- Knob, slider and progress bar widgets
- "Single instance only" option
- `GuiWidgetLayout` now has `spacing` keyword attribute 

### Changed
- Virtual MIDI ports now require dedicated `virtual=True` init argument
- Any type object can be used as GUI widget content, `str(content)` will be 
  applied automatically
- Minor GUI widgets updates

## **v0.5** - 30.06.2024

### Fixed
- Increased log performance
- Maximized window sizing issues

### Added
- Ableton Live control ports and messages with custom remote script
- `CallOn` flags to use as port subscription conditions
- `OscQueryMaker` can include data to requests
- `Control + Click` on object reference in GUI now copies its arguments
- `Show Unused Ports` button for Port widget 
- `Hold` button for Log widget

### Changed
- GUI colors

## **v0.4.1** - 03.06.2024

### Fixed
- Greatly increased performance of GUI widgets text autoresize
- Buttons in button selector widgets now always have same text size

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
