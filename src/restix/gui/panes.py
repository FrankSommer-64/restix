# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# restix - Datensicherung auf restic-Basis.
#
# Copyright (c) 2025, Frank Sommer.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------------------------

"""
Zusammengesetzte Bereiche der restix GUI.
"""

import time

from collections.abc import Callable

from PySide6.QtCore import QSize, Qt, Signal, QObject, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QMouseEvent, QBrush, QFont
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QFileDialog, QGridLayout, QGroupBox,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                               QSizePolicy, QTableView, QVBoxLayout, QWidget)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.core.task import TaskProgress, TaskResult
from restix.gui import *
from restix.gui.dialogs import PasswordDialog
from restix.gui.settings import GuiSettings


class TargetModel(QAbstractTableModel):
    """
    Model für die Backup-Ziele der restix-Konfiguration.
    """
    ATTR_NAMES = (CFG_PAR_ALIAS, CFG_PAR_COMMENT, CFG_PAR_LOCATION, CFG_PAR_SCOPE, CFG_PAR_CREDENTIALS)
    HEADER_TEXTS = (L_ALIAS, L_COMMENT, L_LOCATION, L_SCOPE, L_CREDENTIALS)

    def __init__(self, local_config: LocalConfig, edit: bool = False):
        """
        Konstruktor.
        :param local_config: die restix-Konfiguration
        :param edit: True, falls die Backup-Ziele bearbeitet werden sollen; False, falls sie nur angezeigt werden sollen
        """
        super().__init__()
        self._targets = local_config.get(CFG_GROUP_TARGET)
        self._edit_flag = edit
        self.__bold_font = QFont()
        self.__bold_font.setBold(True)

    def data(self, index: QModelIndex, /, role = ...) -> str|QFont|None:
        """
        :param index: Zelle in der TableView
        :param role: Typ der gewünschten Information (Text oder Style)
        :returns: Inhalt oder Style einer Zelle
        """
        if role == Qt.ItemDataRole.DisplayRole:
            return self.target(index)[TargetModel.ATTR_NAMES[index.column()]]
        if role == Qt.ItemDataRole.FontRole and index.column() == 0:
            return self.__bold_font

    def headerData(self, section: int, orientation: Qt.Orientation, /, role = ...) -> str|None:
        """
        :param section: Spalte der TableView
        :param orientation: Orientierung der Überschriften (horizontal oder vertikal)
        :param role: Typ der gewünschten Information (Text oder Style)
        :returns: Text für die Überschrift der angegebenen Spalte
        """
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return localized_label(TargetModel.HEADER_TEXTS[section])

    def rowCount(self, /, parent= ...) -> int:
        """
        :returns: Anzahl der Zeilen im Model
        """
        return len(self._targets)

    def columnCount(self, /, parent= ...) -> int:
        """
        :returns: Anzahl der Spalten im Model
        """
        return 5 if self._edit_flag else 2

    def target(self, index: QModelIndex) -> dict:
        """
        :param index: die Zelle im Model
        :returns: Daten hinter der angegebenen Zelle
        """
        return self._targets[index.row()]


