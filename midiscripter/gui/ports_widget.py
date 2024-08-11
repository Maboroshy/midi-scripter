import itertools

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from midiscripter.base.port_base import Input, Output, SubscribedCall, Port
from midiscripter.midi import MidiIn, MidiOut, MidiPortsChangedIn
from midiscripter.osc import OscIn, OscOut
from midiscripter.ableton_remote import AbletonIn, AbletonOut
from midiscripter.keyboard import KeyIn, KeyOut
from midiscripter.mouse import MouseIn, MouseOut
from midiscripter.file_event import FileEventIn
from midiscripter.metronome import MetronomeIn
from midiscripter.logger import log
from .saved_state_controls import SavedToggleButton


class PortWidgetItem(QTreeWidgetItem):
    def request_state_change(self, state: bool) -> bool:
        raise NotImplementedError


class PortItemMixin:
    port_instance: Input | Output
    is_broken: bool = False

    def request_state_change(
        self: 'GeneralPortItem | MidiPortItem | KeyInputPortItem', state: bool
    ) -> bool:
        if state:
            if not self.port_instance.is_enabled:
                self.port_instance._open()

                if self.port_instance.is_enabled:
                    self.set_broken_status(False)
                    log('Enabled {port}', port=self.port_instance)
                    return True
                else:
                    self.set_broken_status(True)
                    log.red("Can't enable {port}", port=self.port_instance)
                    return False
            else:
                # Clear possible "broken port" background
                self.set_broken_status(False)
                return True
        else:
            self.port_instance.is_enabled = False
            log('Disabled {port}', port=self.port_instance)
            return False

    def set_broken_status(self, is_broken: bool) -> None:
        self.is_broken = is_broken
        if is_broken:
            item_color = QColor().fromRgb(255, 0, 0, 20)
        else:
            item_color = QColor(Qt.GlobalColor.transparent)
        self.setData(0, Qt.ItemDataRole.BackgroundRole, QBrush(item_color))

    def add_calls(self: 'GeneralPortItem | MidiPortItem') -> None:
        for _, call_list in self.port_instance.calls:
            for call in call_list:
                CallItem(self, self.port_instance, call_list, call)


class GeneralPortItem(PortItemMixin, PortWidgetItem):
    port_instance: Input | Output

    def __init__(self, parent_item: QTreeWidgetItem, port_instance: Input | Output):
        self.port_instance = port_instance
        self.repr = self.port_instance.__repr__()

        item_text = self.port_instance._force_uid or str(self.port_instance._uid)
        super().__init__(parent_item, (item_text,))

        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(f'dark{port_instance._gui_color}'))

        if self.port_instance.is_enabled:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)

        if issubclass(type(self.port_instance), Input):
            self.add_calls()


class AlwaysPresentInputPortItem(PortItemMixin, PortWidgetItem):
    port_class: type[KeyIn | MouseIn]
    port_instance: None | KeyIn | MouseIn

    def __init__(self, parent_item: QTreeWidgetItem, port_class: type[KeyIn | MouseIn]):
        self.port_class = port_class
        super().__init__(parent_item, (self.port_class._force_uid,))

        self.repr = f'{port_class.__name__}()'
        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(f'dark{port_class._gui_color}'))

        self.port_instance = self.port_class._name_to_instance.get(self.port_class._force_uid, None)
        if self.port_instance and self.port_instance.is_enabled:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)

    def request_state_change(self, state: bool) -> bool:
        if not self.port_instance:
            self.port_instance = self.port_class()
        return PortItemMixin.request_state_change(self, state)


class AbsentMidiPortItem(PortWidgetItem):
    port_instance: Input | Output

    def __init__(self, parent_item: QTreeWidgetItem, port_instance: Input | Output):
        super().__init__(parent_item, (port_instance._uid,))
        self.port_instance = port_instance
        self.setDisabled(True)
        self.setCheckState(0, Qt.CheckState.Unchecked)


