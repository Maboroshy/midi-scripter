from midiscripter import *


# Settings
NUMBER_OF_LAYERS = 4
MIDI_CONTROLLER_CHANNEL = 1
LAYERS_CHANNELS_START_FROM = 2
LAYER_SELECTOR_CC_CONTROL = 1


from_midi_controller = MidiIn('MIDI Controller')
to_midi_controller = MidiOut('MIDI Controller')

to_daw = MidiOut('To DAW')
from_daw = MidiIn('From DAW')

layer_selector_widget = GuiButtonSelectorH(
    tuple(str(n) for n in range(1, NUMBER_OF_LAYERS + 1)), 'Layer Selector'
)


current_layer_index = 0
layers_feedback_cc_values = {layer_index: {} for layer_index in range(0, NUMBER_OF_LAYERS)}

LAYER_SELECTOR_ATTRS = (MidiType.CONTROL_CHANGE, MIDI_CONTROLLER_CHANNEL, LAYER_SELECTOR_CC_CONTROL)
LAYERS_CHANNELS_RANGE = range(
    LAYERS_CHANNELS_START_FROM, LAYERS_CHANNELS_START_FROM + NUMBER_OF_LAYERS
)


def send_saved_feedback_values() -> None:
    for control, value in layers_feedback_cc_values[current_layer_index].items():
        feedback_msg = MidiMsg(MidiType.CONTROL_CHANGE, MIDI_CONTROLLER_CHANNEL, control, value)
        to_midi_controller.send(feedback_msg)


@layer_selector_widget.subscribe(type=GuiEventType.SELECTED)
def gui_layer_selector(msg: GuiEventMsg) -> None:
    global current_layer_index
    current_layer_index = int(msg.data) - 1
    log.blue(f'Selected layer #{msg.data}')

    layer_cc_values_len = 128 / NUMBER_OF_LAYERS
    current_layer_cc_value = int(
        (layer_cc_values_len * current_layer_index) + (layer_cc_values_len / 2)
    )
    to_midi_controller.send(ChannelMsg(*LAYER_SELECTOR_ATTRS, current_layer_cc_value))

    send_saved_feedback_values()


@from_midi_controller.subscribe(*LAYER_SELECTOR_ATTRS)
def cc_layer_selector(msg: MidiMsg) -> None:
    global current_layer_index
    new_layer_index = int(msg.data2 / 128 * NUMBER_OF_LAYERS)

    if new_layer_index == current_layer_index:
        return

    current_layer_index = new_layer_index
    log.blue(f'Selected layer #{current_layer_index + 1}')

    send_saved_feedback_values()


@from_midi_controller.subscribe
def input_proxy(msg: MidiMsg) -> None:
    if msg.matches(*LAYER_SELECTOR_ATTRS):
        return

    if msg.type is MidiType.CONTROL_CHANGE:
        msg.channel = LAYERS_CHANNELS_START_FROM + current_layer_index

    to_daw.send(msg)


@from_daw.subscribe
def feedback_proxy(msg: MidiMsg) -> None:
    if msg.type is not MidiType.CONTROL_CHANGE:
        to_midi_controller.send(msg)
        return

    layer_index_for_msg = msg.channel - LAYERS_CHANNELS_START_FROM

    if msg.channel in LAYERS_CHANNELS_RANGE:
        layers_feedback_cc_values[layer_index_for_msg][msg.data1] = msg.data2

    if msg.channel not in LAYERS_CHANNELS_RANGE or layer_index_for_msg == current_layer_index:
        to_midi_controller.send(msg)


if __name__ == '__main__':
    start_gui()
