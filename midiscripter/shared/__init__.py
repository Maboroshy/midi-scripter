import __main__

try:
    SCRIPT_PATH_STR: None | str = __main__.__file__
except AttributeError:  # in subprocess or IPython
    SCRIPT_PATH_STR: None | str = None

from .autostart import AutostartManager
from .ableton_script_installer import install_ableton_remote_script, get_ableton_remote_script_path
from .util import (
    thread_executor,
    precise_epoch_time,
    restart_script,
    raise_current_process_cpu_priority,
)
