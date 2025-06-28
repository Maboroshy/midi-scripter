# This is modified version of PyTeMidi by Daniel Drizhuk (complynx)
# https://pypi.org/project/pytemidi/
# https://github.com/complynx/pytemidi
#
# PyTeMidi's MIT license:
#
# Copyright (c) 2020 Daniel Drizhuk (complynx)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ruff: noqa: ANN001, ANN201

import ctypes
import os
import struct
import threading
import time
import weakref
from ctypes import wintypes as wintypes
from collections.abc import Callable


py_bitness = struct.calcsize('P') * 8
libName = 'teVirtualMIDI64.dll' if py_bitness == 64 else 'teVirtualMIDI.dll'
try:
    midiDll = ctypes.WinDLL(os.path.join(os.environ['WINDIR'], 'system32', libName))
except FileNotFoundError:
    raise FileNotFoundError(
        "DLL not found, ensure you've installed loopMIDI or rtpMIDI from\n"
        'http://www.tobias-erichsen.de/software/\n'
    ) from None

# Bits in Mask to enable logging for specific areas
LOGGING_MISC = 1  # log internal stuff (port enable, disable...)
LOGGING_RX = 2  # log data received from the driver
LOGGING_TX = 4  # log data sent to the driver

# This is the size of the buffer that is being used for communication
# with the driver when instanciating a port with the old, deprecated
# "virtualMIDICreatePort" function.  This value is currently 128kb - 1,
# but may change anytime in the future.  This value also limits the
# maximum size of received sysex-data due to the parser in the merger-
# module in the driver.
DEFAULT_BUFFER_SIZE = 0x1FFFE

# Bits in Mask to virtualMIDICreatePortEx2
FLAGS_PARSE_RX = 1  # tells the driver to always provide valid preparsed MIDI-commands
FLAGS_PARSE_TX = 2  # tells the driver to parse all data received via virtualMIDISendData
FLAGS_INSTANTIATE_RX_ONLY = 4  # Only the "midi-out" part of the port is created
FLAGS_INSTANTIATE_TX_ONLY = 8  # Only the "midi-in" part of the port is created
FLAGS_INSTANTIATE_BOTH = 12  # a bidirectional port is created

FLAGS_SUPPORTED = (
    FLAGS_PARSE_RX | FLAGS_PARSE_TX | FLAGS_INSTANTIATE_RX_ONLY | FLAGS_INSTANTIATE_TX_ONLY
)


class MIDIPort(ctypes.Structure):
    """Wrapper for the VM_MIDI_PORT C struct."""

    pass


MIDI_PORT = ctypes.POINTER(MIDIPort)  # Just a pointer, whatever is underneath, we don't care

# Callback interface.  This callback is called by the driver/interface-dll for a packet of MIDI-data that is received
# from the driver by the application using the virtual MIDI-port.
#
# This callback is called in an arbitrary thread-context - so make sure you have all your locking in order!
#
# If you have created the virtual-MIDI-port and specified TE_VM_FLAGS_PARSE_RX in the flags parameter, you will
# receive a fully valid, preparsed MIDI-command with each callback.  The maximum size of data will be the amount
# you specified in maxSysexLength.  Invalid commands or Sysex-commands with a length in excess of maxSysexLength
# will be discarded and not forwarded to you.  Realtime-MIDI-commands will never be "intermingled" with other
# commands (either normal or Sysex) in this mode.  If a realtime-MIDI-command is detected, it is sent to the
# application before the command that it was intermingled with.
#
# In case of the driver being deactivated, the callback is called one time with a midiDataBytes==NULL and
# length==zero, either the driver has been disabled, or another application using the driver has started
# the installation of a newer driver-version
#
# You can throttle the speed of your virtualMIDI-port by not returning immediately from
# this callback after you have taken care of the data received.
#
# If you want to throttle to 31250 bps for example, you need to place this line
# before you return from your callback-function:
# Sleep( length * 10 * 1000) / 31250 );
#
# LPVM_MIDI_DATA_CB(LPVM_MIDI_PORT, midiDataBytes, length, dwCallbackInstance)

