from midiscripter.logger.log_obj import LogEntry, LogObjRef
from midiscripter.gui.color_theme import theme_color


def _to_html_link(text: str, color: str, link_text: str) -> str:
    return f'<a href="{link_text}" style="color: {theme_color(color)};">{text}</a>'


def _to_html_colored_text(text: str, color: str) -> str:
    return f'<font color="{theme_color(color)}">{text}</font>'


def _obj_ref_to_html(obj_ref: LogObjRef) -> str:
    if not obj_ref.color:
        return obj_ref.text
    elif obj_ref.link is None:
        return _to_html_colored_text(obj_ref.text, obj_ref.color)
    else:
        return _to_html_link(obj_ref.text, obj_ref.color, obj_ref.link)


def html_log_formatter(log_entries: list[LogEntry]) -> list[str]:
    html_entries = []
    for entry in log_entries:
        text, format_args, format_kwargs, timestamp, color = entry

        if not text:
            html_entries.append('<p>&nbsp;</p>')
            continue

        try:
            args = [_obj_ref_to_html(obj_ref) for obj_ref in format_args]
            kwargs = {arg: _obj_ref_to_html(obj_ref) for arg, obj_ref in format_kwargs.items()}
            text = text.format(*args, **kwargs)
        except (KeyError, IndexError):
            pass

        ctime_text = _to_html_colored_text(f'{timestamp}: ', 'grey')

        if color:
            text = _to_html_colored_text(text, color)

        text = text.replace('\n', '<br>')

        html_entry = f'<p>{ctime_text}{text}</p>'
        html_entries.append(html_entry)

    return html_entries
