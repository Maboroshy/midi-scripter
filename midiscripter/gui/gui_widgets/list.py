from collections.abc import Sequence

from PySide6.QtWidgets import *
from PySide6.QtCore import *

from .gui_widget_base import GuiWidget
from .mixins import WrappedQWidgetMixin


class ListSelectorWidget(WrappedQWidgetMixin, QListWidget):
    FONT_SIZE = 16

    def __init__(self):
        QListWidget.__init__(self)
        WrappedQWidgetMixin.__init__(self)

        font = self.font()
        font.setPointSize(self.FONT_SIZE)
        self.setFont(font)

        self.setStyleSheet('border: none; padding: 8px')

        self.currentRowChanged.connect(self.selection_changed_signal)

    def set_content(self, list_items: Sequence[str]) -> None:
        self.addItems([str(item) for item in list_items])

    def set_selection(self, selection: int | str) -> None:
        if isinstance(selection, int):
            self.setCurrentRow(selection)
        elif isinstance(selection, str):
            items_for_name = self.findItems(selection, Qt.MatchFlag.MatchExactly)
            if items_for_name != -1:
                self.setCurrentItem(items_for_name[0])
        else:
            raise ValueError('Selection must be int or str')

    def get_selected_item_index(self) -> int | None:
        return self.currentRow()

    def get_selected_item_text(self) -> str | None:
        if self.currentItem():
            return self.currentItem().text()
        else:
            return None


class GuiListSelector(GuiWidget):
    """List of text items to select value"""

    _qt_widget_class = ListSelectorWidget

    def __init__(
        self,
        content: Sequence[str] | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
        title: str | None = None,
    ):
        """
        Args:
            content: Items' texts
            color: Text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            select: Text or index of item to select initially
            title: Title for dock widget and position saving, set by content or type if `None`
        """
        super().__init__(content, color=color, select=select, title=title)
