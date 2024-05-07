import pathlib

import watchdog.events
import watchdog.observers

import midiscripter.base.port_base
import midiscripter.file_event
import midiscripter.logger

shared_observer = watchdog.observers.Observer()
shared_observer.daemon = True
shared_observer.start()


class FileEventIn(midiscripter.base.port_base.Input, watchdog.events.FileSystemEventHandler):
    """File system events input port. Watches file/directory modifications.
    Produces [`FileEventMsg`][midiscripter.FileEventMsg] objects.
    """

    def __init__(self, path: str | pathlib.Path, recursive: bool = False):
        """
        Args:
            path: File/directory path to watch
            recursive: `True` to watch directory path recursively
        """
        if isinstance(path, str):
            path = pathlib.Path(path)

        midiscripter.base.port_base.Input.__init__(self, path)
        watchdog.events.FileSystemEventHandler.__init__(self)

        self.__path = path

        if self.__path.is_dir():
            self.__path_to_watch = self.__path
            self.__watch_dir_changes = True
        else:
            self.__path_to_watch = self.__path.parent  # some editors recreate a file on save
            self.__watch_dir_changes = False

        self.__recursive = recursive
        self.__watch = None

    def __repr__(self):
        return f"{self.__class__.__name__}('{str(self._uid)}')"

    def __str__(self):
        return f"'{self.__path.relative_to(self.__path.parent.parent)}' watcher"

    def _open(self) -> None:
        self.__watch = shared_observer.schedule(self, str(self.__path_to_watch), self.__recursive)
        if not shared_observer.is_alive():
            shared_observer.start()
        self.is_enabled = True
        midiscripter.logger.log('Opened {input}', input=self)

    def _close(self) -> None:
        if self.__watch:
            shared_observer.unschedule(self.__watch)
        self.is_enabled = False
        midiscripter.logger.log('Stopped {input}', input=self)

    def on_any_event(self, event: watchdog.events.FileSystemEvent) -> None:
        # Override of `watchdog.events.FileSystemEventHandler` method.
        # Runs on each file system change in `_path`.
        if not self.is_enabled:
            return

        event_path = pathlib.Path(event.src_path)

        if self.__watch_dir_changes or event_path == self.__path:
            msg = midiscripter.file_event.file_event_msg.FileEventMsg(
                event.event_type.upper(), self.__path, source=self
            )
            self._send_input_msg_to_calls(msg)
