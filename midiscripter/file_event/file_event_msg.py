import pathlib
from typing import TYPE_CHECKING, Optional, Union

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from midiscripter.file_event.file_event_port import FileEventIn


class FileEventType(midiscripter.base.msg_base.AttrEnum):
    # Names are hardcoded, equal watchdog's event types
    MOVED = 'MOVED'
    DELETED = 'DELETED'
    CREATED = 'CREATED'
    MODIFIED = 'MODIFIED'
    CLOSED = 'CLOSED'
    OPENED = 'OPENED'


class FileEventMsg(midiscripter.base.msg_base.Msg):
    ___match_args__ = ('type', 'path')

    type: FileEventType
    """File event type"""

    path: pathlib.Path
    """File path of event"""

    source: Optional['FileEventIn']

    def __init__(
        self,
        type: FileEventType | str,
        path: pathlib.Path,
        *,
        source: Optional['FileEventIn'] = None,
    ):
        """
        Args:
            type: File event type
            path: File path
            source (FileEventIn): The [`FileEventIn`][midiscripter.FileEventIn] instance that generated the message
        """
        super().__init__(type, source)
        self.type = type
        self.path = path

    def matches(self, type=None, path=None):
        return super().matches(type, path)