bytep = ctypes.POINTER(ctypes.c_uint8)
MIDI_DATA_CB = ctypes.WINFUNCTYPE(None, MIDI_PORT, bytep, wintypes.DWORD, wintypes.PDWORD)

# virtualMIDICreatePortEx2 - this is the current intended function to create a virtual MIDI-port.
#
# You can specify a name for the device to be created. Each named port can only exist once on a system.
#
# When the application terminates, the port will be deleted (or if the public front-end of the port is already in use by
# a DAW-application, it will become inactive - giving back apropriate errors to the application using this port.
#
# In addition to the name, you can supply a callback-interface, which will be called for all MIDI-data received by the
# virtual-midi port. You can also provide instance-data, which will also be handed back within the callback, to have the
# ability to reference port-specific data-structures within your application.
#
# If you specify "NULL" for the callback function, you will not receive any callback, but can call the blocking function
# "virtualMIDIGetData" to retrieve received MIDI-data/commands.  This is especially useful if one wants to interface
# this library to managed code like .NET or Java, where callbacks into managed code are potentially complex or
# dangerous.  A call to virtualMIDIGetData when a callback has been set during the creation will return with
# "ERROR_INVALID_FUNCTION".
#
# If you specified TE_VM_FLAGS_PARSE_RX in the flags parameter, you will always get one fully valid, preparsed
# MIDI-command in each callback. In maxSysexLength you should specify a value that is large enough for the maximum size
# of Sysex that you expect to receive.  Sysex-commands larger than the value specified here will be discarded and not
# sent to the user.  Realtime-MIDI-commands will never be "intermingled" with other commands (either normal or Sysex)
# in this mode.  If a realtime-MIDI-command is detected, it is sent to the application before the command that it was
# intermingled with.
#
# If you specify a maxSysexLength smaller than 2, you will receive fully valid preparsed MIDI-commands, but no
# Sysex-commands, since a Sysex-command must be at least composed of 0xf0 + 0xf7 (start and end of sysex).  Since the
# parser will never be able to construct a valid Sysex, you will receive none - but all other MIDI-commands will be
# parsed out and sent to you.
#
# When a NULL-pointer is handed back to the application, creation failed.  You can check GetLastError() to find out the
# specific problem  why the port could not be created.
# LPVM_MIDI_PORT CALLBACK virtualMIDICreatePortEx2( LPCWSTR portName, LPVM_MIDI_DATA_CB callback,
# DWORD_PTR dwCallbackInstance, DWORD maxSysexLength, DWORD flags );

virtualMIDICreatePortEx2 = midiDll.virtualMIDICreatePortEx2
virtualMIDICreatePortEx2.restype = MIDI_PORT
virtualMIDICreatePortEx2.argtypes = [
    wintypes.LPCWSTR,
    MIDI_DATA_CB,
    wintypes.PDWORD,
    wintypes.DWORD,
    wintypes.DWORD,
]

# With this function, you can close a virtual MIDI-port again, after you have instanciated it.
# After the return from this function, no more callbacks will be received.
# Beware: do not call this function from within the midi-port-data-callback. This may result in a deadlock!

virtualMIDIClosePort = midiDll.virtualMIDIClosePort
virtualMIDIClosePort.restype = None
virtualMIDIClosePort.argtypes = [MIDI_PORT]

# With this function you can send a buffer of MIDI-data to the driver / the application that opened the
# virtual-MIDI-port. If this function returns false, you may check GetLastError() to find out what caused the problem.
#
# This function should always be called with a single complete and valid midi-command (1-3 octets, or possibly more
# for sysex).  Sysex-commands should not be split!  Realtime-MIDI-commands shall not be intermingled with other MIDI-
# commands, but sent seperately!
#
# The data-size that can be used to send data to the virtual ports may be limited in size to prevent
# an erratic application to allocate too much of the limited kernel-memory thus interfering with
# system-stability.  The current limit is 512kb.
#
# BOOL CALLBACK virtualMIDISendData( LPVM_MIDI_PORT midiPort, LPBYTE midiDataBytes, DWORD length );

