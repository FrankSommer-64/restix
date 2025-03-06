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


from PySide6.QtCore import QSize, Qt, Signal, QObject, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QMouseEvent, QBrush, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout,
                               QPushButton, QLabel, QHBoxLayout, QSizePolicy, QGridLayout, QListWidget,
                               QListWidgetItem, QGroupBox, QTableView, QAbstractItemView, QCheckBox)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.gui.settings import GuiSettings


GROUP_BOX_STYLE = 'QGroupBox {font: bold; border: 1px solid blue; border-radius: 6px; margin-top: 6px} ' \
                  'QGroupBox::title {color: blue; subcontrol-origin: margin; left: 7px; padding: 0 5px 0 5px;}'


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
    def __init__(self, parent: QWidget, local_config: LocalConfig):
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
        self.setStyleSheet(_TARGET_TABLE_STYLE)

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
        :param parent: die Pane für den Button
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
        self.setStyleSheet(f'background-image : url({RESTIX_ASSETS_DIR}:{image_url}); border-width: 2px; border-color: black; border-style: solid')
        self.setMinimumSize(QSize(128, 128))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

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
        :param parent: das Widget, das diese Pane enthält.
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
        _layout = QVBoxLayout()
        _layout.setSpacing(0)
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__image_button = ImageButton(self, image_url, click_handler, triggers_menu)
        _layout.addWidget(self.__image_button)
        _label = QLabel(localized_label(label_id), self)
        _label.setStyleSheet('font-weight: bold')
        _label.setMinimumWidth(128)
        _label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_label)
        self.setLayout(_layout)
        self.setStyleSheet('background-color: white; border-width: 2px; border-color: black; border-style: solid')


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


class ActionSelectionPane(QWidget):
    """
    Pane mit den Hintergrundbild-Buttons zur Auswahl der Aktionen.
    """
    def __init__(self, parent: QWidget, actions: (str, str, (), bool)):
        """
        Konstruktor.
        :param parent: die zentrale restix Pane
        :param actions: Beschreibung der Aktionen
        """
        super().__init__(parent)
        _layout = QHBoxLayout()
        _layout.setSpacing(0)
        _layout.setContentsMargins(0, 0, 0, 0)
        for _action in actions:
            _url, _label, _slot, _triggers_menu = _action
            _layout.addWidget(ImageButtonPane(self, _url, _label, _slot, _triggers_menu))
        self.setLayout(_layout)
        self.setStyleSheet('background-color: white')


class MessagePane(QWidget):
    """
    Pane zur Ausgabe von Nachrichten.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        """
        super().__init__(parent)
        _layout = QVBoxLayout(self)
        self.__messages = QListWidget(self)
        self.__messages.setStyleSheet(_MESSAGE_PANE_STYLE)
        self.__messages.setMinimumHeight(250)
        _layout.addWidget(self.__messages)
        self.setLayout(_layout)

    def show_message(self, text: str):
        """
        Gibt eine Nachricht aus.
        :param text: der Nachrichtentext
        """
        _text_item = QListWidgetItem(text)
        _text_item.setForeground(QBrush(Qt.GlobalColor.black))
        self.__messages.addItem(_text_item)
        self.__messages.scrollToBottom()


class ActionButtonPane(QWidget):
    """
    Pane zur Ausgabe von Nachrichten.
    """
    def __init__(self, parent: QWidget, ok_button_label_id: str, ok_handler, cancel_handler):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        """
        super().__init__(parent)
        _layout = QHBoxLayout(self)
        _layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        _ok_button = QPushButton(localized_label(ok_button_label_id))
        _ok_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        _ok_button.setStyleSheet(_OK_BUTTON_STYLE)
        _ok_button.clicked.connect(ok_handler)
        _layout.addWidget(_ok_button)
        self.setLayout(_layout)


class TargetSelectionPane(QGroupBox):
    """
    Pane zur Auswahl eines Backup-Ziels.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, settings: GuiSettings):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param local_config: lokale restix-Konfiguration
        :param settings: die GUI-Einstellungen des Benutzers
        """
        super().__init__(localized_label(L_TARGETS), parent)
        self.restix_config = local_config
        _layout = QGridLayout(self)
        self._table_view = TargetTableView(self, local_config)
        _layout.addWidget(self._table_view)
        self.setLayout(_layout)
        self.setStyleSheet(GROUP_BOX_STYLE)

    def selected_target_alias(self) -> dict:
        """
        :returns: Alias des ausgewählten Backup-Ziels; None, falls nichts ausgewählt wurde
        """
        return self._table_view.selected_target()


class ResticActionPane(QWidget):
    """
    Basisklasse für die Panes aller Aktionen, die einen restic-Befehl auslösen.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: die zentrale restix Pane
        :param local_config: lokale restix-Konfiguration
        :param gui_settings: die GUI-Einstellungen des Benutzers
        """
        super().__init__(parent)
        self.restix_config = local_config
        self.pane_layout = QGridLayout(self)
        self.pane_layout.setSpacing(5)
        self.pane_layout.setColumnStretch(1, 1)
        # links oben Backup-Ziel-Auswahl
        self.target_selection_pane = TargetSelectionPane(self, local_config, gui_settings)
        self.pane_layout.addWidget(self.target_selection_pane, 0, 0, 2, 1)
        # unten Ausgabetexte
        self.message_pane = MessagePane(self)
        self.pane_layout.addWidget(self.message_pane, 2, 0, 1, -1)
        self.message_pane.show_message('Hallo')



def create_option(layout: QGridLayout, caption_id: str, tooltip_id: str, initial_state:bool) -> QCheckBox:
    """
    Erzeugt Label und Checkbox für eine Option.
    :param layout: das Layout, in dem die Option enthalten sein soll.
    :param caption_id: die Label-ID für die Beschreibung.
    :param tooltip_id: die Label-ID für den Tooltip-Text.
    :param initial_state: der initiale Zustand der Checkbox.
    :returns: the checkbox widget
    """
    _row_nr = layout.rowCount()
    _tooltip = localized_label(tooltip_id)
    _caption = QLabel(localized_label(caption_id))
    _caption.setToolTip(_tooltip)
    _caption.setStyleSheet(_CHECKBOX_CAPTION_STYLE)
    layout.addWidget(_caption, _row_nr, 0)
    _check_box = QCheckBox()
    _check_box.setToolTip(_tooltip)
    _check_box.setChecked(initial_state)
    layout.addWidget(_check_box, _row_nr, 1)
    return _check_box


_CHECKBOX_CAPTION_STYLE = 'color: black; font-weight: bold'
_MESSAGE_PANE_STYLE = 'background-color: white; border-color: black; border-style: solid; border-width: 1px'
_OK_BUTTON_STYLE = 'background-color: green; color: white; font-weight: bold'
_TARGET_TABLE_STYLE = 'background-color: white'
