from midiscripter import *


input_port = MidiIn('Enter port name')
output_port = MidiOut('To DAW', virtual=True)


@input_port.subscribe
def proxy(msg: MidiMsg) -> None:
    log('Your actions here')
    output_port.send(msg)


if __name__ == '__main__':
    start_gui()