class TargetTableView(QTableView):
    """
    View zur Auswahl oder Bearbeitung der Backup-Ziele.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, selection_handler: Callable):
        """
        Konstruktor.
        :param parent: das übergeordnete Widget
        :param local_config: die restix-Konfiguration
        """
        super().__init__(parent)
        self._model = TargetModel(local_config)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.horizontalHeader().setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.setModel(self._model)
        self.resizeColumnsToContents()
        if selection_handler is not None:
            self.pressed.connect(selection_handler)
        self.setStyleSheet(TARGET_TABLE_STYLE)

    def selected_target(self) -> dict | None:
        """
        :returns: ausgewähltes Backup-Ziel; None, falls nichts ausgewählt wurde
        """
        _selection = self.selectedIndexes()
        if len(_selection) > 0:
            return self._model.target(_selection[0])
        return None


class ImageButtonSignals(QObject):
    """
    Interne Signale für Klicks auf Image-Buttons.
    """
    # Links-Klick
    clicked = Signal()
    # Links- oder Rechts-Klick an Bildschirm-Position X, Y
    menu_triggered = Signal(int, int)


class ImageButton(QPushButton):
    """
    Button mit Hintergrundbild.
    Eigene Klasse, da Kontextmenü sowohl mit Klick auf rechte als auch linke Maustaste erscheinen soll.
    """
    def __init__(self, parent: QWidget, image_url: str, click_handler, triggers_menu=False):
        """
        Konstruktor.
        :param parent: Pane für den Button
        :param image_url: URL des Hintergrundbilds
        :param click_handler: Slot für Klicks auf den Button
        :param triggers_menu: zeigt an, ob beim Klick auf den Button ein Kontextmenü angezeigt werden soll
        """
        super().__init__('', parent)
        self.__click_handler = click_handler
        self.__triggers_menu = triggers_menu
        self.__signals = ImageButtonSignals()
        if triggers_menu:
            self.__signals.menu_triggered.connect(click_handler)
        else:
            self.__signals.clicked.connect(click_handler)
        self.setStyleSheet(_IMAGE_BUTTON_STYLE.format(RESTIX_ASSETS_DIR, image_url))
        self.setFixedSize(QSize(IMAGE_BUTTON_SIZE, IMAGE_BUTTON_SIZE))

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Event-Handler für Mausklicks.
        Löst das registrierte Signal aus.
        :param event: das Maus-Event
        """
        if self.__triggers_menu:
            # bei Kontextmenü wird Links- oder Rechts-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
                self.__signals.menu_triggered.emit(event.globalX(), event.globalY())
        else:
            # bei normalem Button wird nur Links-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton:
                self.__signals.clicked.emit()


