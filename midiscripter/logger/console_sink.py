import sys
from collections.abc import Callable

import colorama

from midiscripter.logger.log import LogEntry, LogObj
from midiscripter.base.msg_base import Msg
from midiscripter.base.port_base import Input, Output


class ConsoleSink:
    # Possible colors for CLI are: black, red, green, yellow, blue, magenta, cyan, white
    COLOR_MAP = {
        Input: colorama.Fore.GREEN,
        Output: colorama.Fore.MAGENTA,
        Msg: colorama.Fore.BLUE,
        Callable: colorama.Fore.CYAN,
    }

    def __call__(self, log_entries: list[LogEntry | None]):
        entries = []
        for entry in log_entries:
            if entry is None:
                entries.append('\n')
                continue

            text, kwargs, timestamp, color = entry
            format_kwargs = {}

            if color and color.upper() in vars(colorama.Fore):
                main_color_tag = getattr(colorama.Fore, color.upper())
                text = f'{main_color_tag}{text}{colorama.Style.RESET_ALL}'
            else:
                main_color_tag = colorama.Style.RESET_ALL

            for arg_name, arg_object in kwargs.items():
                arg_object: LogObj
                for obj_type in (Input, Output, Msg, Callable):
                    if isinstance(arg_object, obj_type):
                        format_kwargs[arg_name] = (
                            self.COLOR_MAP[obj_type] + arg_object.log_str + main_color_tag
                        )
                        break
                else:
                    format_kwargs[arg_name] = arg_object.log_str

            ctime_text = f'{colorama.Style.DIM}{timestamp}: {colorama.Style.RESET_ALL}'
            entry_text = ctime_text + text + '\n'

            try:
                entries.append(entry_text.format(**format_kwargs))
            except KeyError:
                entries.append(entry_text)

        output = ''.join(entries)

        sys.stdout.write(output)
        sys.stdout.flush()
