import collections
import json
import pathlib

from midiscripter import *


PRESET_COUNT = 6
SAVED_DEVICE_NAME_PREFIX = '>'


ableton_osc = OscIO(11001, 11000)

storage_file_path = pathlib.Path(SCRIPT_PATH_STR).with_suffix('.json')


def save_presets() -> None:
    preset_data = [(pr.name, pr.param_data) for pr in Preset.instances if pr.param_data]
    storage_file_path.write_text(json.dumps(preset_data, indent=4))


class Preset:
    EMPTY_PRESET_NAME = 'Empty'
    instances = []

    def __init__(self, name: str, param_data: dict | None = None):
        self.instances.append(self)

        self.param_data: dict[str, dict[str, dict[str, float]]] | None = param_data

        self.save_button = GuiButton('Save', color='green')
        self.save_button.subscribe(GuiEvent.TRIGGERED)(self.save_param_data_from_set)

        self.clear_button = GuiButton('Clear', color='red')
        self.clear_button.subscribe(GuiEvent.TRIGGERED)(self.clear)

        self.name_line = GuiEditableText(name)
        self.name_line.subscribe(GuiEvent.CONTENT_SET)(save_presets)

        self.load_button = GuiButton('Load', color='blue')
        self.load_button.subscribe(GuiEvent.TRIGGERED)(self.load_param_data_to_set)

        self.update_buttons()

    @property
    def name(self) -> str:
        return self.name_line.content

    def as_widget_row(self) -> tuple:
        return [[self.save_button, self.clear_button]], self.name_line * 2, self.load_button

    def update_buttons(self) -> None:
        if self.param_data:
            self.clear_button.color = 'red'
            self.name_line.color = 'black'
            self.load_button.color = 'blue'
        else:
            self.clear_button.color = 'grey'
            self.name_line.color = 'grey'
            self.load_button.color = 'grey'

    def clear(self) -> None:
        self.name_line.content = self.EMPTY_PRESET_NAME
        self.param_data = {}
        self.update_buttons()
        save_presets()

    def save_param_data_from_set(self) -> None:
        self.param_data = collections.defaultdict(dict)
        track_names = ableton_osc.query('/live/song/get/track_names')
        if not track_names:
            log.red('Ableton OSC is not running')
            return

        for track_index, track_name in enumerate(track_names):
            devices_names = ableton_osc.query('/live/track/get/devices/name', track_index)[1:]

            for device_index, device_name in enumerate(devices_names):
                if not device_name.startswith(SAVED_DEVICE_NAME_PREFIX):
                    continue

                param_names = ableton_osc.query(
                    '/live/device/get/parameters/name', (track_index, device_index)
                )[2:]
                param_values = ableton_osc.query(
                    '/live/device/get/parameters/value', (track_index, device_index)
                )[2:]

                device_preset = dict(zip(param_names, param_values, strict=True))
                self.param_data[track_name][device_name] = device_preset

        self.update_buttons()
        save_presets()

    def load_param_data_to_set(self) -> None:
        track_names = ableton_osc.query('/live/song/get/track_names')
        if not track_names:
            log.red('No connection to AbletonOSC')
            return

        for track_index, track_name in enumerate(track_names):
            if track_name not in self.param_data:
                continue

            devices_names = ableton_osc.query('/live/track/get/devices/name', track_index)[1:]

            for device_index, device_name in enumerate(devices_names):
                if not device_name.startswith(SAVED_DEVICE_NAME_PREFIX):
                    continue

                param_names = ableton_osc.query(
                    '/live/device/get/parameters/name', (track_index, device_index)
                )[2:]

                if param_names == tuple(self.param_data[track_name][device_name]):
                    param_values = self.param_data[track_name][device_name].values()
                    ableton_osc.send(
                        OscMsg(
                            '/live/device/set/parameters/value',
                            (track_index, device_index, *param_values),
                        )
                    )
                else:
                    for param_index, param_name in enumerate(param_names):
                        try:
                            param_value = self.param_data[track_name][device_name][param_name]
                            ableton_osc.send(
                                OscMsg(
                                    '/live/device/set/parameter/value',
                                    (track_index, device_index, param_index, param_value),
                                )
                            )
                        except KeyError:
                            log.yellow(
                                f"Can't set preset for {track_name} | {device_name} | {param_name}."
                                f" The parameter's name changed."
                            )


try:
    presets_data: list[tuple[str, dict]] = json.loads(storage_file_path.read_text())
    presets: list[Preset] = [Preset(*data) for data in presets_data]
except (json.JSONDecodeError, FileNotFoundError):
    presets: list[Preset] = []

while len(presets) < PRESET_COUNT:
    presets.append(Preset(Preset.EMPTY_PRESET_NAME))

GuiWidgetLayout(*[preset.as_widget_row() for preset in presets], title='Presets')


if __name__ == '__main__':
    start_gui()
