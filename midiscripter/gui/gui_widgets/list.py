from typing import overload

from PySide6.QtWidgets import *

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

        self.__content = None
        self.currentRowChanged.connect(self.selection_changed_signal)

    def get_content(self) -> tuple[str]:
        return self.__content

    def set_content(self, list_items: tuple[str]) -> None:
        self.__content = list_items
        self.addItems(self.__content)

    def set_selection(self, selection: int | str) -> None:
        if isinstance(selection, int):
            self.setCurrentRow(selection)
        else:
            try:
                self.setCurrentRow(self.__content.index(selection))
            except ValueError:
                pass

    def get_selected_item_index(self) -> int | None:
        return self.currentRow()

    def get_selected_item_text(self) -> str | None:
        return self.__content[self.currentRow()]


class GuiListSelector(GuiWidget):
    """List of text items to select value."""

    _qt_widget_class = ListSelectorWidget

    @overload
    def __init__(
        self,
        title: str,
        content: tuple[str, ...],
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ): ...

    @overload
    def __init__(
        self,
        content: tuple[str, ...],
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ): ...

    def __init__(
        self,
        title_and_content: str | tuple[str, ...],
        content: tuple[str, ...] | None = None,
        *,
        color: str | tuple[int, int, int] | None = None,
        select: int | str | None = None,
    ):
        """
        **Overloads:**
            ``` python
            GuiListSelector(
                title: str,
                content: tuple[str, ...],
                *,
                color: str | tuple[int, int, int] | None = None,
                select: int | str | None = None
            )
            ```
            ``` python
            GuiListSelector(
                content: tuple[str, ...],
                *,
                color: str | tuple[int, int, int] | None = None,
                select: int | str | None = None
            )
            ```

        Args:
            title (str): Widget's title
            content: Items' texts
            color: Text color as [color name](https://www.w3.org/TR/SVG11/types.html#ColorKeywords) or RGB tuple
            select: Text or index of item to select initially
        """
        super().__init__(title_and_content, content, color=color, select=select)
