import itertools
from collections.abc import Callable

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.logger.html_sink
from midiscripter.base.port_base import Input, Output
from midiscripter.logger import log
from midiscripter.midi import MidiIn, MidiOut
from midiscripter.keyboard import KeyIn
from midiscripter.mouse import MouseIn


class PortWidgetItem(QTreeWidgetItem):
    def request_state_change(self, new_state: bool) -> bool:
        raise NotImplementedError


class PortItemMixin:
    port_instance: Input | Output

    def set_color_by_port_type(
        self: 'GeneralPortItem | MidiPortItem', port_type: type[Input | Output]
    ) -> None:
        if issubclass(port_type, Input):
            item_color = midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Input]
        else:
            item_color = midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Output]
        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(item_color))

    def request_state_change(
        self: 'GeneralPortItem | MidiPortItem | KeyInputPortItem', new_state: bool
    ) -> bool:
        if new_state:
            if not self.port_instance.is_enabled:
                self.port_instance._open()

                if self.port_instance.is_enabled:
                    log('Enabled {port}', port=self.port_instance)
                    return True
                else:
                    # Set "broken port" background
                    self.setData(
                        0,
                        Qt.ItemDataRole.BackgroundRole,
                        QBrush(QColor().fromRgb(255, 0, 0, 20)),
                    )
                    log.red("Can't enable {port}", port=self.port_instance)
                    return False
            else:
                # Clear possible "broken port" background
                self.setData(
                    0,
                    Qt.ItemDataRole.BackgroundRole,
                    QBrush(QColor(Qt.GlobalColor.transparent)),
                )
                return True
        else:
            self.port_instance.is_enabled = False
            log('Disabled {port}', port=self.port_instance)
            return False

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

        self.set_color_by_port_type(type(self.port_instance))
        self.setCheckState(0, Qt.CheckState.Checked)

        if issubclass(type(self.port_instance), Input):
            self.add_calls()


class AlwaysPresentInputPortItem(PortItemMixin, PortWidgetItem):
    port_class: type[KeyIn | MouseIn]
    port_instance: None | KeyIn | MouseIn

    def __init__(self, parent_item: QTreeWidgetItem, port_class: type[KeyIn | MouseIn]):
        self.port_class = port_class
        super().__init__(parent_item, (self.port_class._force_uid,))

        self.repr = f'{port_class.__name__}()'

        item_color = midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Input]
        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(item_color))

        try:
            port_index = (port_class.__name__, self.port_class._force_uid)
            self.port_instance = self.port_class.instance_registry[port_index]
            self.setCheckState(0, Qt.CheckState.Checked)
        except KeyError:
            self.port_instance = None
            self.setCheckState(0, Qt.CheckState.Unchecked)

    def request_state_change(self, new_state: bool) -> bool:
        if not self.port_instance:
            self.port_instance = self.port_class()
        return PortItemMixin.request_state_change(self, new_state)


class AbsentMidiPortItem(QTreeWidgetItem):
    def __init__(self, parent_item: QTreeWidgetItem, port_name: str):
        super().__init__(parent_item, (port_name,))
        self.setDisabled(True)
        self.setCheckState(0, Qt.CheckState.Unchecked)


class MidiPortItem(PortItemMixin, PortWidgetItem):
    port_instance: MidiIn | MidiOut
    PORT_CLASS: type[MidiIn | MidiOut]
    VIRTUAL_PORT_PREFIX = '[v]'

    def __init__(self, parent_item: QTreeWidgetItem, port_name: str):
        self.port_name = port_name
        port_key = (self.PORT_CLASS.__name__, self.port_name)
        self.port_instance = self.PORT_CLASS.instance_registry.get(port_key, None)
        self.repr = f"{self.PORT_CLASS.__name__}('{self.port_name}')"

        if self.port_instance and self.port_instance._is_virtual:
            item_name = f'{self.VIRTUAL_PORT_PREFIX} {self.port_name}'
        else:
            item_name = self.port_name

        super().__init__(parent_item, (item_name,))

        self.set_color_by_port_type(self.PORT_CLASS)

        if not self.port_instance:
            self.setCheckState(0, Qt.CheckState.Unchecked)
        elif self.port_instance.is_enabled:
            self.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.setCheckState(0, Qt.CheckState.Unchecked)
            self.setData(0, Qt.ItemDataRole.BackgroundRole, QBrush(QColor().fromRgb(255, 0, 0, 20)))

    def request_state_change(self, new_state: bool) -> bool:
        if not self.port_instance:
            self.port_instance = self.PORT_CLASS(self.port_name)
        return PortItemMixin.request_state_change(self, new_state)


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
    def request_state_change(self, new_state: bool) -> bool:
        parent_port = self.parent().port_instance
        if new_state:
            parent_port.attached_passthrough_outs.append(self.port_instance)
        else:
            parent_port.attached_passthrough_outs.remove(self.port_instance)
        return new_state


