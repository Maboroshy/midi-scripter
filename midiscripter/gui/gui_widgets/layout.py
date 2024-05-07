from typing import TYPE_CHECKING
from collections.abc import Sequence

from PySide6.QtWidgets import *

import midiscripter.gui.app

if TYPE_CHECKING:
    import gui_widget_base


class GuiWidgetLayout:
    """Layout for grouping and positioning widgets."""

    def __init__(
        self,
        rows: Sequence[
            'gui_widget_base.GuiWidget | GuiWidgetLayout | '
            'Sequence[gui_widget_base.GuiWidget | GuiWidgetLayout]'
        ],
    ):
        """
        Args:
            rows: A tuple of items to put in a row.
                  Items can be widgets, layouts or tuples of widgets or layouts.
                  If item is a tuple it's a column of items inside the tuple.

        Warning:
            Calls can't be subscribed to `GuiWidgetLayout`.
            Pre-declare widgets to subscribed calls to them.

        Example:
            ```
            GuiWidgetLayout([widget_col1_row1, widget_col2_row1],
                            [widget_col1_row2, widget_col2_row2])
            ```
        """
        self.wrapped_qt_widgets = []
        self.qt_widget = QWidget()

        qt_widget_layout = QVBoxLayout()
        qt_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.qt_widget.setLayout(qt_widget_layout)

        for row in rows:
            if not isinstance(row, Sequence):
                qt_widget_layout.addWidget(row.qt_widget)
                midiscripter.gui.app.remove_qwidget(row.qt_widget)
                self.wrapped_qt_widgets.append(row.qt_widget)
            else:
                if not row:
                    continue

                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                qt_widget_layout.addLayout(row_layout)

                for gui_widget in row:
                    row_layout.addWidget(gui_widget.qt_widget)
                    midiscripter.gui.app.remove_qwidget(gui_widget.qt_widget)
                    self.wrapped_qt_widgets.append(gui_widget.qt_widget)

        midiscripter.gui.app.add_qwidget(self.qt_widget)
