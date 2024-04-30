from midiscripter import *

input_port = MidiIn('Enter port name')
output_port = MidiOut('loopMIDI')


@input_port.subscribe
def proxy(msg: MidiMsg) -> None:
    output_port.send(msg)


if __name__ == '__main__':
    start_gui()
