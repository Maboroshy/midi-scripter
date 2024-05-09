# Changelog

## v0.4 - __________

### Added

- Reworked GUI log widget. It can exclude entries based on filter now.

## v0.3 - 07.05.2024

### Added

- Linux and macOS support.
- On Linux and macOS declaration of unavailable MIDI port will create a virtual
  port that show up in ports widget with `[v]` prefix.

### Fixed

- MIDI port send issues
- Sending with closed port behavior
- Port re-enabling behavior
- Running starter from IPython now raises exception.

## v0.2 - 30.04.2024

Initial release
