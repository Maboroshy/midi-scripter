from typing import TYPE_CHECKING
from collections.abc import Sequence

from PySide6.QtWidgets import *

import midiscripter.gui.app
from .gui_widget_base import GuiWindowItem

if TYPE_CHECKING:
    from gui_widget_base import GuiWidget


class GuiWidgetLayout(GuiWindowItem):
    """Layout for grouping and positioning widgets"""

    _title_to_instance: dict[str, 'GuiWidgetLayout'] = {}
    """Title to instances registry filled by `__init__`"""

    def __init__(
        self,
        *rows: Sequence['GuiWidget | GuiWidgetLayout | None | Sequence'],
        spacing: int = 6,
        title: str | None = None,
    ):
        """
        Args:
            rows: A tuple of items to put in a row.
                  Items can be widgets, layouts, `None` for spacers or Sequences (list, tuple)
                  of all the above. If item is a Sequence, it's a column of items in the Sequence.
                  To stretch the widget multiply it by the stretch multiplier: `gui_widget_obj * 2`.
            spacing: space between layout items
            title: Title for dock widget and position saving, set by type if `None`

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
            # 1 row x 3 columns with the spacer as the second and one third one widget stretched
            GuiWidgetLayout('1 x 2', [row1_col1, None, row1_col3 * 2])
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
            Calls can't be subscribed to `GuiWidgetLayout`. Subscribe calls to widgets instead.
        """
        super().__init__(title=title)

        self.qt_widget = QWidget()
        self.qt_widget.setObjectName(self._title)

        self.__spacing = spacing

        qt_widget_layout = QVBoxLayout()
        self.qt_widget.setLayout(qt_widget_layout)

        self.__populate_layout(qt_widget_layout, rows)

        midiscripter.gui.app.add_qwidget(self.qt_widget)

    def __populate_layout(
        self, layout: QBoxLayout, items: 'Sequence[GuiWidget, GuiWidgetLayout, Sequence, None]'
    ) -> None:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.__spacing)

        for item in items:
            if item is None:
                layout.addStretch(1)
            elif not isinstance(item, Sequence):
                layout.addWidget(item.qt_widget, item._stretch_multiplier)
                midiscripter.gui.app.remove_qwidget(item.qt_widget)
            else:
                # Flip layout type
                child_layout = QVBoxLayout() if isinstance(layout, QHBoxLayout) else QHBoxLayout()
                layout.addLayout(child_layout, 1)
                self.__populate_layout(child_layout, item)
