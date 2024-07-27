from collections.abc import Callable

from midiscripter.logger.log import LogEntry, LogObj
from midiscripter.base.msg_base import Msg
from midiscripter.base.port_base import Input, Output, SubscribedCall


def to_html_link(text: str, color: str, link_text: str) -> str:
    return f'<a href="{link_text}" style="color: {color};">{text}</a>'


def to_html_colored_text(text: str, color: str) -> str:
    return f'<font color="{color}">{text}</font>'


class HtmlSink:
    COLOR_MAP = {
        Input: 'darkGreen',  # Possible colors for CLI are:
        Output: 'darkMagenta',  # black, red, green, yellow,
        Msg: 'darkBlue',  # blue, magenta, cyan, white
        Callable: 'darkCyan',
    }

    def __init__(self, sink_function: Callable):
        self.sink_function = sink_function

    def __call__(self, log_entries: list[LogEntry | None]):
        html_entries = []
        for entry in log_entries:
            if entry is None:
                html_entries.append('')
                continue

            text, kwargs, timestamp, color = entry

            text = text.replace('\n', '<br>')

            if color in kwargs:
                text = to_html_colored_text(text, f'dark{color}')

            format_kwargs = {}
            for arg_name, arg_object in kwargs.items():
                arg_object: LogObj

                for obj_type in (Input, Output, Msg):
                    if isinstance(arg_object, obj_type):
                        format_kwargs[arg_name] = to_html_link(
                            arg_object.log_str, self.COLOR_MAP[obj_type], arg_object.log_repr
                        )
                        break
                else:
                    if isinstance(arg_object, SubscribedCall):
                        format_kwargs[arg_name] = to_html_colored_text(
                            arg_object.log_str, self.COLOR_MAP[Callable]
                        )
                    else:
                        format_kwargs[arg_name] = arg_object.log_str

            ctime_text = to_html_colored_text(timestamp, 'grey')
            html_entry = f'{ctime_text}: {text}'

            try:
                html_entries.append(html_entry.format(**format_kwargs))
            except KeyError:
                html_entries.append(html_entry)

        self.sink_function(html_entries)
