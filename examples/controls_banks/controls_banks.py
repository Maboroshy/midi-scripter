from midiscripter import *


# Settings
NUMBER_OF_BANKS = 4
MIDI_CONTROLLER_CHANNEL = 1
BANKS_CHANNELS_START_FROM = 2
BANK_SELECTOR_CC_CONTROL = 1


from_midi_controller = MidiIn('MIDI Controller')
to_midi_controller = MidiOut('MIDI Controller')

to_daw = MidiOut('To DAW', virtual=True)
from_daw = MidiIn('From DAW', virtual=True)

bank_selector_widget = GuiButtonSelectorH(
    tuple(str(n) for n in range(1, NUMBER_OF_BANKS + 1)), title='Bank Selector'
)


current_bank_index = 0
banks_feedback_cc_values = {bank_index: {} for bank_index in range(0, NUMBER_OF_BANKS)}

BANK_SELECTOR_ATTRS = (MidiType.CONTROL_CHANGE, MIDI_CONTROLLER_CHANNEL, BANK_SELECTOR_CC_CONTROL)
BANKS_CHANNELS_RANGE = range(BANKS_CHANNELS_START_FROM, BANKS_CHANNELS_START_FROM + NUMBER_OF_BANKS)


def send_saved_feedback_values() -> None:
    """Sends messages with all CC latest values for selected bank to MIDI controller"""
    for control, value in banks_feedback_cc_values[current_bank_index].items():
        feedback_msg = MidiMsg(MidiType.CONTROL_CHANGE, MIDI_CONTROLLER_CHANNEL, control, value)
        to_midi_controller.send(feedback_msg)


@bank_selector_widget.subscribe(type=GuiEvent.SELECTED)
def gui_bank_selector(msg: GuiEventMsg) -> None:
    """Sets current bank on GUI widget selection with feedback to MIDI controller's selector"""
    global current_bank_index
    current_bank_index = int(msg.data) - 1
    log.blue(f'Selected bank #{msg.data}')

    bank_selector_zone_len = 128 / NUMBER_OF_BANKS
    current_bank_cc_value = int(
        (bank_selector_zone_len * current_bank_index) + (bank_selector_zone_len / 2)
    )
    to_midi_controller.send(ChannelMsg(*BANK_SELECTOR_ATTRS, current_bank_cc_value))

    send_saved_feedback_values()


@from_midi_controller.subscribe(*BANK_SELECTOR_ATTRS)
def cc_bank_selector(msg: MidiMsg) -> None:
    """Sets current bank on MIDI controller's selector with feedback to GUI widget"""
    global current_bank_index
    new_bank_index = int(msg.data2 / 128 * NUMBER_OF_BANKS)

    if new_bank_index == current_bank_index:
        return

    current_bank_index = new_bank_index
    bank_selector_widget.select(new_bank_index)

    send_saved_feedback_values()


@from_midi_controller.subscribe
def input_proxy(msg: MidiMsg) -> None:
    """A general MIDI input proxy that changes message channel according to selected bank"""
    if msg.matches(*BANK_SELECTOR_ATTRS):
        return

    if msg.type is MidiType.CONTROL_CHANGE:
        msg.channel = BANKS_CHANNELS_START_FROM + current_bank_index

    to_daw.send(msg)


@from_daw.subscribe
def feedback_proxy(msg: MidiMsg) -> None:
    """A feedback proxy that saves feedback even for not selected banks for later sending"""
    if msg.type is not MidiType.CONTROL_CHANGE:
        to_midi_controller.send(msg)
        return

    bank_index_for_msg = msg.channel - BANKS_CHANNELS_START_FROM

    if msg.channel in BANKS_CHANNELS_RANGE:
        banks_feedback_cc_values[bank_index_for_msg][msg.data1] = msg.data2

    if msg.channel not in BANKS_CHANNELS_RANGE or bank_index_for_msg == current_bank_index:
        to_midi_controller.send(msg)


if __name__ == '__main__':
    start_gui()
