import __main__
from .autostart import AutostartManager
from .ableton_script_installer import install_ableton_remote_script, get_ableton_remote_script_path
from .util import restart_script, raise_current_process_cpu_priority, unbracket_args_and_kwargs
from .thread_pool import MinimalThreadPoolExecutor

try:
    SCRIPT_PATH_STR: None | str = __main__.__file__
except AttributeError:  # in subprocess or IPython
    SCRIPT_PATH_STR: None | str = None

thread_executor = MinimalThreadPoolExecutor(10, 64)
