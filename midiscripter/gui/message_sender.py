import inspect

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from midiscripter.base.port_base import Output

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
        self.output_selector.setPlaceholderText('Output Port')
        layout.addWidget(self.output_selector, 1, 0)
        for port_name, port_instance in Output._instances.items():
            self.output_selector.addItem(
                f'{str(port_name)} ({port_instance.__class__.__name__})', port_instance
            )
        self.output_selector.currentIndexChanged.connect(self.__set_output)

        self.send_button = QPushButton('Send')
        self.send_button.setFixedWidth(50)
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

    def __set_output(self, _: int) -> None:
        self.output = self.output_selector.currentData(Qt.ItemDataRole.UserRole)
        self.__validate()

    def __parse_input(self, input_text: str) -> None:
        try:
            self.msg = eval(input_text)
        except Exception:
            self.msg = None
        self.__validate()

    def __validate(self) -> None:
        self.input_line.setStyleSheet(
            f'background-color: {"white" if self.msg or not self.input_line.text() else "pink"}'
        )

        if not self.output or not self.msg:
            self.send_button.setDisabled(True)
        else:
            valid_msg_type = inspect.get_annotations(self.output.send)['msg']
            self.send_button.setDisabled(not isinstance(self.msg, valid_msg_type))

    def __send_message(self) -> None:
        self.output.send(self.msg)