virtualMIDISendData = midiDll.virtualMIDISendData
virtualMIDISendData.restype = wintypes.BOOL
virtualMIDISendData.argtypes = [MIDI_PORT, wintypes.LPBYTE, wintypes.DWORD]

# With this function you can abort the created midiport.  This may be useful in case you want
# to use the virtualMIDIGetData function which is blocking until it gets data.  After this
# call has been issued, the port will be shut-down and any further call (other than virtualMIDIClosePort)
# will fail
#
# BOOL CALLBACK virtualMIDIShutdown( LPVM_MIDI_PORT midiPort );
virtualMIDIShutdown = midiDll.virtualMIDIShutdown
virtualMIDIShutdown.restype = None
virtualMIDIShutdown.argtypes = [MIDI_PORT]


class DriverError(IOError):
    def __init__(self, errno, additional=''):
        super().__init__(self, f'ERROR({errno}): {additional}')


def realaddr(pointer):
    return ctypes.cast(pointer, ctypes.c_void_p).value


def shutdown(_id) -> None:
    pointer = ctypes.c_void_p(_id)
    port = ctypes.cast(pointer, MIDI_PORT)
    virtualMIDIClosePort(port)


class GCThread(threading.Thread):
    GCTimer = 30 * 60

    def __init__(self):
        super().__init__(daemon=True, name='PyTeMIDI.GC')
        self.collection = {}
        self.running = False
        self.unified_callback_ptr = MIDI_DATA_CB(self.unified_callback)

    def collect(self) -> None:
        for _id, ref in self.collection.items():
            if ref() is None:
                shutdown(_id)
        self.collection = {k: v for k, v in self.collection.items() if v is not None}

    def add(self, _id, dev) -> None:
        self.collection[_id] = weakref.ref(dev)
        if not self.running:
            self.start()

    def remove(self, _id) -> None:
        shutdown(_id)
        del self.collection[_id]

    def close_all(self) -> None:
        for _id in self.collection:
            shutdown(_id)

    def unified_callback(self, port, midi_bytes, length, additional) -> None:
        port_addr = realaddr(port)
        dev = self.collection[port_addr]() if port_addr in self.collection else None
        if dev is not None and midi_bytes is not None:
            try:
                dev._callback(bytes(midi_bytes[:length]))
            except Exception:
                pass

    def run(self) -> None:
        self.running = True

        import atexit

        atexit.register(self.close_all)

        while True:
            time.sleep(self.GCTimer)
            self.collect()


GC = GCThread()


class Device:
    opened_port_names = []

    def __init__(
        self,
        name: str,
        callback: Callable,
        no_output: bool = False,
        no_input: bool = False,
        sysex_size: int = DEFAULT_BUFFER_SIZE,
    ):
        self._name = name
        self._no_input = no_input
        self._no_output = no_output
        self._sysex_size = sysex_size
        self._callback = callback
        self._id = None
        self._id_addr = 0

    def create(self) -> None:
        flags = 0
        if not self._no_input:
            flags |= FLAGS_INSTANTIATE_RX_ONLY
            flags |= FLAGS_PARSE_RX
        if not self._no_output:
            flags |= FLAGS_INSTANTIATE_TX_ONLY
            flags |= FLAGS_PARSE_TX

        _id = virtualMIDICreatePortEx2(
            self._name, GC.unified_callback_ptr, None, self._sysex_size, flags
        )

        if _id is None:
            raise DriverError(ctypes.GetLastError(), "Couldn't create the device")

        self._id = _id
        self._id_addr = realaddr(_id)

        GC.add(self._id_addr, self)

        self.opened_port_names.append(self._name)

    def close(self) -> None:
        GC.remove(self._id_addr)
        self._id = None
        self._id_addr = 0
        self.opened_port_names.remove(self._name)

    def send(self, raw_midi_data: tuple[hex, ...]) -> None:
        raw_midi_bytes = bytearray(raw_midi_data)
        c_buf = (ctypes.c_ubyte * len(raw_midi_bytes)).from_buffer(raw_midi_bytes)
        ret = virtualMIDISendData(self._id, c_buf, len(raw_midi_bytes))
        if ret == 0:
            raise DriverError(ctypes.GetLastError(), "Couldn't send data")
