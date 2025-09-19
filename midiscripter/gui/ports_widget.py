from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from midiscripter.base.port_base import Input, SubscribedCall, Port, MultiPort
from midiscripter.midi import MidiIn, MidiOut, MidiIO, MidiPortsChangedIn
from midiscripter.midi.midi_port import _MidiPortMixin
from midiscripter.osc import OscIn, OscOut, OscIO
from midiscripter.ableton_remote import AbletonIn, AbletonOut, AbletonIO
from midiscripter.keyboard import KeyIn, KeyOut, KeyIO
from midiscripter.mouse import MouseIn, MouseOut, MouseIO
from midiscripter.file_event import FileEventIn
from midiscripter.metronome import MetronomeIn
from midiscripter.gui.color_theme import theme_color
from .saved_state_controls import SavedToggleButton


class PortWidgetItem(QTreeWidgetItem):
    def request_state_change(self, state: bool) -> bool:
        raise NotImplementedError


class PortItem(PortWidgetItem):
    __VIRTUAL_PORT_MARKER = 'ⓥ'
    port_instance: Port
    repr: str

    def __init__(self, parent_item: QTreeWidgetItem, port_instance: Port, name_prefix: str = ''):
        self.port_instance = port_instance
        self.repr = repr(self.port_instance)

        item_name = str(self.port_instance)
        if self.port_instance._is_virtual:
            item_name = f'{item_name} {self.__VIRTUAL_PORT_MARKER}'

        super().__init__(parent_item, (f'{name_prefix} {item_name}',))

        self.add_children()

        if not self.port_instance._is_available:
            self.setDisabled(True)
            self.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            if self.port_instance._log_color:
                item_color = theme_color(self.port_instance._log_color)
                self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(item_color))
            self.update_ports_state()

    def update_ports_state(self) -> None:
        if isinstance(self.port_instance, MultiPort):
            wrapped_port_states = [port.is_opened for port in self.port_instance._wrapped_ports]
            if all(wrapped_port_states) != any(wrapped_port_states):
                self.setCheckState(0, Qt.CheckState.PartiallyChecked)
                return

        if self.port_instance.is_opened:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)

    def add_children(self) -> None:
        if isinstance(self.port_instance, MultiPort):
            for port_instance in self.port_instance._input_ports:
                PortItem(self, port_instance, 'In:')

            for port_instance in self.port_instance._output_ports:
                PortItem(self, port_instance, 'Out:')

        if isinstance(self.port_instance, MidiIn):
            for passthrough_out_port in self.port_instance._attached_passthrough_outs:
                PassthroughOutputMidiPortItem(self, passthrough_out_port)

        if isinstance(self.port_instance, Input):
            for _, call_list in self.port_instance._calls:
                for call in call_list:
                    if '._' not in str(call):  # private object method
                        CallItem(self, self.port_instance, call_list, call)

    def request_state_change(
        self: 'GeneralPortItem | MidiPortItem | AlwaysPresentInputPortItem', state: bool
    ) -> None:
        if state:
            self.port_instance._open()

            if self.port_instance.is_opened:
                self.__set_broken_status(False)
                self.setCheckState(0, Qt.CheckState.Checked)
            else:
                self.__set_broken_status(True)
                self.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            self.port_instance._close()
            self.setCheckState(0, Qt.CheckState.Unchecked)

        if isinstance(self.port_instance, MultiPort):
            self.update_ports_state()
            [self.child(n).update_ports_state() for n in range(self.childCount())]

        if isinstance(self.parent(), PortItem):
            self.parent().update_ports_state()

    def __set_broken_status(self, is_broken: bool) -> None:
        if is_broken:
            item_color = QColor().fromRgb(255, 0, 0, 20)
        else:
            item_color = QColor(Qt.GlobalColor.transparent)
        self.setData(0, Qt.ItemDataRole.BackgroundRole, QBrush(item_color))


class PassthroughOutputMidiPortItem(PortItem):
    def request_state_change(self, state: bool) -> None:
        parent_port = self.parent().port_instance
        if state:
            parent_port._attached_passthrough_outs.append(self.port_instance)
        else:
            parent_port._attached_passthrough_outs.remove(self.port_instance)


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

        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(theme_color(call._log_color)))
        self.setCheckState(0, Qt.CheckState.Checked)

    def request_state_change(self, state: bool) -> None:
        if state:
            self.origin_call_list.append(self.call)
        else:
            self.origin_call_list.remove(self.call)


class PortsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('Ports')
        self.setMinimumWidth(175)
        self.setMinimumHeight(200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.ports_view = PortsView()
        layout.addWidget(self.ports_view)

        show_unused_button = SavedToggleButton(
            'Show Unused Ports', self.__set_unused_ports_visibility, default_state=True
        )
        layout.addWidget(show_unused_button)
        self.__set_unused_ports_visibility(bool(show_unused_button))

    def repopulate(self) -> None:
        self.ports_view.populate()

    def __set_unused_ports_visibility(self, show_unused_ports: bool) -> None:
        self.ports_view._show_unused_ports = show_unused_ports
        self.ports_view.update_ports_visibility()


class PortsView(QTreeWidget):
    __update = Signal()

    def __init__(self):
        super().__init__()
        self._show_unused_ports = False

        self.setHeaderHidden(True)
        self.setFrameStyle(QFrame.Shape.NoFrame)

        self.setStyleSheet('QTreeWidget::item::hover {background-color: rgba(0, 183, 255, 10)}')

        self.__port_instances_closed_by_user = []
        self.__ports_declared_in_script = tuple(Port._subclass_instances)

        self.setMouseTracking(True)
        self.itemEntered.connect(self.__update_item_tooltip)

        self.currentItemChanged.connect(self.selectionModel().clear)
        self.itemSelectionChanged.connect(self.__item_selected)
        # with the blocks set itemChanged is emitted only on check state change
        self.itemChanged.connect(self.__item_state_changed)

        self.__update.connect(self.populate)

        midi_ports_updater_port = MidiPortsChangedIn()
        midi_ports_updater_port.subscribe(lambda: self.__update.emit())
        midi_ports_updater_port._open()

    def update_ports_visibility(self) -> None:
        for top_item_index in range(self.topLevelItemCount()):
            port_type_item = self.topLevelItem(top_item_index)

            no_port_type_items_visible = True
            for child_index in range(port_type_item.childCount()):
                port_item: PortItem = port_type_item.child(child_index)

                if (
                    self._show_unused_ports
                    or port_item.port_instance in self.__ports_declared_in_script
                ):
                    port_item.setHidden(False)
                    no_port_type_items_visible = False
                else:
                    port_item.setHidden(True)

            port_type_item.setHidden(no_port_type_items_visible)

    def populate(self) -> None:
        """Populates the widget with items"""
        self.blockSignals(True)

        self.clear()

        self.__add_midi_ports()
        self.__add_declared_ports('OSC', OscIO, OscIn, OscOut)
        self.__add_declared_ports(
            'Other',
            AbletonIO,
            AbletonIn,
            AbletonOut,
            MultiPort,
            KeyIO,
            KeyIn,
            KeyOut,
            MouseIO,
            MouseIn,
            MouseOut,
            MetronomeIn,
            FileEventIn,
        )

        self.update_ports_visibility()

        self.blockSignals(False)

        # Overrides auto setting the first item as current
        self.setCurrentItem(self.invisibleRootItem())

    def __add_top_level_item(self, item_text: str) -> QTreeWidgetItem:
        bold_font = self.font()
        bold_font.setBold(True)

        top_item = QTreeWidgetItem(self, (item_text,))
        top_item.setData(0, Qt.ItemDataRole.FontRole, bold_font)
        top_item.setExpanded(True)

        return top_item

    def __add_midi_ports(self) -> None:
        top_item = self.__add_top_level_item('MIDI')

        virtual_port_names = [
            port._uid for port in _MidiPortMixin._subclass_instances if port._is_virtual
        ]
        midi_to_ableton_class = {MidiIO: AbletonIO, MidiIn: AbletonIn, MidiOut: AbletonOut}

        midi_port_instances = []
        for port_class, ableton_class in midi_to_ableton_class.items():
            midi_port_instances.extend(port_class._class_instances)
            for port_name in port_class._get_available_names():
                if (
                    port_name not in port_class._uid_to_instance
                    and port_name not in ableton_class._uid_to_instance
                    and port_name not in virtual_port_names
                ):
                    midi_port_instances.append(port_class(port_name))  # noqa: PERF401

        midi_port_instances.sort(key=lambda port: not port._is_virtual)
        midi_port_instances.sort(key=lambda port: not port._is_available)

        for port_instance in midi_port_instances:
            # Open newly connected ports that were declared but absent
            if (
                port_instance in self.__ports_declared_in_script
                and port_instance._is_available
                and not port_instance.is_opened
                and port_instance not in self.__port_instances_closed_by_user
            ):
                port_instance._open()
                if port_instance.__class__ is MidiIn:
                    port_instance._call_on_init()

            # Close the ports that became absent
            if (
                not port_instance._is_available
                and port_instance.__class__ is not MidiIO
                and port_instance.is_opened
            ):
                port_instance._close()

            if not port_instance._wrapped_in:
                PortItem(top_item, port_instance)

    def __add_declared_ports(self, title: str, *port_types: type[Port]) -> None:
        port_instances_to_add = []
        for port_type in port_types:
            for port_instance in port_type._class_instances:
                if not port_instance._wrapped_in:
                    port_instances_to_add.append(port_instance)  # noqa: PERF401

        if not port_instances_to_add:
            return

        port_top_item = self.__add_top_level_item(title)

        for port_instance in port_instances_to_add:
            PortItem(port_top_item, port_instance)

    def __item_selected(self) -> None:
        """Sends selected item text to the clipboard and shows a "copied" tooltip"""
        if not self.selectedItems():
            return

        selected_item: PortItem | CallItem = self.selectedItems()[0]

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
                lambda: QToolTip.showText(
                    self.cursor().pos(), f'Copied {text_for_clipboard}', self, msecShowTime=2000
                ),
            )  # Don't hide on mouse button release
        except AttributeError:
            pass

        self.selectionModel().clear()

    def __item_state_changed(self, item: PortWidgetItem, _: int) -> None:
        """Enabled or disables the MIDI port / passthrough out / call according to the checked
        state change"""
        self.blockSignals(True)
        target_state: bool = item.checkState(0) == Qt.CheckState.Checked
        item.request_state_change(target_state)
        self.blockSignals(False)

        if isinstance(item, PortItem):
            if target_state is False:
                self.__port_instances_closed_by_user.append(item.port_instance)
            else:
                try:
                    self.__port_instances_closed_by_user.remove(item.port_instance)
                except ValueError:
                    pass

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
                conditions_str = f'{item.call.conditions[0] or ""}{item.call.conditions[1] or ""}'
            else:
                conditions_str = str(item.call.conditions)
            tooltip_text = f'Conditions: {conditions_str}\n{tooltip_text}'

        self.blockSignals(True)
        item.setData(0, Qt.ItemDataRole.ToolTipRole, tooltip_text)
        self.blockSignals(False)
