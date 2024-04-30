from typing import TYPE_CHECKING, Optional, Union

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from midiscripter.osc.osc_port import OscIn


class OscMsg(midiscripter.base.msg_base.Msg):
    """Open Sound Control message"""

    __match_args__ = ('type', 'address', 'data')
    type: str = 'OSC'

    address: str
    """Message address"""

    data: str | bytes | bool | int | float | list | tuple
    """Message data"""

    source: Optional['OscIn']

    def __init__(
        self,
        address: str,
        data: str | bytes | bool | int | float | list | tuple = None,
        *,
        source: Optional['OscIn'] = None,
    ):
        """
        Args:
            address: Open Sound Control message address
            data: Open Sound Control message data
            source (OscIn): The [`OscIn`][midiscripter.OscIn] instance
                            that generated the message
        """
        super().__init__(self.type, source)
        self.address = address
        self.data = data

    def matches(self, address=None, data=None):
        return super().matches(self.type, address, data)