class ImageButtonPane(QWidget):
    """
    Pane mit Hintergrundbild-Button im oberen und Label im unteren Bereich.
    """
    def __init__(self, parent: QWidget, image_url: str, label_id: str, click_handler, triggers_menu=False):
        """
        Konstruktor.
        :param parent: Widget, das diese Pane enthält.
        :param image_url: URL des Hintergrundbilds
        :param label_id: Resource-ID der Beschriftung
        :param click_handler: Slot für Klicks auf die Pane
        :param triggers_menu: zeigt an, ob beim Klick auf die Pane ein Kontextmenü angezeigt werden soll
        """
        super().__init__(parent)
        self.__click_handler = click_handler
        self.__triggers_menu = triggers_menu
        self.__signals = ImageButtonSignals()
        if triggers_menu:
            self.__signals.menu_triggered.connect(click_handler)
        else:
            self.__signals.clicked.connect(click_handler)
        _layout = QVBoxLayout(self)
        _layout.setSpacing(0)
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__image_button = ImageButton(self, image_url, click_handler, triggers_menu)
        _layout.addWidget(self.__image_button)
        self.__label = QLabel(localized_label(label_id), self)
        self.__label.setStyleSheet(IMAGE_BUTTON_LABEL_STYLE_NORMAL)
        self.__label.setFixedWidth(IMAGE_BUTTON_SIZE)
        self.__label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.__label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(self.__label)
        self.setStyleSheet(IMAGE_BUTTON_PANE_STYLE)

    def mark_label(self, flag: bool):
        """
        Setzt die Hintergrundfarbe des Button-Labels.
        :param flag: True, falls der Button aktiv ist; ansonsten False
        """
        _style = IMAGE_BUTTON_LABEL_STYLE_ACTIVE if flag else IMAGE_BUTTON_LABEL_STYLE_NORMAL
        self.__label.setStyleSheet(_style)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Event-Handler für Mausklicks.
        Löst das registrierte Signal aus.
        :param event: das Maus-Event
        """
        if self.__triggers_menu:
            # bei Kontextmenü wird Links- oder Rechts-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
                self.__signals.menu_triggered.emit(event.globalX(), event.globalY())
        else:
            # bei normalem Button wird nur Links-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton:
                self.__signals.clicked.emit()


class DirectorySelector(QPushButton):
    """
    Button zur Auswahl eines Verzeichnisses.
    """
    def __init__(self, tooltip: str):
        """
        Konstruktor.
        :param tooltip: lokalisierter Tooltip-Text
        """
        super().__init__(localized_label(L_SELECT))
        self.setToolTip(tooltip)
        self.__selected_path = None
        self.clicked.connect(self._clicked)

    def _clicked(self):
        """
        Wird aufgerufen, wenn der Button geklickt wurde.
        """
        _dir = QFileDialog.getExistingDirectory(self, localized_label(L_SELECT))
        if len(_dir) > 0:
            self.__selected_path = _dir
            self.setText(_dir)
        else:
            self.__selected_path = None
            self.setText(localized_label(L_SELECT))


class ActionSelectionPane(QWidget):
    """
    Pane mit den Hintergrundbild-Buttons zur Auswahl der Aktionen.
    """
    def __init__(self, parent: QWidget, actions: (str, str, (), bool)):
        """
        Konstruktor.
        :param parent: zentrale restix Pane
        :param actions: Beschreibung der Aktionen
        """
        super().__init__(parent)
        self.__selected_button_label_id = None
        _layout = QGridLayout(self)
        _layout.setSpacing(10)
        _layout.setContentsMargins(0, 0, 0, 0)
        _url, _label, _slot, _triggers_menu = actions[0]
        _pane = ImageButtonPane(self, _url, _label, _slot, _triggers_menu)
        self.__button_panes = {_label: _pane}
        _layout.addWidget(_pane, 0, 0, Qt.AlignmentFlag.AlignLeft)
        for _i in range(1, len(actions) - 1):
            _url, _label, _slot, _triggers_menu = actions[_i]
            _pane = ImageButtonPane(self, _url, _label, _slot, _triggers_menu)
            self.__button_panes[_label] = _pane
            _layout.addWidget(_pane, 0, _i, Qt.AlignmentFlag.AlignHCenter)
        _url, _label, _slot, _triggers_menu = actions[len(actions) - 1]
        _pane = ImageButtonPane(self, _url, _label, _slot, _triggers_menu)
        self.__button_panes[_label] = _pane
        _layout.addWidget(_pane, 0, len(actions) - 1, Qt.AlignmentFlag.AlignRight)

    def action_selected(self, button_label_id: str | None):
        """
        Wird aufgerufen, wenn der Benutzer eine Aktion ausgewählt hat.
        Markiert den zur Aktion gehörenden Button.
        :param button_label_id: Resource-ID des Button-Labels zur gewählten Aktion
        """
        if self.__selected_button_label_id is not None:
            self.__button_panes.get(self.__selected_button_label_id).mark_label(False)
        if button_label_id is not None:
            self.__button_panes.get(button_label_id).mark_label(True)
        self.__selected_button_label_id = button_label_id

class MessagePane(QWidget):
    """
    Pane zur Ausgabe von Nachrichten.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        """
        super().__init__(parent)
        _layout = QVBoxLayout(self)
        self.__messages = QListWidget(self)
        _layout.setContentsMargins(0, DEFAULT_CONTENT_MARGIN, 0, 0)
        self.__messages.setStyleSheet(MESSAGE_PANE_STYLE)
        self.__messages.setMinimumHeight(MIN_MESSAGE_PANE_HEIGHT)
        self.__messages.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        _layout.addWidget(self.__messages)

    def show_message(self, severity: str, text: str):
        """
        Gibt eine Nachricht aus.
        :param severity: Schweregrad der Nachricht (Information, Warnung, Fehler).
        :param text: Nachrichtentext
        """
        _info = QListWidgetItem(text)
        if severity == SEVERITY_ERROR:
            _info.setForeground(QBrush(Qt.GlobalColor.red))
        elif severity == SEVERITY_WARNING:
            _info.setForeground(QBrush(Qt.GlobalColor.blue))
        else:
            _info.setForeground(QBrush(Qt.GlobalColor.black))
        self.__messages.addItem(_info)
        self.__messages.scrollToBottom()

    def clear(self):
        """
        Löscht alle Nachrichten aus der Pane.
        """
        self.__messages.clear()


class ActionButtonPane(QWidget):
    """
    Pane zur Ausgabe von Nachrichten.
    """
    def __init__(self, parent: QWidget, start_button_label_ids: list[str], start_button_tooltip_ids: list[str],
                 start_handlers: list[Callable], cancel_handler: Callable | None):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param start_button_label_ids: ID der Beschriftungen für die Start-Buttons
        :param start_button_tooltip_ids: ID der Tooltips für die Start-Buttons
        :param start_handlers: Click-Handler für jeden der Start-Buttons
        :param cancel_handler: Handler, wenn der Abbrechen-Button geklickt wird
        """
        super().__init__(parent)
        _layout = QGridLayout(self)
        self.__start_buttons = []
        self.__cancel_button = None
        for _i, _label_id in enumerate(start_button_label_ids):
            _button = QPushButton(localized_label(start_button_label_ids[_i]))
            _button.setToolTip(localized_label(start_button_tooltip_ids[_i]))
            _button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            _button.setStyleSheet(ACTION_BUTTON_STYLE)
            _button.clicked.connect(start_handlers[_i])
            self.__start_buttons.append(_button)
            _layout.addWidget(_button, 0, _i)
        if cancel_handler is not None:
            self.__cancel_button = QPushButton(localized_label(L_CANCEL))
            self.__cancel_button.setToolTip(localized_label(T_CANCEL_ACTION))
            self.__cancel_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            self.__cancel_button.setStyleSheet(CANCEL_BUTTON_STYLE)
            self.__cancel_button.setEnabled(False)
            self.__cancel_button.clicked.connect(cancel_handler)
            _layout.addWidget(self.__cancel_button, 0, len(start_button_label_ids))

    def action_started(self):
        """
        Deaktiviert den OK-Button, aktiviert den Cancel-Button.
        """
        if self.__cancel_button is None:
            return
        for _button in self.__start_buttons:
            _button.setEnabled(False)
        self.__cancel_button.setEnabled(True)

    def action_stopped(self):
        """
        Aktiviert den OK-Button, deaktiviert den Cancel-Button.
        """
        if self.__cancel_button is None:
            return
        for _button in self.__start_buttons:
            _button.setEnabled(True)
        self.__cancel_button.setEnabled(False)


