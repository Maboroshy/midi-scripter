import sys

import colorama

from midiscripter.logger.log_obj import LogEntry


def _to_colored_text(text: str, color: str, global_color: None | str = None) -> str:
    if not color:
        return text

    if global_color:
        closing_tag = getattr(colorama.Fore, color.upper())
    else:
        closing_tag = colorama.Style.RESET_ALL
    color_tag = getattr(colorama.Fore, color.upper())
    return f'{color_tag}{text}{closing_tag}'


def console_log_formatter(log_entries: list[LogEntry]) -> str:
    entries = []
    for entry in log_entries:
        text = entry.text

        if not text:
            entries.append('\n')
            continue

        if entry.color:
            text = _to_colored_text(text, entry.color)

        try:
            args = [_to_colored_text(obj_ref.text, obj_ref.color, entry.color) for obj_ref in entry.format_args]
            kwargs = {
                arg: _to_colored_text(obj_ref.text, obj_ref.color, entry.color)
                for arg, obj_ref in entry.format_kwargs.items()
            }
            text = text.format(*args, **kwargs)
        except (KeyError, IndexError):
            pass

        ctime_text = f'{colorama.Style.DIM}{entry.timestamp}: {colorama.Style.RESET_ALL}'
        entry_text = f'{ctime_text}{text}\n'
        entries.append(entry_text)

    return ''.join(entries)


def console_sink(output: str) -> None:
    sys.stdout.write(output)
    sys.stdout.flush()
