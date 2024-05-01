import re

_NOTE_NAMES = {
    'Cb': -1,
    'C': 0,
    'C#': 1,
    'Db': 1,
    'D': 2,
    'D#': 3,
    'Eb': 3,
    'E': 4,
    'E#': 5,
    'F': 5,
    'F#': 6,
    'Gb': 6,
    'G': 7,
    'G#': 8,
    'Ab': 8,
    'A': 9,
    'A#': 10,
    'Bb': 10,
    'B': 11,
    'B#': 12,
}
_NOTE_INT_TO_NOTE_NAME_MAP_SHARPS = (
    'C',
    'C#',
    'D',
    'D#',
    'E',
    'F',
    'F#',
    'G',
    'G#',
    'A',
    'A#',
    'B',
)
_NOTE_INT_TO_NOTE_NAME_MAP_FLATS = ('C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B')


class NoteData:
    """Optional wrapper for MIDI note data for readable representation.
    When using it as `int` - it's note MIDI data, when using as `str` - it's note name.
    """

    middle_c_octave_n = 3
    """Octave number for middle C to use as reference for note naming"""

    __note_name_re = re.compile(r'([A-G][#|b]?)(-?[0-9])')

    def __init__(self, int_or_name: int | str, use_flats: bool = False):
        """
        Args:
            int_or_name: note MIDI data (0-127) or note name (like 'C#3' or 'Db3')
            use_flats: True to use flats in note name (Db3), False to use sharps (C#3)
        """
        if isinstance(int_or_name, int):
            self.__int = int_or_name
            self.__str = self.__covert_to_str(self.__int, use_flats)
        elif isinstance(int_or_name, str):
            self.__str = int_or_name
            self.__int = self.__covert_to_int(self.__str)
        else:
            raise TypeError

    def as_str(self) -> str:
        """Note name. Same as `str(note_data_obj)`."""
        return self.__str

    def as_int(self) -> int:
        """Note MIDI data. Same as `int(note_data_obj)`."""
        return self.__int

    def __str__(self):
        return self.__str

    def __int__(self):
        return self.__int

    def __covert_to_str(self, note_int: int, use_flats: bool = False) -> str:
        if not 0 <= note_int < 121:
            raise AttributeError

        octave_n = (note_int / 12) - 5 + self.middle_c_octave_n
        if use_flats:
            note_name = _NOTE_INT_TO_NOTE_NAME_MAP_FLATS[note_int % 12]
        else:
            note_name = _NOTE_INT_TO_NOTE_NAME_MAP_SHARPS[note_int % 12]

        return f'{note_name}{int(octave_n)}'

    def __covert_to_int(self, note_str: str) -> int:
        match = self.__note_name_re.fullmatch(note_str)

        if not match:
            raise AttributeError

        note_name, octave_str = match.groups()
        note_index = _NOTE_NAMES[note_name]
        octave_n = int(octave_str)

        return note_index + (12 * (octave_n + 5 - self.middle_c_octave_n))
