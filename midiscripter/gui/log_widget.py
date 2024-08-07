from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.logger.html_sink
from midiscripter.logger import log


class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('Log')

        layout = QGridLayout()
        self.setLayout(layout)

        log_view = LogView()
        layout.addWidget(log_view, 2, 1, 1, 5)

        exclude_line = QLineEdit()
        exclude_line.setPlaceholderText('Substrings divided by ;')
        exclude_line.setClearButtonEnabled(True)
        exclude_line.textChanged.connect(log_view.set_exclude)
        exclude_line.textChanged.connect(
            lambda text: exclude_line.setStyleSheet(
                f'background-color: {"lightgreen" if bool(text) else "white"}'
            )
        )
        exclude_line.setText(QSettings().value('log exclude', ''))
        layout.addWidget(QLabel('Exclude:'), 3, 1, 1, 1)
        layout.addWidget(exclude_line, 3, 2, 1, 1)

        filter_line = QLineEdit()
        filter_line.setPlaceholderText('Substrings divided by ;')
        filter_line.setClearButtonEnabled(True)
        filter_line.textChanged.connect(log_view.set_filter)
        filter_line.textChanged.connect(
            lambda text: filter_line.setStyleSheet(
                f'background-color: {"lightgreen" if bool(text) else "white"}'
            )
        )
        filter_line.setText(QSettings().value('log filter', ''))
        layout.addWidget(QLabel('Filter:'), 3, 3, 1, 1)
        layout.addWidget(filter_line, 3, 4, 1, 1)

        pause_button = QPushButton('Pause')
        pause_button.setToolTip('Pause the logging')
        pause_button.setCheckable(True)
        pause_button.toggled.connect(
            lambda state: log_view.pause_logging() if state else log_view.resume_logging()
        )
        pause_button.setFixedWidth(50)
        layout.addWidget(pause_button, 3, 5, 1, 1, Qt.AlignmentFlag.AlignRight)


class LogView(QPlainTextEdit):
    append_html_entry = Signal(list)
    entry_ctime_part_len = len(log._get_precise_time_stamp()) + 2

    def __init__(self):
        super().__init__()
        self.__anchor_text: str | None = None
        self.__filter_text_parts = []
        self.__exclude_text_parts = []

        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setMaximumBlockCount(log.BUFFER_SIZE)
        self.setMouseTracking(True)

        self.setFrameStyle(QFrame.Shape.NoFrame)

        self.append_html_entry.connect(self.__add_entry)
        self.resume_logging()

    @Slot(str)
    def set_filter(self, filter_text: str) -> None:
        self.__filter_text_parts = [
            text.lower().strip().strip("'") for text in filter_text.split(';') if text.strip()
        ]
        self.__apply_filter()
        QSettings().setValue('log filter', filter_text)

    @Slot(str)
    def set_exclude(self, exclude_text: str) -> None:
        self.__exclude_text_parts = [
            text.lower().strip().strip("'") for text in exclude_text.split(';') if text.strip()
        ]
        self.__apply_filter()
        QSettings().setValue('log exclude', exclude_text)

    def __apply_filter(self, to_last_n_blocks: int = 0) -> None:
        self.__set_lines_visibility(to_last_n_blocks)
        if not to_last_n_blocks:
            self.__clear_highlighting()
        self.__highlight_filter_matches(to_last_n_blocks)

    def __set_lines_visibility(self, last_n_blocks: int = 0) -> None:
        document = self.document()

        start_from_block_number = 0 if not last_n_blocks else document.blockCount() - last_n_blocks

        previous_visible_entry = None
        for line_n in range(start_from_block_number, document.blockCount()):
            block = document.findBlockByNumber(line_n)
            log_entry = block.text()[self.entry_ctime_part_len :]

            if log_entry and (  # noqa: SIM114
                self.__text_line_is_excluded(log_entry)
                or not self.__text_line_matches_filter(log_entry)
            ):
                block.setVisible(False)
            elif not log_entry and not previous_visible_entry:  # two separators in a row
                block.setVisible(False)
            else:
                block.setVisible(True)
                previous_visible_entry = log_entry

        self.setDocument(document)

    def __text_line_is_excluded(self, text_line: str) -> bool:
        if not self.__exclude_text_parts:
            return False
        return any(text in text_line.lower() for text in self.__exclude_text_parts)

    def __text_line_matches_filter(self, text_line: str) -> bool:
        if not self.__filter_text_parts:
            return True
        return any(text in text_line.lower() for text in self.__filter_text_parts)

    def __clear_highlighting(self) -> None:
        text_format = QTextCharFormat()
        text_format.setBackground(QBrush(Qt.NoBrush))

        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(text_format)

    def __highlight_filter_matches(self, last_n_blocks: int = 0) -> None:
        if not self.__filter_text_parts:
            return

        cursor = self.textCursor()

        text_format = QTextCharFormat()
        text_format.setBackground(QBrush(QColor('yellow')))

        if not last_n_blocks:
            start_from = 0
        else:
            document = self.document()
            first_new_block = document.findBlockByNumber(document.blockCount() - last_n_blocks)
            start_from = first_new_block.position()

        for filter_word in self.__filter_text_parts:
            regex = QRegularExpression(filter_word, QRegularExpression.CaseInsensitiveOption)
            match_iter = regex.globalMatch(self.toPlainText(), start_from)

            while match_iter.hasNext():
                match = match_iter.next()
                cursor.setPosition(match.capturedStart())
                cursor.movePosition(
                    QTextCursor.MoveOperation.NextCharacter,
                    QTextCursor.MoveMode.KeepAnchor,
                    match.capturedLength(),
                )
                cursor.mergeCharFormat(text_format)

    @Slot(list)
    def __add_entry(self, log_entries: list[str]) -> None:
        [self.appendHtml(f'<div>{entry}</div>') for entry in log_entries]
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

        if self.__filter_text_parts or self.__exclude_text_parts:
            self.__apply_filter(len(log_entries) + 1)

    @staticmethod
    def pause_logging() -> None:
        log._sink = None

    def resume_logging(self) -> None:
        log._sink = midiscripter.logger.html_sink.HtmlSink(self.append_html_entry.emit)

    def hideEvent(self, event: QHideEvent) -> None:
        self.pause_logging()
        super().hideEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        self.resume_logging()
        super().showEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.__anchor_text = self.anchorAt(event.pos())
        if self.__anchor_text:
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self.__anchor_text or event.button() != Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)
            return

        if QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            text_for_clipboard = self.__anchor_text[
                self.__anchor_text.find('(') + 1 : self.__anchor_text.rfind(')')
            ]
        else:
            text_for_clipboard = self.__anchor_text

        QGuiApplication.clipboard().setText(text_for_clipboard)
        QApplication.instance().main_window.message_sender_widget.paste(text_for_clipboard)

        QToolTip().showText(
            event.globalPosition().toPoint(),
            f'Copied {text_for_clipboard}',
            self,
            msecShowTime=2000,
        )
        super().mouseReleaseEvent(event)
