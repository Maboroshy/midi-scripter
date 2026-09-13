from typing import TYPE_CHECKING

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container


class OscMsg(midiscripter.base.msg_base.Msg):
    """Open Sound Control message"""

    __match_args__ = ('address', 'data')
    type: str = 'OSC'

    address: str
    """Message address"""

    data: str | bytes | bool | int | float | list | tuple
    """Message data"""

    def __init__(self, address: str, data: str | bytes | bool | int | float | list | tuple = None):
        """
        Args:
            address: Open Sound Control message address
            data: Open Sound Control message data
        """
        super().__init__('OSC')
        self.address = address
        self.data = data

    def __str__(self):
        return f'OSC | {self.address}{" | " + str(self.data) if self.data is not None else ""}'

    def __copy__(self):
        return OscMsg(self.address, self.data)

    def matches(
        self,
        address: 'None | Container | str' = None,
        data: 'None | Container | str | bytes | bool | int | float | list | tuple' = None,
    ) -> bool:
        return midiscripter.base.msg_base.Msg.matches(self, address, data)

    def _as_tuple(self) -> tuple:
        return self.address, self.data
