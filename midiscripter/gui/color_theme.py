from typing import Literal


_light_colors = {
    'grey': 'grey',
    'red': 'lightcoral',
    'blue': 'deepskyblue',
    'green': 'lightgreen',
    'yellow': 'yellow',
    'magenta': 'plum',
    'cyan': 'aqua',
}


_dark_colors = {
    'grey': 'grey',
    'red': 'darkred',
    'blue': 'darkblue',
    'green': 'darkgreen',
    'yellow': 'darkgoldenrod',
    'magenta': 'darkmagenta',
    'cyan': 'darkcyan',
}


_dark_mode = True


def enable_dark_mode(enable: bool) -> None:
    """Set dark mode status for theming"""
    global _dark_mode
    _dark_mode = enable


def theme_color(
    color_name: Literal['grey', 'red', 'blue', 'green', 'yellow', 'magenta', 'cyan'],
    for_background: bool = False,
) -> str:
    """Convert the color to current (light/dark) GUI theme"""
    if (not for_background and _dark_mode) or (for_background and not _dark_mode):
        return _light_colors[color_name]
    else:
        return _dark_colors[color_name]
