import pathlib
from typing import TYPE_CHECKING

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container


class FileEvent(midiscripter.base.msg_base.AttrEnum):
    """File event message type enumerator
    to use as [`FileEventMsg`][midiscripter.FileEventMsg] `type` attribute"""

    # Names are hardcoded, equal watchdog's event types
    MOVED = 'MOVED'
    DELETED = 'DELETED'
    CREATED = 'CREATED'
    MODIFIED = 'MODIFIED'
    CLOSED = 'CLOSED'
    OPENED = 'OPENED'


class FileEventMsg(midiscripter.base.msg_base.Msg):
    ___match_args__ = ('type', 'path')

    type: FileEvent
    """File event type"""

    path: pathlib.Path
    """File path of event"""

    def __init__(self, type: FileEvent | str, path: pathlib.Path):
        """
        Args:
            type: File event type
            path: File path
        """
        super().__init__(type)
        self.path = path

    def matches(
        self,
        type: 'None | Container[FileEvent] | FileEvent | str' = None,
        path: 'None | Container[pathlib.Path] | pathlib.Path' = None,
    ) -> bool:
        return super().matches(type, path)