class CallItem(PortWidgetItem):
    MATCH_CALL_PREFIX = '[m]'

    def __init__(
        self,
        parent_item: QTreeWidgetItem,
        port_instance: Input,
        origin_call_list: list['Callable'],
        call: 'Callable',
    ):
        if call.conditions:
            item_name = f'{self.MATCH_CALL_PREFIX} {call.__name__}'
        else:
            item_name = call.__name__

        super().__init__(parent_item, (item_name,))
        self.port_instance = port_instance
        self.origin_call_list = origin_call_list
        self.call = call

        item_color = midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Callable]
        self.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(item_color))
        self.setCheckState(0, Qt.CheckState.Checked)

    def request_state_change(self, new_state: bool) -> bool:
        if new_state:
            self.origin_call_list.append(self.call)
        else:
            self.origin_call_list.remove(self.call)
        return new_state


class PortsWidget(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('Ports')
        self.setHeaderHidden(True)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self.itemEntered.connect(self.__update_item_tooltip)
        self.__populate()

    def __populate(self) -> None:
        """Populates the widget with items"""
        self.clear()

        self.__add_midi_ports()

        self.__add_declared_ports('OSC Inputs', midiscripter.OscIn)
        self.__add_declared_ports('OSC Outputs', midiscripter.OscOut)

        AlwaysPresentInputPortItem(self.__add_top_level_item('Keyboard Input'), KeyIn)
        self.__add_declared_ports('Keyboard Output', midiscripter.KeyOut)

        AlwaysPresentInputPortItem(self.__add_top_level_item('Mouse Input'), MouseIn)
        self.__add_declared_ports('Mouse Output', midiscripter.MouseOut)

        self.__add_declared_ports('Metronome', midiscripter.MetronomeIn)
        self.__add_declared_ports('File Event Watcher', midiscripter.FileEventIn)
        self.__add_declared_ports('MIDI Port Changes Watcher', midiscripter.MidiPortsChangedIn)

        self.itemSelectionChanged.connect(self.__item_selected)
        # with set blocks on data change itemChanged is emitted only on check state change
        self.itemChanged.connect(self.__item_state_changed)

    def __add_top_level_item(self, item_text: str) -> QTreeWidgetItem:
        bold_font = self.font()
        bold_font.setBold(True)

        top_item = QTreeWidgetItem(self, (item_text,))
        top_item.setData(0, Qt.ItemDataRole.FontRole, bold_font)
        top_item.setExpanded(True)

        return top_item

    def __add_midi_ports(self) -> None:
        for title, _item_class in [
            ('MIDI Inputs', InputMidiPortItem),
            ('MIDI Outputs', OutputMidiPortItem),
        ]:
            top_item = self.__add_top_level_item(title)
            port_class = _item_class.PORT_CLASS

            port_instance_list = [
                port
                for port in port_class.instance_registry.values()
                if isinstance(port, port_class)
            ]
            virtual_port_names = [port._uid for port in port_instance_list if port._is_virtual]

            for port_name in itertools.chain(port_class._available_names, virtual_port_names):
                _item_class(top_item, port_name)

            for port_instance in port_instance_list:
                if not port_instance._is_available and port_instance._uid not in virtual_port_names:
                    AbsentMidiPortItem(top_item, port_instance._uid)

    def __add_declared_ports(self, title: str, port_type: type[Input | Output]) -> None:
        port_instances_to_add = []
        for port_key, port_instance in port_type.instance_registry.items():
            if port_key[0] is port_type.__name__:
                port_instances_to_add.append(port_instance)

        if not port_instances_to_add:
            return

        port_top = self.__add_top_level_item(title)

        for port in port_instances_to_add:
            GeneralPortItem(port_top, port)

    def __item_selected(self) -> None:
        """Sends selected item text to the clipboard and shows a "copied" tooltip"""
        if not self.selectedItems():
            return

        selected_item: MidiPortItem | GeneralPortItem | CallItem = self.selectedItems()[0]

        try:
            port_repr = selected_item.repr
            QGuiApplication.clipboard().setText(port_repr)
            QTimer.singleShot(
                200,
                lambda: QToolTip().showText(
                    self.cursor().pos(), f'Copied {port_repr}', self, msecShowTime=2000
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
            tooltip_text = (
                f'Conditions: {item.call.conditions[0]} {item.call.conditions[1]}\n{tooltip_text}'
            )

        self.blockSignals(True)
        item.setData(0, Qt.ItemDataRole.ToolTipRole, tooltip_text)
        self.blockSignals(False)
