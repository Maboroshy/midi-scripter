from collections.abc import Callable

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import midiscripter.logger.html_sink
from midiscripter.base.port_base import Input, Output
from midiscripter.logger import log
from midiscripter.midi import MidiIn, MidiOut


class PortsWidget(QTreeWidget):
    PORT_CLASS_ROLE = 100
    PORT_UID_ROLE = 101
    PORT_REPR_ROLE = 103
    CALLBACK_FUNCTION_ROLE = 104
    PASSTHROUGH_OUT_PORT_ROLE = 105

    def __init__(self):
        super().__init__()
        self.setObjectName('Ports')
        self.setHeaderHidden(True)
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self.itemEntered.connect(self.__update_item_tooltip)
        self.__populate()

    def __add_top_level_item(self, item_text: str):
        bold_font = self.font()
        bold_font.setBold(True)

        top_item = QTreeWidgetItem(self, (item_text,))
        top_item.setData(0, Qt.ItemDataRole.FontRole, bold_font)
        top_item.setExpanded(True)

        return top_item

    def __populate(self):
        """Populates the widget with items"""
        self.clear()
        self.__add_midi_inputs()
        self.__add_midi_outputs()
        self.__add_ports_if_declared('OSC Inputs', midiscripter.OscIn)
        self.__add_ports_if_declared('OSC Outputs', midiscripter.OscOut)
        self.__add_keyboard_in()
        self.__add_ports_if_declared('Keyboard Output', midiscripter.KeyOut)
        self.__add_ports_if_declared('Metronome', midiscripter.MetronomeIn)
        self.__add_ports_if_declared('File Event Watcher', midiscripter.FileEventIn)
        self.__add_ports_if_declared('MIDI Port Changes Watcher', midiscripter.MidiPortsChangedIn)

        self.itemChanged.connect(self.__item_state_changed)
        self.itemSelectionChanged.connect(self.__item_selected)

    def __add_midi_inputs(self):
        if not MidiIn._available_names:
            return

        inputs_top = self.__add_top_level_item('MIDI Inputs')

        for input_port_name in MidiIn._available_names:
            port_key = (MidiIn.__name__, input_port_name)
            port_instance = MidiIn.instance_registry.get(port_key, None)
            input_item = QTreeWidgetItem(inputs_top, (input_port_name,))

            if not port_instance:
                input_item.setCheckState(0, Qt.CheckState.Unchecked)
            elif port_instance.is_enabled:
                input_item.setCheckState(0, Qt.CheckState.Checked)
            else:
                input_item.setCheckState(0, Qt.CheckState.Unchecked)
                input_item.setData(
                    0, Qt.ItemDataRole.BackgroundRole, QBrush(QColor().fromRgb(255, 0, 0, 20))
                )

            input_item.setData(0, self.PORT_CLASS_ROLE, MidiIn)
            input_item.setData(0, self.PORT_UID_ROLE, input_port_name)

            port_repr = f"{MidiIn.__name__}('{input_port_name}')"
            input_item.setData(0, self.PORT_REPR_ROLE, port_repr)

            input_item.setData(
                0,
                Qt.ItemDataRole.ForegroundRole,
                QBrush(midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Input]),
            )

            if port_instance:
                for passthrough_out_port in port_instance.attached_passthrough_outs:
                    sub_item = QTreeWidgetItem(input_item, (passthrough_out_port._uid,))
                    sub_item.setCheckState(0, Qt.CheckState.Checked)

                    sub_item.setData(
                        0,
                        Qt.ItemDataRole.ForegroundRole,
                        QBrush(midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Output]),
                    )
                    sub_item.setData(0, self.PORT_CLASS_ROLE, MidiIn)
                    sub_item.setData(0, self.PORT_UID_ROLE, input_port_name)
                    sub_item.setData(0, self.PASSTHROUGH_OUT_PORT_ROLE, passthrough_out_port)
                    sub_item.setData(0, self.PORT_REPR_ROLE, passthrough_out_port.__repr__())

                self.__add_inputs_subscribed_calls(input_item)

        for port_instance in MidiIn.instance_registry.values():
            if isinstance(port_instance, MidiIn) and not port_instance._is_available:
                absent_input_item = QTreeWidgetItem(inputs_top, (str(port_instance),))
                absent_input_item.setCheckState(0, Qt.CheckState.Unchecked)
                absent_input_item.setDisabled(True)

    def __add_inputs_subscribed_calls(self, input_item: QTreeWidgetItem):
        port_class = input_item.data(0, self.PORT_CLASS_ROLE)
        port_name = input_item.data(0, self.PORT_UID_ROLE)

        port_instance = port_class(port_name) if port_name else port_class()

        for callback_function in port_instance.subscribed_calls:
            sub_item = QTreeWidgetItem(input_item, (callback_function.__name__,))
            sub_item.setCheckState(0, Qt.CheckState.Checked)

            sub_item.setData(
                0,
                Qt.ItemDataRole.ForegroundRole,
                QBrush(midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Callable]),
            )
            sub_item.setData(0, self.PORT_CLASS_ROLE, MidiIn)
            sub_item.setData(0, self.PORT_UID_ROLE, port_name)
            sub_item.setData(0, self.CALLBACK_FUNCTION_ROLE, callback_function)

    def __add_midi_outputs(self):
        if not MidiOut._available_names:
            return

        outputs_top = self.__add_top_level_item('MIDI Outputs')

        for output_port_name in MidiOut._available_names:
            port_key = (MidiOut.__name__, output_port_name)
            port_instance = MidiOut.instance_registry.get(port_key, None)
            output_item = QTreeWidgetItem(outputs_top, (output_port_name,))

            if not port_instance:
                output_item.setCheckState(0, Qt.CheckState.Unchecked)
            elif port_instance.is_enabled:
                output_item.setCheckState(0, Qt.CheckState.Checked)
            else:
                output_item.setCheckState(0, Qt.CheckState.Unchecked)
                output_item.setData(
                    0, Qt.ItemDataRole.BackgroundRole, QBrush(QColor().fromRgb(255, 0, 0, 20))
                )

            output_item.setData(0, self.PORT_CLASS_ROLE, MidiOut)
            output_item.setData(0, self.PORT_UID_ROLE, output_port_name)

            port_repr = f"{MidiOut.__name__}('{output_port_name}')"
            output_item.setData(0, self.PORT_REPR_ROLE, port_repr)

            output_item.setData(
                0,
                Qt.ItemDataRole.ForegroundRole,
                QBrush(midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Output]),
            )

        for port_instance in MidiOut.instance_registry.values():
            if isinstance(port_instance, MidiOut) and not port_instance._is_available:
                absent_output_item = QTreeWidgetItem(outputs_top, (port_instance._uid,))
                absent_output_item.setCheckState(0, Qt.CheckState.Unchecked)
                absent_output_item.setDisabled(True)

    def __add_ports_if_declared(self, title: str, port_type: type):
        port_instances_to_add = []
        for port_key, port_instance in port_type.instance_registry.items():
            if port_key[0] is port_type.__name__:
                port_instances_to_add.append(port_instance)

        if not port_instances_to_add:
            return

        port_top = self.__add_top_level_item(title)

        for port in port_instances_to_add:
            port_item = QTreeWidgetItem(port_top, (str(port._uid),))
            port_item.setCheckState(0, Qt.CheckState.Checked)

            port_item.setData(0, self.PORT_CLASS_ROLE, port_type)
            port_item.setData(0, self.PORT_REPR_ROLE, port.__repr__())

            if port._force_uid:
                port_item.setData(0, self.PORT_UID_ROLE, None)
            else:
                port_item.setData(0, self.PORT_UID_ROLE, port._uid)

            if issubclass(port_type, Input):
                item_color = midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Input]
                self.__add_inputs_subscribed_calls(port_item)
            elif issubclass(port_type, Output):
                item_color = midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Output]

            port_item.setData(0, Qt.ItemDataRole.ForegroundRole, QBrush(item_color))

    def __add_keyboard_in(self):
        port_top = self.__add_top_level_item('Keyboard Input')
        port_item = QTreeWidgetItem(port_top, ('Keyboard Input',))
        if (
            midiscripter.KeyIn.__name__,
            midiscripter.KeyIn._force_uid,
        ) in midiscripter.KeyIn.instance_registry:
            port_item.setCheckState(0, Qt.CheckState.Checked)
        else:
            port_item.setCheckState(0, Qt.CheckState.Unchecked)

        port_item.setData(0, self.PORT_CLASS_ROLE, midiscripter.KeyIn)
        port_item.setData(0, self.PORT_UID_ROLE, None)
        port_item.setData(0, self.PORT_REPR_ROLE, f'{midiscripter.KeyIn.__name__}()')
        port_item.setData(
            0,
            Qt.ItemDataRole.ForegroundRole,
            QBrush(midiscripter.logger.html_sink.HtmlSink.COLOR_MAP[Input]),
        )

    def __item_selected(self):
        """Sends selected item text to the clipboard and shows a "copied" tooltip"""
        if not self.selectedItems():
            return

        selected_item: QTreeWidgetItem = self.selectedItems()[0]
        port_repr = selected_item.data(0, self.PORT_REPR_ROLE)
        if port_repr:
            QGuiApplication.clipboard().setText(port_repr)
            QTimer.singleShot(
                200,
                lambda: QToolTip().showText(
                    self.cursor().pos(), f'Copied {port_repr}', self, msecShowTime=2000
                ),
            )  # Don't hide on mouse button release
        selected_item.setSelected(False)

    def __item_state_changed(self, item: QTreeWidgetItem, _):
        """Enabled or disables the MIDI port / passthrough out / call according to the checked state change"""
        new_checked_state = item.checkState(0) == Qt.CheckState.Checked

        port_class = item.data(0, self.PORT_CLASS_ROLE)
        port_name = item.data(0, self.PORT_UID_ROLE)

        callback_function = item.data(0, self.CALLBACK_FUNCTION_ROLE)
        passthrough_out_port: MidiOut = item.data(0, self.PASSTHROUGH_OUT_PORT_ROLE)

        port_instance = port_class(port_name) if port_name else port_class()

        if callback_function:
            if new_checked_state:
                port_instance.subscribed_calls.append(callback_function)
            else:
                port_instance.subscribed_calls.remove(callback_function)

        elif passthrough_out_port:
            if new_checked_state:
                port_instance.attached_passthrough_outs.append(passthrough_out_port)
            else:
                port_instance.attached_passthrough_outs.remove(passthrough_out_port)

        else:
            if new_checked_state:
                if not port_instance.is_enabled:
                    port_instance._open()
                    port_instance.is_enabled = True
                    log('Enabled {port}', port=port_instance)

                if not port_instance.is_enabled:
                    item.setData(
                        0, Qt.ItemDataRole.BackgroundRole, QBrush(QColor().fromRgb(255, 0, 0, 20))
                    )
                    log.red("Can't enable {port}", port=port_instance)
                else:
                    item.setData(
                        0,
                        Qt.ItemDataRole.BackgroundRole,
                        QBrush(QColor(Qt.GlobalColor.transparent)),
                    )

            else:
                port_instance.is_enabled = False
                log('Disabled {port}', port=port_instance)

            self.blockSignals(True)
            item.setCheckState(
                0, (Qt.CheckState.Unchecked, Qt.CheckState.Checked)[port_instance.is_enabled]
            )
            self.blockSignals(False)

    def __update_item_tooltip(self, item: QTreeWidgetItem):
        """Updates items tooltip on hover"""
        call_function = item.data(0, self.CALLBACK_FUNCTION_ROLE)
        if call_function:
            port_class = item.data(0, self.PORT_CLASS_ROLE)
            call_statistics = list(port_class._call_statistics[call_function])

            if not call_statistics:
                tooltip_text = 'No calls made yet'
            else:
                call_statistics.sort()
                tooltip_text = (
                    'Execution time for last 20 calls:\n'
                    f'Min: {call_statistics[0]} ms; '
                    f'Med: {call_statistics[int(len(call_statistics) / 2)]} ms; '
                    f'Max: {call_statistics[-1]} ms'
                )

            item.setData(0, Qt.ItemDataRole.ToolTipRole, tooltip_text)
