import sys
from collections.abc import Callable

import colorama

from midiscripter.base.msg_base import Msg
from midiscripter.base.port_base import Input, Output


class ConsoleSink:
    COLOR_MAP = {
        Input: colorama.Fore.GREEN,  # Possible colors for CLI are:
        Output: colorama.Fore.MAGENTA,  # black, red, green, yellow,
        Msg: colorama.Fore.BLUE,  # blue, magenta, cyan, white
        Callable: colorama.Fore.CYAN,
    }

    def __call__(self, log_entries: list[tuple[str, dict]]):
        entries = []
        for entry in log_entries:
            text = entry[0]
            kwargs = entry[1]

            if not text:
                entries.append('\n')
                continue

            if '_color' in kwargs and kwargs['_color'].upper() in vars(colorama.Fore):
                main_color_tag = getattr(colorama.Fore, kwargs['_color'].upper())
                text = f'{main_color_tag}{text}{colorama.Style.RESET_ALL}'
            else:
                main_color_tag = colorama.Style.RESET_ALL

            for arg_name, arg_object in kwargs.items():
                for obj_type in (Input, Output, Msg, Callable):
                    if isinstance(arg_object, obj_type):
                        kwargs[arg_name] = (
                            self.COLOR_MAP[obj_type] + str(arg_object) + main_color_tag
                        )

            ctime_text = (
                f'{colorama.Style.DIM}{kwargs["_ctime_str"]}: ' f'{colorama.Style.RESET_ALL}'
            )

            entry_text = ctime_text + text + '\n'

            try:
                entries.append(entry_text.format(**kwargs))
            except KeyError:
                entries.append(entry_text)

        output = ''.join(entries)

        sys.stdout.write(output)
        sys.stdout.flush()
