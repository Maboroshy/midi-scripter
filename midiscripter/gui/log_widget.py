import collections
import re
from collections.abc import Collection

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.logger.html
from midiscripter.logger import log


class LogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('Log')

        layout = QGridLayout()
        self.setLayout(layout)

        self.log_view = LogView()
        layout.addWidget(self.log_view, 2, 1, 1, 5)

        self.exclude_line = QLineEdit()
        self.exclude_line.setPlaceholderText('Substrings divided by ;')
        self.exclude_line.setClearButtonEnabled(True)
        self.exclude_line.textChanged.connect(self.log_view.set_exclude)
        self.exclude_line.textChanged.connect(
            lambda text: self.exclude_line.setStyleSheet(
                f'background-color: {"lightgreen" if bool(text) else "white"}'
            )
        )
        self.exclude_line.setText(QSettings().value('log exclude', ''))
        layout.addWidget(QLabel('Exclude:'), 3, 1, 1, 1)
        layout.addWidget(self.exclude_line, 3, 2, 1, 1)

        self.filter_line = QLineEdit()
        self.filter_line.setPlaceholderText('Substrings divided by ;')
        self.filter_line.setClearButtonEnabled(True)
        self.filter_line.textChanged.connect(self.log_view.set_filter)
        self.filter_line.textChanged.connect(
            lambda text: self.filter_line.setStyleSheet(
                f'background-color: {"lightgreen" if bool(text) else "white"}'
            )
        )
        self.filter_line.setText(QSettings().value('log filter', ''))
        layout.addWidget(QLabel('Filter:'), 3, 3, 1, 1)
        layout.addWidget(self.filter_line, 3, 4, 1, 1)

        pause_button = QPushButton('&Pause')
        pause_button.setToolTip('Pause the logging')
        pause_button.setCheckable(True)
        pause_button.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_P))
        pause_button.toggled.connect(lambda state: setattr(log, 'flushing_is_enabled', not state))
        pause_button.setFixedWidth(50)
        layout.addWidget(pause_button, 3, 5, 1, 1, Qt.AlignmentFlag.AlignRight)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.keyCombination() == QKeyCombination(
            Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_F
        ):
            self.filter_line.setText(self.log_view.textCursor().selectedText())

        if event.keyCombination() == QKeyCombination(
            Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_E
        ):
            self.exclude_line.setText(self.log_view.textCursor().selectedText())


class LogView(QPlainTextEdit):
    append_html_entry = Signal(list)
    entry_ctime_part_len = len(f'{log._get_precise_timestamp()}: ')

    def __init__(self):
        super().__init__()
        self.__anchor_text: str | None = None
        self.__filter_text_parts = []
        self.__exclude_text_parts = []
        self.__log_content = collections.deque(maxlen=log.BUFFER_SIZE)
        self.__previous_filtered_entry_text = None

        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setMaximumBlockCount(log.BUFFER_SIZE)
        self.setMouseTracking(True)

        self.setFrameStyle(QFrame.Shape.NoFrame)

        self.append_html_entry.connect(self.__add_entries)

        log._formatter = midiscripter.logger.html.html_log_formatter
        log._sink = self.append_html_entry.emit
        log._flushing_is_enabled = True

    @Slot(str)
    def set_filter(self, filter_text: str) -> None:
        self.__filter_text_parts = [
            text.lower().strip().strip("'") for text in filter_text.split(';') if text.strip()
        ]
        QSettings().setValue('log filter', filter_text)
        self.__apply_filter()

    @Slot(str)
    def set_exclude(self, exclude_text: str) -> None:
        self.__exclude_text_parts = [
            text.lower().strip().strip("'") for text in exclude_text.split(';') if text.strip()
        ]
        QSettings().setValue('log exclude', exclude_text)
        self.__apply_filter()

    def __text_line_is_excluded(self, text_line: str) -> bool:
        if not self.__exclude_text_parts:
            return False
        return any(text in text_line.lower() for text in self.__exclude_text_parts)

    def __text_line_matches_filter(self, text_line: str) -> bool:
        if not self.__filter_text_parts:
            return True
        return any(text in text_line.lower() for text in self.__filter_text_parts)

    def __filter_entries(self, log_entries: Collection[str]) -> list[str]:
        filtered_entries = []
        for entry in log_entries:
            entry_plain_text = re.sub(r'<.*?>', '', entry)
            log_msg_text = entry_plain_text[self.entry_ctime_part_len :]

            if log_msg_text and (  # noqa: SIM114
                self.__text_line_is_excluded(log_msg_text)
                or not self.__text_line_matches_filter(log_msg_text)
            ):
                continue
            elif (
                not log_msg_text and not self.__previous_filtered_entry_text
            ):  # two separators in a row
                continue
            else:
                filtered_entries.append(entry)
                self.__previous_filtered_entry_text = log_msg_text

        return filtered_entries

    def __clear_highlighting(self) -> None:
        text_format = QTextCharFormat()
        text_format.setBackground(QBrush(Qt.NoBrush))
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeCharFormat(text_format)

    def __highlight_filter_matches(self, last_n_blocks: int = 0) -> None:
        if not self.__filter_text_parts:
            return

        document: QTextDocument = self.document()
        cursor: QTextCursor = self.textCursor()

        text_format = QTextCharFormat()
        text_format.setBackground(QBrush(QColor('yellow')))

        if not last_n_blocks:
            start_from = 0
        else:
            first_new_block = document.findBlockByNumber(document.blockCount() - last_n_blocks)
            start_from = first_new_block.position()

        for filter_word in self.__filter_text_parts:
            regex = QRegularExpression(filter_word, QRegularExpression.CaseInsensitiveOption)
            match_iter = regex.globalMatch(self.toPlainText(), start_from)

            while match_iter.hasNext():
                match = match_iter.next()

                text_block: QTextBlock = document.findBlock(match.capturedStart())
                if match.capturedStart() < text_block.position() + self.entry_ctime_part_len:
                    continue

                cursor.setPosition(match.capturedStart())
                cursor.movePosition(
                    QTextCursor.MoveOperation.NextCharacter,
                    QTextCursor.MoveMode.KeepAnchor,
                    match.capturedLength(),
                )
                cursor.mergeCharFormat(text_format)

    def __print_entries(self, log_entries: Collection[str]) -> None:
        self.appendHtml(''.join(log_entries))

    @Slot(list)
    def __add_entries(self, log_entries: Collection[str]) -> None:
        self.__log_content.extend(log_entries)

        if self.__filter_text_parts or self.__exclude_text_parts:
            filtered_entries = self.__filter_entries(log_entries)
            if filtered_entries:
                self.__print_entries(filtered_entries)
            if self.__filter_text_parts:
                self.__highlight_filter_matches(len(filtered_entries))
        else:
            self.__print_entries(log_entries)

        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def __apply_filter(self) -> None:
        self.clear()
        if self.__filter_text_parts or self.__exclude_text_parts:
            filtered_entries = self.__filter_entries(self.__log_content)
            self.__print_entries(filtered_entries)
            self.__highlight_filter_matches(len(filtered_entries))
        else:
            self.__print_entries(self.__log_content)
            self.__clear_highlighting()

    def hideEvent(self, event: QHideEvent) -> None:
        log._flushing_is_enabled = False
        super().hideEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        log._flushing_is_enabled = True
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
