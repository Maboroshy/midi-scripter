import pathlib
from typing import TYPE_CHECKING

import midiscripter.base.msg_base

if TYPE_CHECKING:
    from collections.abc import Container
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

    source: 'None | FileEventIn'

    def __init__(
        self,
        type: FileEventType | str,
        path: pathlib.Path,
        *,
        source: 'None | FileEventIn' = None,
    ):
        """
        Args:
            type: File event type
            path: File path
            source (FileEventIn): The [`FileEventIn`][midiscripter.FileEventIn]
                                  instance that generated the message
        """
        super().__init__(type, source)
        self.type = type
        self.path = path

    def matches(
        self,
        type: 'None | Container[FileEventType] | FileEventType | str' = None,
        path: 'None | Container[pathlib.Path] | pathlib.Path' = None,
    ) -> bool:
        return super().matches(type, path)
