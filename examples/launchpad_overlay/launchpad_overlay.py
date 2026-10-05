import json
import pathlib
from typing import Callable

from midiscripter import *


storage_file_path = pathlib.Path(SCRIPT_PATH_STR).with_suffix('.json')


try:
    overlay_cc = json.loads(storage_file_path.read_text())
except (json.JSONDecodeError, FileNotFoundError):
    overlay_cc = []


def label_pad(pad_index: int) -> str:
    pad_label = str(pad_index)
    if pad_label.startswith('9'):
        return ['▴', '▾', '◂', '▸', 'Session', '  Note  ', 'Custom', '⭕'][pad_index - 90 - 1]
    if pad_label.endswith('9'):
        return '>'
    return pad_label


def make_callback_for_value(midi_value: int) -> Callable:
    def toggle_cc(msg: GuiEventMsg):
        overlay_cc.append(midi_value) if msg.data else overlay_cc.remove(midi_value)
        storage_file_path.write_text(json.dumps(overlay_cc))
    return toggle_cc


def prepare_lpx_layout() -> list:
    rows = []
    for row_i in range(1, 10):
        column = []
        rows.append(column)
        for column_i in range(1, 10):
            midi_value = row_i * 10 + column_i
            if midi_value == 99:
                column.append(GuiText('◪'))
            else:
                toggle_button = GuiToggleButton(label_pad(midi_value), toggle_state=midi_value in overlay_cc)
                toggle_button.subscribe(GuiEvent.TOGGLED)(make_callback_for_value(midi_value))
                column.append(toggle_button)
    rows.reverse()
    return rows


widget = GuiWidgetLayout(*prepare_lpx_layout(), title='LPX Pad Selector')


real_lpx = MidiIn('LPX MIDI')
lpx_proxy = MidiOut('LPX Proxy', virtual=True)


@real_lpx.subscribe((MidiType.CONTROL_CHANGE, MidiType.NOTE_ON), 1, overlay_cc)
def send_mappable(msg: ChannelMsg):
    msg.channel = 4
    lpx_proxy.send(msg)


if __name__ == '__main__':
    start_gui()