class TargetSelectionPane(QGroupBox):
    """
    Pane zur Auswahl eines Backup-Ziels.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, settings: GuiSettings,
                 target_selected_handler: Callable):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param local_config: lokale restix-Konfiguration
        :param settings: GUI-Einstellungen des Benutzers
        :param target_selected_handler: Handler für die Auswahl eines Backup-Ziels
        """
        super().__init__(localized_label(L_TARGET), parent)
        self.restix_config = local_config
        self.gui_settings = settings
        _layout = QGridLayout(self)
        self._table_view = TargetTableView(self, local_config, target_selected_handler)
        _layout.addWidget(self._table_view)
        self.setStyleSheet(GROUP_BOX_STYLE)

    def selected_target(self) -> dict:
        """
        :returns: Alias des ausgewählten Backup-Ziels; None, falls nichts ausgewählt wurde
        """
        _selected_target = self._table_view.selected_target()
        if _selected_target is not None:
            self.gui_settings.set_latest_target(_selected_target[CFG_PAR_ALIAS])
        return _selected_target


class ResticActionPane(QWidget):
    """
    Basisklasse für die Panes aller Aktionen, die einen restic-Befehl auslösen.
    """
    def __init__(self, parent: QWidget, start_button_label_ids: list[str], start_button_tooltip_ids: list[str],
                 target_selected_handler: Callable | None, start_handlers: list[Callable],
                 local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: zentrale restix Pane
        :param start_button_label_ids: ID der Beschriftungen für die Start-Buttons
        :param start_button_tooltip_ids: ID der Tooltips für die Start-Buttons
        :param target_selected_handler: Handler, wenn der Benutzer ein Backup-Ziel auswählt
        :param start_handlers: Click-Handler für jeden der Start-Buttons
        :param local_config: lokale restix-Konfiguration
        :param gui_settings: GUI-Einstellungen des Benutzers
        """
        super().__init__(parent)
        self.restix_config = local_config
        self.__target_selected_handler = target_selected_handler
        self.selected_target = None
        self.pane_layout = QGridLayout(self)
        self.pane_layout.setSpacing(5)
        self.pane_layout.setColumnStretch(1, 1)
        # links oben Backup-Ziel-Auswahl
        self.target_selection_pane = TargetSelectionPane(self, local_config, gui_settings, self.target_selected)
        self.pane_layout.addWidget(self.target_selection_pane, 0, 0, 2, 1)
        # rechts mittig Buttons
        self.button_pane = ActionButtonPane(self, start_button_label_ids, start_button_tooltip_ids,
                                            start_handlers, self.cancel_button_clicked)
        self.pane_layout.addWidget(self.button_pane, 1, 1)
        # unten Ausgabetexte
        self.message_pane = MessagePane(self)
        self.pane_layout.addWidget(self.message_pane, 2, 0, 1, -1)

    def start_button_clicked(self) -> tuple[bool, str]:
        """
        Wird aufgerufen, wenn einer der 'Start'-Buttons geklickt wurde.
        :returns: Prüfung ok, bei credentials-Typ prompt eingegebenes Passwort; ansonsten None
        """
        if self.selected_target is None:
            # ohne Backup-Ziel geht nichts
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_NO_TARGET_SELECTED),
                                    QMessageBox.StandardButton.Ok)
            return False, ''
        _pw = None
        _credentials = self.restix_config.credentials_for_target(self.selected_target[CFG_PAR_ALIAS])
        if _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_PROMPT:
            # Passwort einlesen
            _pw_dlg = PasswordDialog(self)
            if _pw_dlg.exec() == QDialog.DialogCode.Accepted:
                _pw = _pw_dlg.password()
            else:
                return False, ''
        self.message_pane.clear()
        self.button_pane.action_started()
        return True, _pw

    def cancel_button_clicked(self):
        """
        Wird aufgerufen, wenn der 'Cancel'-Button geklickt wurde.
        """
        self.button_pane.action_stopped()

    def target_selected(self):
        """
        Wird aufgerufen, wenn der Benutzer ein Backup-Ziel auswählt.
        """
        self.selected_target = self.target_selection_pane.selected_target()
        if self.__target_selected_handler is not None:
            self.__target_selected_handler()

    def handle_progress(self, progress_info: TaskProgress):
        """
        Zeigt eine Fortschritt-Nachricht in der MessagePane an.
        :param progress_info: Daten der Fortschritt-Nachricht.
        """
        self.message_pane.show_message(progress_info.message_severity(), progress_info.message_text())

    def handle_finish(self):
        """
        Informiert den Benutzer darüber, dass der Hintergrund-Prozess erfolgreich ausgeführt wurde.
        Aktualisiert den Status der Start- und Cancel-Buttons.
        """
        _info = localized_message(I_GUI_TASK_FINISHED, time.strftime('%X', time.localtime()))
        self.message_pane.show_message(SEVERITY_INFO, _info)
        self.button_pane.action_stopped()

    def handle_result(self, result: TaskResult):
        """
        Gibt eine Zusammenfassung des Ergebnisses der Hintergrund-Task aus.
        Aktualisiert den Status der Start- und Cancel-Buttons.
        :param result: Ergebnis des Hintergrund-Prozesses
        """
        self.message_pane.show_message(SEVERITY_INFO, result.summary())
        self.button_pane.action_stopped()

    def handle_error(self, exception: Exception):
        """
        Informiert den Benutzer darüber, dass Hintergrund-Prozess fehlgeschlagen ist.
        Aktualisiert den Status der Start- und Cancel-Buttons.
        :param exception: Exception, die zum Fehlschlag des Hintergrund-Prozesses geführt hat
        """
        self.message_pane.show_message(SEVERITY_ERROR, str(exception))
        self.button_pane.action_stopped()


def create_checkbox(layout: QGridLayout, caption_id: str, tooltip_id: str, initial_state:bool) -> QCheckBox:
    """
    Erzeugt Label und Checkbox für eine Option.
    :param layout: Layout, in dem die Option enthalten sein soll.
    :param caption_id: Label-ID für die Beschreibung.
    :param tooltip_id: Label-ID für den Tooltip-Text.
    :param initial_state: initialer Zustand der Checkbox.
    :returns: checkbox widget
    """
    _row_nr = layout.rowCount()
    _tooltip = localized_label(tooltip_id)
    layout.addWidget(option_label(caption_id, _tooltip), _row_nr, 0)
    _check_box = QCheckBox()
    _check_box.setToolTip(_tooltip)
    _check_box.setChecked(initial_state)
    layout.addWidget(_check_box, _row_nr, 1, 1, 2)
    return _check_box


def create_combo(layout: QGridLayout, caption_id: str, tooltip_id: str) -> QComboBox:
    """
    Erzeugt Label und Combo-Box für eine Option.
    :param layout: Layout, in dem die Option enthalten sein soll.
    :param caption_id: Label-ID für die Beschreibung.
    :param tooltip_id: Label-ID für den Tooltip-Text.
    :returns: Combo-Box
    """
    _row_nr = layout.rowCount()
    _tooltip = localized_label(tooltip_id)
    layout.addWidget(option_label(caption_id, _tooltip), _row_nr, 0)
    _combo_box = QComboBox()
    _combo_box.setMinimumWidth(MIN_COMBO_WIDTH)
    _combo_box.setToolTip(_tooltip)
    layout.addWidget(_combo_box, _row_nr, 1, 1, 2)
    return _combo_box


def create_dir_selector(layout: QGridLayout, caption_id: str, tooltip_id: str) -> DirectorySelector:
    """
    Erzeugt Label und Button zur Auswahl eines Verzeichnisses.
    :param layout: Layout, in dem die Option enthalten sein soll.
    :param caption_id: Label-ID für die Beschreibung.
    :param tooltip_id: Label-ID für den Tooltip-Text.
    :returns: Button zur Auswahl eines Verzeichnisses
    """
    _row_nr = layout.rowCount()
    _tooltip = localized_label(tooltip_id)
    layout.addWidget(option_label(caption_id, _tooltip), _row_nr, 0)
    _dir_selector = DirectorySelector(_tooltip)
    layout.addWidget(_dir_selector, _row_nr, 1, 1, 2)
    return _dir_selector


def create_text(layout: QGridLayout, caption_id: str, tooltip_id: str) -> QLineEdit:
    """
    Erzeugt Label und Texteingabefeld für eine Option.
    :param layout: Layout, in dem die Option enthalten sein soll.
    :param caption_id: Label-ID für die Beschreibung.
    :param tooltip_id: Label-ID für den Tooltip-Text.
    :returns: Texteingabefeld
    """
    _row_nr = layout.rowCount()
    _tooltip = localized_label(tooltip_id)
    layout.addWidget(option_label(caption_id, _tooltip), _row_nr, 0)
    _input_field = QLineEdit()
    _input_field.setStyleSheet(TEXT_FIELD_STYLE)
    _input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    _input_field.setToolTip(_tooltip)
    layout.addWidget(_input_field, _row_nr, 1, 1, 2)
    return _input_field


def option_label(caption_id: str, tooltip_text: str) -> QLabel:
    """
    Erzeugt das Label für eine Option.
    :param caption_id: Label-ID für die Beschreibung.
    :param tooltip_text: lokalisierter Tooltip-Text.
    :returns: Label widget
    """
    _caption = '' if len(caption_id) == 0 else localized_label(caption_id)
    _label = QLabel(_caption)
    _label.setToolTip(tooltip_text)
    _label.setStyleSheet(CAPTION_STYLE)
    return _label

_IMAGE_BUTTON_STYLE = 'background-image : url({0}:{1}); border-width: 2px; border-color: black; border-style: solid'
