import inspect
import re

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from midiscripter.base.port_base import Output
from midiscripter.base.msg_base import AttrEnum, Msg

# Imports used by `eval`
from midiscripter.midi import MidiMsg, ChannelMsg, SysexMsg, MidiType
from midiscripter.osc import OscMsg
from midiscripter.ableton_remote import AbletonMsg, AbletonEvent
from midiscripter.keyboard import KeyMsg, KeyEvent
from midiscripter.mouse import MouseMsg, MouseEvent
from midiscripter.file_event import FileEventMsg, FileEvent
from .gui_widgets.gui_msg import GuiEventMsg, GuiEvent


class MessageSender(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('Message Sender')
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setMinimumWidth(220)

        layout = QGridLayout()
        self.setLayout(layout)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText('Message Representation')
        self.input_line.setClearButtonEnabled(True)
        layout.addWidget(self.input_line, 0, 0)
        self.input_line.textChanged.connect(self.__parse_input)

        self.copy_button = QPushButton('Copy')
        self.copy_button.setFixedWidth(50)
        layout.addWidget(self.copy_button, 0, 1)
        self.copy_button.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(self.input_line.text())
        )

        self.output_selector = QComboBox()
        layout.addWidget(self.output_selector, 1, 0)
        self.update_ports()
        self.output_selector.currentIndexChanged.connect(self.__set_output)

        self.send_button = QPushButton('&Send')
        self.send_button.setFixedWidth(50)
        self.send_button.setShortcut(
            QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_S)
        )
        layout.addWidget(self.send_button, 1, 1)
        self.send_button.setDisabled(True)
        self.send_button.clicked.connect(self.__send_message)

        self.msg = None
        self.output = None

    def paste(self, input_text: str) -> None:
        current_text = self.input_line.text()
        self.input_line.setText(input_text)
        if not self.msg:
            self.input_line.setText(current_text)

    def wheelEvent(self, event: QWheelEvent) -> None:
        text = self.input_line.text()
        cursor_pos = self.input_line.cursorPosition()

        for item_match in re.finditer(r'[^,() ]+', text):
            start_pos, end_pos = item_match.span()
            if start_pos <= cursor_pos <= end_pos:
                item_text = item_match.group(0)
                break
        else:
            return

        try:
            item_obj = eval(item_text)
        except (NameError, AttributeError):
            return

        if isinstance(item_obj, bool):
            new_item_obj = not item_obj
        elif isinstance(item_obj, int):
            new_item_obj = item_obj + 1 if event.angleDelta().y() > 0 else item_obj - 1
        elif isinstance(item_obj, AttrEnum):
            enum_class = item_obj.__class__
            enum_members = list(enum_class.__members__)
            member_index = enum_members.index(item_obj)
            new_index = member_index + 1 if event.angleDelta().y() > 0 else member_index - 1
            if new_index == -1 or new_index == len(enum_members):
                return
            new_item_obj = enum_class[enum_members[new_index]]
        else:
            return

        new_item_obj_repr = repr(new_item_obj)
        self.input_line.setText(text[:start_pos] + new_item_obj_repr + text[end_pos:])
        self.input_line.setCursorPosition(start_pos + len(new_item_obj_repr))

    def update_ports(self) -> None:
        self.output_selector.clear()

        enabled_ports = [output for output in Output._instances if output.is_enabled]

        if not enabled_ports:
            self.output_selector.setPlaceholderText('No Enabled Output Ports')
            self.output_selector.setDisabled(True)
            return

        self.output_selector.setPlaceholderText('Output Port')
        self.output_selector.setDisabled(False)

        for port in enabled_ports:
            self.output_selector.addItem(f'{str(port._uid)} ({port.__class__.__name__})', port)
        self.output_selector.currentIndexChanged.connect(self.__set_output)

    def __set_output(self, _: int) -> None:
        self.output = self.output_selector.currentData(Qt.ItemDataRole.UserRole)
        self.__validate()

    def __parse_input(self, input_text: str) -> None:
        try:
            object_for_input = eval(input_text)
            self.msg = object_for_input if isinstance(object_for_input, Msg) else None
        except Exception:
            self.msg = None
        self.__validate()

    def __validate(self) -> None:
        input_line_bg_color = 'white' if self.msg or not self.input_line.text() else 'pink'
        self.input_line.setStyleSheet(f'background-color: {input_line_bg_color}')

        if not self.output or not self.msg:
            self.send_button.setDisabled(True)
        else:
            valid_msg_type = inspect.get_annotations(self.output.send)['msg']
            self.send_button.setDisabled(not isinstance(self.msg, valid_msg_type))

    def __send_message(self) -> None:
        self.output.send(self.msg)