class MidiPortItem(PortItemMixin, PortWidgetItem):
    port_instance: None | MidiIn | MidiOut
    PORT_CLASS: type[MidiIn | MidiOut]
    VIRTUAL_PORT_PREFIX = '[v]'

    def __init__(self, parent_item: QTreeWidgetItem, port_name: str):
        self.port_name = port_name
        self.port_instance = self.PORT_CLASS._name_to_instance.get(self.port_name, None)
        self.repr = f"{self.PORT_CLASS.__name__}('{self.port_name}')"

        if self.port_instance and self.port_instance._is_virtual:
            item_name = f'{self.VIRTUAL_PORT_PREFIX} {self.port_name}'
        else:
            item_name = self.port_name

        super().__init__(parent_item, (item_name,))

        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(f'dark{self.PORT_CLASS._gui_color}'))

        if not self.port_instance:
            self.setCheckState(0, Qt.CheckState.Unchecked)
        elif self.port_instance.is_enabled:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)
            self.setData(0, Qt.ItemDataRole.BackgroundRole, QBrush(QColor().fromRgb(255, 0, 0, 20)))

    def request_state_change(self, state: bool) -> bool:
        if not self.port_instance:
            self.port_instance = self.PORT_CLASS(self.port_name)
        return PortItemMixin.request_state_change(self, state)


class InputMidiPortItem(MidiPortItem):
    PORT_CLASS = MidiIn

    def __init__(self, parent_item: QTreeWidgetItem, port_name: str):
        super().__init__(parent_item, port_name)

        if self.port_instance:
            for passthrough_out_port in self.port_instance.attached_passthrough_outs:
                PassthroughOutputMidiPortItem(self, passthrough_out_port._uid)

            self.add_calls()


class OutputMidiPortItem(MidiPortItem):
    PORT_CLASS = MidiOut


class PassthroughOutputMidiPortItem(OutputMidiPortItem):
    def request_state_change(self, state: bool) -> bool:
        parent_port = self.parent().port_instance
        if state:
            parent_port.attached_passthrough_outs.append(self.port_instance)
        else:
            parent_port.attached_passthrough_outs.remove(self.port_instance)
        return state


class CallItem(PortWidgetItem):
    def __init__(
        self,
        parent_item: QTreeWidgetItem,
        port_instance: Input,
        origin_call_list: list[SubscribedCall],
        call: SubscribedCall,
    ):
        super().__init__(parent_item, (str(call),))
        self.port_instance = port_instance
        self.origin_call_list = origin_call_list
        self.call = call

        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(f'dark{call._gui_color}'))
        self.setCheckState(0, Qt.CheckState.Checked)

    def request_state_change(self, state: bool) -> bool:
        if state:
            self.origin_call_list.append(self.call)
        else:
            self.origin_call_list.remove(self.call)
        return state


class PortsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('Ports')
        self.setMinimumWidth(175)
        self.setMinimumHeight(200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        ports_view = PortsView()
        layout.addWidget(ports_view)

        hide_unused_button = SavedToggleButton(
            'Show Unused Ports', ports_view.set_unused_ports_visibility, default_state=True
        )
        layout.addWidget(hide_unused_button)


class PortsView(QTreeWidget):
    __ALWAYS_PRESENT_PORT_TYPES = (KeyIn, MouseIn)

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setFrameStyle(QFrame.Shape.NoFrame)

        self.__populate()
        self.__ports_declared_in_script = Port._instances

        self.setMouseTracking(True)
        self.itemEntered.connect(self.__update_item_tooltip)

        self.itemSelectionChanged.connect(self.__item_selected)
        # with the blocks set itemChanged is emitted only on check state change
        self.itemChanged.connect(self.__item_state_changed)

    def set_unused_ports_visibility(self, unused_are_visible: bool) -> None:
        for top_item_index in range(self.topLevelItemCount()):
            port_type_item = self.topLevelItem(top_item_index)

            no_port_type_items_visible = True
            for child_index in range(port_type_item.childCount()):
                port_item: PortWidgetItem = port_type_item.child(child_index)

                if unused_are_visible or port_item.port_instance in self.__ports_declared_in_script:
                    port_item.setHidden(False)
                    no_port_type_items_visible = False
                else:
                    port_item.setHidden(True)

            port_type_item.setHidden(no_port_type_items_visible)

    def __populate(self) -> None:
        """Populates the widget with items"""
        self.blockSignals(True)

        self.__add_midi_ports()

        self.__add_declared_ports('OSC', OscIn, OscOut)
        self.__add_declared_ports('Ableton Live', AbletonIn, AbletonOut)
        self.__add_declared_ports('Keyboard', KeyIn, KeyOut)
        self.__add_declared_ports('Mouse', MouseIn, MouseOut)

        self.__add_declared_ports('Metronome', MetronomeIn)
        self.__add_declared_ports('File Event Watcher', FileEventIn)
        self.__add_declared_ports('MIDI Port Changes Watcher', MidiPortsChangedIn)

        self.blockSignals(False)

    def __add_top_level_item(self, item_text: str) -> QTreeWidgetItem:
        bold_font = self.font()
        bold_font.setBold(True)

        top_item = QTreeWidgetItem(self, (item_text,))
        top_item.setData(0, Qt.ItemDataRole.FontRole, bold_font)
        top_item.setExpanded(True)

        return top_item

    def __add_midi_ports(self) -> None:
        for title, item_class in [
            ('MIDI Inputs', InputMidiPortItem),
            ('MIDI Outputs', OutputMidiPortItem),
        ]:
            top_item = self.__add_top_level_item(title)
            port_class = item_class.PORT_CLASS

            ableton_port_instances = itertools.chain(AbletonIn._instances, AbletonOut._instances)
            ableton_remote_port_names = [port.name for port in ableton_port_instances]

            virtual_port_names = [port._uid for port in port_class._instances if port._is_virtual]
            for port_name in virtual_port_names:
                if port_name not in ableton_remote_port_names:
                    item_class(top_item, port_name)

            for port_name in port_class._available_names:
                if port_name in ableton_remote_port_names:
                    continue
                item_class(top_item, port_name)

            for port_instance in port_class._instances:
                if not port_instance._is_available and port_instance._uid not in virtual_port_names:
                    AbsentMidiPortItem(top_item, port_instance)

    def __add_declared_ports(self, title: str, *port_types: type[Input | Output]) -> None:
        always_present_port_types_to_add = []
        port_instances_to_add = []
        for port_type in port_types:
            if port_type in self.__ALWAYS_PRESENT_PORT_TYPES:
                always_present_port_types_to_add.append(port_type)

            for port_instance in port_type._instances:
                if port_type not in always_present_port_types_to_add:
                    port_instances_to_add.append(port_instance)  # noqa: PERF401

        if not port_instances_to_add and not always_present_port_types_to_add:
            return

        port_top = self.__add_top_level_item(title)

        for port_type in always_present_port_types_to_add:
            AlwaysPresentInputPortItem(port_top, port_type)

        for port_instance in port_instances_to_add:
            GeneralPortItem(port_top, port_instance)

    def __item_selected(self) -> None:
        """Sends selected item text to the clipboard and shows a "copied" tooltip"""
        if not self.selectedItems():
            return

        selected_item: MidiPortItem | GeneralPortItem | CallItem = self.selectedItems()[0]

        try:
            if QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
                text_for_clipboard = selected_item.repr[
                    selected_item.repr.find('(') + 1 : selected_item.repr.rfind(')')
                ]
            else:
                text_for_clipboard = selected_item.repr

            QGuiApplication.clipboard().setText(text_for_clipboard)
            QTimer.singleShot(
                200,
                lambda: QToolTip().showText(
                    self.cursor().pos(), f'Copied {text_for_clipboard}', self, msecShowTime=2000
                ),
            )  # Don't hide on mouse button release
        except AttributeError:
            pass

        selected_item.setSelected(False)

    def __item_state_changed(self, item: PortWidgetItem, _: int) -> None:
        """Enabled or disables the MIDI port / passthrough out / call according to the checked
        state change"""
        self.blockSignals(True)
        target_state: bool = item.checkState(0) == Qt.CheckState.Checked
        new_item_state = item.request_state_change(target_state)
        item.setCheckState(0, (Qt.CheckState.Unchecked, Qt.CheckState.Checked)[new_item_state])
        self.blockSignals(False)

        QApplication.instance().main_window.message_sender_widget.update_ports()

    def __update_item_tooltip(self, item: QTreeWidgetItem) -> None:
        """Updates items tooltip on hover"""
        if not isinstance(item, CallItem):
            return

        call_statistics = list(item.call.statistics)

        if not call_statistics:
            tooltip_text = 'No calls made yet'
        else:
            call_statistics.sort()
            tooltip_text = (
                f'Execution time for last {len(call_statistics)} calls:\n'
                f'Min: {call_statistics[0]} ms; '
                f'Med: {call_statistics[int(len(call_statistics) / 2)]} ms; '
                f'Max: {call_statistics[-1]} ms'
            )

        if item.call.conditions:
            if isinstance(item.call.conditions, tuple):
                conditions_str = f'{item.call.conditions[0] or ''}{item.call.conditions[1] or ''}'
            else:
                conditions_str = str(item.call.conditions)
            tooltip_text = f'Conditions: {conditions_str}\n{tooltip_text}'

        self.blockSignals(True)
        item.setData(0, Qt.ItemDataRole.ToolTipRole, tooltip_text)
        self.blockSignals(False)
