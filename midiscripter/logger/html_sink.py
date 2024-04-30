from collections.abc import Callable

from midiscripter.base.msg_base import Msg
from midiscripter.base.port_base import Input, Output


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

    def __call__(self, log_entries: list[tuple[str, dict]]):
        html_entries = []
        for entry in log_entries:
            text = entry[0]
            kwargs = entry[1]

            text = text.replace('\n', '<br>')
            text = text.replace(' ', '&nbsp;')

            if '_color' in kwargs:
                text = to_html_colored_text(text, f'dark{kwargs["_color"]}')

            for arg_name, arg_object in kwargs.items():
                for obj_type in (Input, Output, Msg):
                    if isinstance(arg_object, obj_type):
                        kwargs[arg_name] = to_html_link(
                            str(arg_object), self.COLOR_MAP[obj_type], arg_object.__repr__()
                        )
                else:
                    if isinstance(arg_object, Callable):
                        kwargs[arg_name] = to_html_colored_text(
                            arg_object.__name__, self.COLOR_MAP[Callable]
                        )

            if text:
                ctime_text = to_html_colored_text(kwargs['_ctime_str'], 'grey')
                html_entry = f'{ctime_text}: {text}'
            else:
                html_entry = ''

            try:
                html_entries.append(html_entry.format(**kwargs))
            except KeyError:
                html_entries.append(html_entry)

        self.sink_function(html_entries)
