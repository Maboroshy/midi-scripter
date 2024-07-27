from typing import TYPE_CHECKING
from collections.abc import Sequence

from PySide6.QtWidgets import *

import midiscripter.gui.app

if TYPE_CHECKING:
    from gui_widget_base import GuiWidget


class GuiWidgetLayout:
    """Layout for grouping and positioning widgets."""

    def __init__(
        self,
        title: str,
        *rows: Sequence['GuiWidget | GuiWidgetLayout | Sequence[GuiWidget | GuiWidgetLayout]'],
        spacing: int = 6,
    ):
        """
        Args:
            title: Layout title in GUI
            rows: A tuple of items to put in a row.
                  Items can be widgets, layouts or tuples of widgets or layouts.
                  If item is a tuple it's a column of items inside the tuple.
            spacing: space between layout items

        Example:
            ``` python
            # 2 rows x 1 column
            GuiWidgetLayout('2 x 1', row1_col1,
                                     row2_col1)
            ```
            ``` python
            # 1 row x 2 columns
            GuiWidgetLayout('1 x 2', [row1_col1, row1_col2])
            ```
            ``` python
            # 2 rows x 2 columns
            GuiWidgetLayout('2 x 2', [row1_col1, row1_col2],
                                     [row2_col1, row2_col2])
            ```
            ``` python
            # 2 x 2 with second row span
            GuiWidgetLayout('row span', [row1_col1, row1_col2],
                                              row2_span)
            ```
            ``` python
            # 2 x 2 with column span
            GuiWidgetLayout('column span', [col1_span, [row1_col2,
                                                        row2_col2]])
            ```

        Note:
            Calls can't be subscribed to `GuiWidgetLayout`.
            Pre-declare widgets and subscribe calls to them.
        """
        self.qt_widget = QWidget()
        self.qt_widget.setObjectName(title)

        self.__spacing = spacing

        qt_widget_layout = QVBoxLayout()
        self.qt_widget.setLayout(qt_widget_layout)

        self.__populate_layout(qt_widget_layout, rows)
        midiscripter.gui.app.add_qwidget(self.qt_widget)

    def __populate_layout(
        self, layout: QBoxLayout, items: 'Sequence[GuiWidget, GuiWidgetLayout, Sequence]'
    ) -> None:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.__spacing)

        for gui_widget_or_seq in items:
            if not isinstance(gui_widget_or_seq, Sequence):
                layout.addWidget(gui_widget_or_seq.qt_widget)
                midiscripter.gui.app.remove_qwidget(gui_widget_or_seq.qt_widget)
            else:
                # Flip layout type
                child_layout = QVBoxLayout() if isinstance(layout, QHBoxLayout) else QHBoxLayout()
                layout.addLayout(child_layout)
                self.__populate_layout(child_layout, gui_widget_or_seq)
