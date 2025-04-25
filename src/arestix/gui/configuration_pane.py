# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# arestix - Datensicherung auf restic-Basis.
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
GUI-Bereich für die arestix-Konfiguration.
"""

from typing import Callable

from PySide6.QtCore import Qt, QAbstractListModel, QPoint
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListView,
                               QMenu, QMessageBox, QPushButton, QSizePolicy, QTabWidget, QTextEdit,
                               QVBoxLayout, QWidget, QFileDialog)

from arestix.core import *
from arestix.core.arestix_exception import ArestixException
from arestix.core.config import LocalConfig
from arestix.core.messages import *
from arestix.core.util import relative_config_path_of, full_config_path_of
from arestix.gui import *
from arestix.gui.editors import ScopeEditor
from arestix.gui.model import ConfigModelFactory


class CredentialsDetailPane(QListView):
    """
    Pane zum Anzeigen und Editieren von Zugriffsdaten.
    """
    def __init__(self, parent: QWidget, config_dir_path: str, include_alias: bool = False):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param config_dir_path: arestix-Konfigurationsverzeichnis
        :param include_alias: zeigt an, ob ein Eingabefeld für den Alias-Namen vorhanden sein soll
        """
        super().__init__(parent)
        self.__config_path = config_dir_path
        self.setStyleSheet(CONFIG_LIST_VIEW_STYLE)
        _layout = QFormLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN,
                                        WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        if include_alias:
            _alias_label = QLabel(localized_label(L_ALIAS))
            _alias_label.setToolTip(localized_label(T_CFG_CREDENTIAL_ALIAS))
            self.__alias_text = QLineEdit()
            self.__alias_text.setStyleSheet(TEXT_FIELD_STYLE)
            self.__alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.__alias_text.setToolTip(localized_label(T_CFG_CREDENTIAL_ALIAS))
            _layout.addRow(_alias_label, self.__alias_text)
            self.__value_row = 3
        else:
            self.__alias_text = None
            self.__value_row = 2
        _comment_label = QLabel(localized_label(L_COMMENT))
        _comment_label.setToolTip(localized_label(T_CFG_CREDENTIAL_COMMENT))
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(localized_label(T_CFG_CREDENTIAL_COMMENT))
        _layout.addRow(_comment_label, self.__comment_text)
        _type_label = QLabel(localized_label(L_TYPE))
        _type_label.setToolTip(localized_label(T_CFG_CREDENTIAL_TYPE))
        self.__type_combo = QComboBox()
        self.__type_combo.setMinimumWidth(MIN_COMBO_WIDTH)
        self.__type_combo.setStyleSheet(CONFIG_COMBO_BOX_STYLE)
        self.__type_combo.setToolTip(localized_label(T_CFG_CREDENTIAL_TYPE))
        for _i, _type in enumerate(CFG_CREDENTIAL_TYPES):
            self.__type_combo.addItem(_type, _i)
        self.__type_combo.setCurrentIndex(-1)
        self.__type_combo.currentIndexChanged.connect(self._type_changed)
        _layout.addRow(_type_label, self.__type_combo)
        self.__value_text = None
        self.__value_button = None

    def get_data(self) -> dict:
        """
        :returns: Zugriffsdaten
        """
        _data = {CFG_PAR_COMMENT: self.__comment_text.text(), CFG_PAR_TYPE: self.__type_combo.currentText()}
        if self.__alias_text is not None:
            _data[CFG_PAR_ALIAS] = self.__alias_text.text()
        if self.__value_text is not None:
            _data[CFG_PAR_VALUE] = self.__value_text.text()
        elif self.__value_button  is not None:
            _data[CFG_PAR_VALUE] = self.__value_button.text()
        return _data

    def set_data(self, credential_data: dict):
        """
        Überträgt die Zugriffsdaten in die GUI widgets.
        :param credential_data: Zugriffsdaten
        """
        if self.__alias_text is not None:
            self.__alias_text.setText(credential_data[CFG_PAR_ALIAS])
        self.__comment_text.setText(credential_data[CFG_PAR_COMMENT])
        _type = credential_data[CFG_PAR_TYPE]
        self.__type_combo.setCurrentText(_type)
        self._show_type(_type, credential_data.get(CFG_PAR_VALUE))

    def _type_changed(self, _index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen anderen Typ aus der Combobox ausgewählt hat.
        :param _index: Index des ausgewählten Credential-Typs
        """
        self._show_type(self.__type_combo.currentText(), '')

    def _show_type(self, credential_type: str, value: str | None):
        """
        Zeigt den Wert zu einem Credential-Typ an.
        :param credential_type: Credential-Typ
        :param value: Dateiname oder Passwort
        """
        if self.layout().rowCount() > self.__value_row:
            self.layout().removeRow(self.__value_row)
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_PROMPT or credential_type == CFG_VALUE_CREDENTIALS_TYPE_TOKEN:
            self.__value_button = None
            self.__value_text = None
            return
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_FILE:
            _tooltip = localized_label(T_CFG_CREDENTIAL_FILE_NAME)
            _value_label = QLabel(localized_label(L_FILE_NAME))
            _value_label.setToolTip(_tooltip)
            self.__value_button = QPushButton(value)
            self.__value_button.clicked.connect(self._select_password_file)
            self.__value_button.setToolTip(_tooltip)
            self.layout().addRow(_value_label, self.__value_button)
            return
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_TEXT:
            _tooltip = localized_label(T_CFG_CREDENTIAL_PASSWORD)
            _value_label = QLabel(localized_label(L_PASSWORD))
            _value_label.setToolTip(_tooltip)
            self.__value_text = QLineEdit()
            self.__value_text.setStyleSheet(TEXT_FIELD_STYLE)
            self.__value_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.__value_text.setEchoMode(QLineEdit.EchoMode.Password)
            self.__value_text.setText(value)
            self.__value_text.setToolTip(_tooltip)
            self.layout().addRow(_value_label, self.__value_text)

    def _select_password_file(self):
        """
        Wird aufgerufen, wenn der Benutzer auf den Button mit dem Dateinamen der Passwort-Datei klickt.
        """
        _current_file_path = full_config_path_of(self.__value_button.text(), self.__config_path)
        _file_path, _ = QFileDialog.getOpenFileName(self, localized_label(L_DLG_TITLE_SELECT_FILE), _current_file_path)
        if len(_file_path) > 0:
            self.__value_button.setText(relative_config_path_of(_file_path, self.__config_path))


class RenameElementDialog(QDialog):
    """
    Dialogfenster zum Umbenennen eines Elements.
    """
    def __init__(self, parent: QWidget, group: str, current_alias: str, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param group: Gruppe des Elements
        :param current_alias: aktueller Aliasname des Elements
        :param local_config: lokale arestix-Konfiguration
        """
        super().__init__(parent)
        self.__group = group
        self.__local_config = local_config
        self.__new_alias = None
        self.setWindowTitle(localized_message(L_DLG_TITLE_RENAME_ELEMENT, group))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _RENAME_ELEMENT_DLG_OFFSET, _parent_rect.y() + _RENAME_ELEMENT_DLG_OFFSET,
                         _RENAME_ELEMENT_DLG_WIDTH, _RENAME_ELEMENT_DLG_HEIGHT)
        self.setStyleSheet(EDITOR_STYLE)
        _layout = QVBoxLayout(self)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _alias_pane = QWidget()
        _alias_pane_layout = QFormLayout(_alias_pane)
        _current_alias_label = QLabel(localized_label(L_CURRENT_ALIAS))
        self.__current_alias_text = QLineEdit(current_alias, readOnly=True)
        _alias_pane_layout.addRow(_current_alias_label, self.__current_alias_text)
        _new_alias_label = QLabel(localized_label(L_NEW_ALIAS))
        self.__new_alias_text = QLineEdit()
        self.__new_alias_text.setStyleSheet(TEXT_FIELD_STYLE)
        _alias_pane_layout.addRow(_new_alias_label, self.__new_alias_text)
        _layout.addWidget(_alias_pane)
        _button_pane = QWidget()
        _button_pane_layout = QHBoxLayout(_button_pane)
        _rename_button = QPushButton(localized_label(L_RENAME))
        _rename_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _rename_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _rename_button.clicked.connect(self._rename_button_clicked)
        _button_pane_layout.addWidget(_rename_button)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.setStyleSheet(CANCEL_BUTTON_STYLE)
        _cancel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _cancel_button.clicked.connect(self.reject)
        _button_pane_layout.addWidget(_cancel_button)
        _layout.addWidget(_button_pane)

    def get_new_alias(self) -> str:
        """
        :returns: vom Benutzer eingegebener neuer Aliasname
        """
        return self.__new_alias

    def _rename_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den Umbenennen-Button geklickt hat
        """
        _old_alias = self.__current_alias_text.text()
        _new_alias = self.__new_alias_text.text()
        if _new_alias == _old_alias:
            self.reject()
            return
        try:
            self.__local_config.pre_check_rename(self.__group, _old_alias, _new_alias)
        except ArestixException as _e:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    str(_e),
                                    QMessageBox.StandardButton.Ok)
            return
        self.__new_alias = _new_alias
        self.accept()


class NewElementDialog(QDialog):
    """
    Basisklasse der Dialogfenster für neue Elemente.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory, title_id: str):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param model_factory: Factory für die Qt-Models
        :param title_id: Resource-ID für die Fensterüberschrift
        """
        super().__init__(parent)
        self.model_factory = model_factory
        self.data = {}
        self.setWindowTitle(localized_label(title_id))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _NEW_ELEMENT_DLG_OFFSET, _parent_rect.y() + _NEW_ELEMENT_DLG_OFFSET,
                         _NEW_ELEMENT_DLG_WIDTH, _NEW_ELEMENT_DLG_HEIGHT)
        self.setStyleSheet('QDialog {background: #fefedd; border: 0px}')
        _layout = QVBoxLayout(self)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def create_button_pane(self):
        """
        :returns: Pane mit den Buttons zum Übernehmen der Eingabedaten oder zum Abbruch
        """
        _button_pane = QWidget()
        _button_pane_layout = QHBoxLayout(_button_pane)
        _add_button = QPushButton(localized_label(L_ADD))
        _add_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _add_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _add_button.clicked.connect(self.add_button_clicked)
        _button_pane_layout.addWidget(_add_button)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.setStyleSheet(CANCEL_BUTTON_STYLE)
        _cancel_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _cancel_button.clicked.connect(self.reject)
        _button_pane_layout.addWidget(_cancel_button)
        self.layout().addWidget(_button_pane)

    def get_data(self) -> dict:
        """
        :returns: vom Benutzer eingegebene Daten
        """
        return self.data

    def add_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den Hinzufügen-Button geklickt hat.
        Funktionalität wird in den abgeleiteten Klassen implementiert.
        """
        pass

    @classmethod
    def for_group(cls, group: str, parent: QWidget, model_factory: ConfigModelFactory):
        """
        :param group: Group (Zugriffsdaten, Backup-Umfang oder Backup-Ziel)
        :param parent: übergeordnetes Widget
        :param model_factory: Factory für die Qt-Models
        :returns: Dialogfenster zum Erzeugen eines neuen Elements der angegebenen Group
        """
        if group == CFG_GROUP_CREDENTIALS:
            return NewCredentialDialog(parent, model_factory)
        if group == CFG_GROUP_SCOPE:
            return NewScopeDialog(parent, model_factory)
        if group == CFG_GROUP_TARGET:
            return NewTargetDialog(parent, model_factory)


class NewCredentialDialog(NewElementDialog):
    """
    Dialogfenster für neue Zugriffsdaten.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent, model_factory, localized_label(L_DLG_TITLE_NEW_CREDENTIALS))
        self.__credentials_pane = CredentialsDetailPane(self, model_factory.configuration_data().path(), True)
        self.layout().addWidget(self.__credentials_pane)
        self.create_button_pane()

    def add_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den Hinzufügen-Button geklickt hat
        """
        _data = self.__credentials_pane.get_data()
        if len(_data[CFG_PAR_ALIAS]) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_label(I_GUI_NO_NAME_SPECIFIED),
                                    QMessageBox.StandardButton.Ok)
            return
        _local_config = self.model_factory.configuration_data()
        if _data[CFG_PAR_ALIAS] in _local_config.credentials():
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_CREDENTIAL_EXISTS, _data[CFG_PAR_ALIAS]),
                                    QMessageBox.StandardButton.Ok)
            return
        if len(_data[CFG_PAR_TYPE]) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_label(I_GUI_NO_CREDENTIAL_TYPE_SPECIFIED),
                                    QMessageBox.StandardButton.Ok)
            return
        self.data = _data
        self.accept()


class NewScopeDialog(NewElementDialog):
    """
    Dialogfenster für neue Backup-Umfänge.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent, model_factory, localized_label(L_DLG_TITLE_NEW_SCOPE))
        _config_path = model_factory.configuration_data().path()
        self.__scope_pane = ScopeDetailPane(self, _config_path, True)
        self.layout().addWidget(self.__scope_pane)
        self.create_button_pane()

    def add_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den Hinzufügen-Button geklickt hat
        """
        _data = self.__scope_pane.get_data()
        if len(_data[CFG_PAR_ALIAS]) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_label(I_GUI_NO_NAME_SPECIFIED),
                                    QMessageBox.StandardButton.Ok)
            return
        _local_config = self.model_factory.configuration_data()
        if _data[CFG_PAR_ALIAS] in _local_config.scopes():
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_SCOPE_EXISTS, _data[CFG_PAR_ALIAS]),
                                    QMessageBox.StandardButton.Ok)
            return
        self.data = _data
        self.accept()


class NewTargetDialog(NewElementDialog):
    """
    Dialogfenster für neue Backup-Ziele.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent, model_factory, localized_label(L_DLG_TITLE_NEW_TARGET))
        self.__target_pane = TargetDetailPane(self, model_factory, True)
        self.layout().addWidget(self.__target_pane)
        self.create_button_pane()

    def add_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den Hinzufügen-Button geklickt hat
        """
        _data = self.__target_pane.get_data()
        if len(_data[CFG_PAR_ALIAS]) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_label(I_GUI_NO_NAME_SPECIFIED),
                                    QMessageBox.StandardButton.Ok)
            return
        _local_config = self.model_factory.configuration_data()
        if _data[CFG_PAR_ALIAS] in _local_config.targets():
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_TARGET_EXISTS, _data[CFG_PAR_ALIAS]),
                                    QMessageBox.StandardButton.Ok)
            return
        self.data = _data
        self.accept()


class ElementSelectorPane(QWidget):
    """
    Pane zur Auswahl eines Elements in einer Group von Konfigurationsdaten.
    """
    def __init__(self, parent: QWidget, group: str, tooltip_id: str, model_factory: ConfigModelFactory,
                 combo_model: QAbstractListModel, selected_handler: Callable):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param group: Element-Gruppe
        :param tooltip_id: Resource ID für den Tooltip-Text der Combo-Box
        :param model_factory: Factory für die Qt-Models
        :param combo_model: Model für die Combo-Box zur Auswahl der Elemente
        :param selected_handler: Handler, wenn ein Element in der Combo-Box ausgewählt wird
        """
        super().__init__(parent)
        self.__group = group
        self.__model_factory = model_factory
        _layout = QVBoxLayout(self)
        _layout.setContentsMargins(SMALL_CONTENT_MARGIN, SMALL_CONTENT_MARGIN,
                                   SMALL_CONTENT_MARGIN, SMALL_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__combo = QComboBox()
        self.__combo.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.__combo.customContextMenuRequested.connect(self._show_context_menu)
        self.__combo.setModel(combo_model)
        self.__combo.setCurrentIndex(-1)
        self.__combo.currentIndexChanged.connect(selected_handler)
        self.__combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.__combo.setToolTip(localized_label(tooltip_id))
        _layout.addWidget(self.__combo)
        _new_button = QPushButton(localized_label(L_NEW))
        _new_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _new_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _new_button.clicked.connect(self._add_element)
        _layout.addWidget(_new_button)

    def _show_context_menu(self, position: QPoint):
        """
        Wird aufgerufen, wenn der Benutzer mit der rechten Maustaste auf ein Element der Combo-Box klickt.
        """
        _context_menu = QMenu(self.__combo)
        _context_menu.addAction(localized_label(L_MENU_RENAME)).triggered.connect(self._rename_element)
        _context_menu.addAction(localized_label(L_MENU_REMOVE)).triggered.connect(self._remove_element)
        _context_menu.setStyleSheet(CONFIG_CONTEXT_MENU_STYLE)
        _context_menu.exec(self.mapToGlobal(position))

    def _add_element(self):
        """
        Wird aufgerufen, wenn der Benutzer den "Neu"-Button geklickt hat.
        """
        _dlg = NewElementDialog.for_group(self.__group, self, self.__model_factory)
        if _dlg.exec() == QDialog.DialogCode.Accepted:
            _index = self.__combo.model().index(self.__combo.count(), 0)
            self.__combo.model().setData(_index, _dlg.get_data())

    def _rename_element(self):
        """
        Wird aufgerufen, wenn der Benutzer den Eintrag "Umbenennen" im Kontextmenü ausgewählt hat
        """
        _local_config = self.__model_factory.configuration_data()
        _dlg = RenameElementDialog(self, self.__group, self.__combo.currentText(), _local_config)
        if _dlg.exec() == QDialog.DialogCode.Accepted:
            _index = self.__combo.model().index(self.__combo.currentIndex(), 0)
            _element_data = self.__combo.model().data(_index, Qt.ItemDataRole.UserRole)
            _element_data[CFG_PAR_ALIAS] = _dlg.get_new_alias()
            self.__combo.model().setData(_index, _element_data)

    def _remove_element(self):
        """
        Wird aufgerufen, wenn der Benutzer den Eintrag "Löschen" im Kontextmenü ausgewählt hat
        """
        _element_alias = self.__combo.currentText()
        _local_config = self.__model_factory.configuration_data()
        try:
            _local_config.pre_check_remove(self.__group, _element_alias)
        except ArestixException as _e:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    str(_e),
                                    QMessageBox.StandardButton.Ok)
            return
        if QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                   localized_message(I_GUI_CONFIRM_REMOVE, _element_alias),
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
            self.__combo.model().removeRow(self.__combo.currentIndex())


class CredentialsPane(QWidget):
    """
    Pane für die Zugriffsdaten.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent)
        self.__model_index = None
        _layout = QHBoxLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _layout.addWidget(ElementSelectorPane(self, CFG_GROUP_CREDENTIALS, T_CFG_CREDENTIAL_ALIAS,
                                              model_factory, model_factory.credential_names_model(),
                                              self._credential_selected), 1)
        _detail_group_box = QGroupBox('')
        _detail_group_box.setStyleSheet(CONFIG_GROUP_BOX_STYLE)
        _group_box_layout = QVBoxLayout(_detail_group_box)
        self.__detail_pane = CredentialsDetailPane(self, model_factory.configuration_data().path())
        self.__detail_pane.setModel(model_factory.credentials_model())
        _group_box_layout.addWidget(self.__detail_pane)
        _update_button = QPushButton(localized_label(L_UPDATE))
        _update_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _update_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _update_button.clicked.connect(self._update_credential)
        _group_box_layout.addWidget(_update_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_detail_group_box, 2)

    def _credential_selected(self, index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Zugriffsdaten ausgewählt hat.
        """
        self.__model_index = self.__detail_pane.model().createIndex(index, 0)
        self.__detail_pane.set_data(self.__detail_pane.model().data(self.__model_index, Qt.ItemDataRole.DisplayRole))

    def _update_credential(self):
        """
        Wird aufgerufen, wenn der Aktualisieren-Button gedrückt wurde.
        """
        if self.__model_index is None:
            return
        self.__detail_pane.model().setData(self.__model_index, self.__detail_pane.get_data())


class ScopeDetailPane(QListView):
    """
    Pane zum Anzeigen und Editieren von Backup-Umfängen.
    """
    def __init__(self, parent: QWidget, config_path: str, include_name: bool = False):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param config_path: Verzeichnis der lokalen arestix-Konfiguration
        :param include_name: zeigt an, ob ein Eingabefeld für den Aliasnamen vorhanden sein soll
        """
        super().__init__(parent)
        self.__config_path = config_path
        self.__includes_file_name = None
        self.__excludes_file_name = None
        self.setStyleSheet(CONFIG_LIST_VIEW_STYLE)
        _layout = QFormLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        if include_name:
            _tooltip = localized_label(T_CFG_SCOPE_ALIAS)
            _alias_label = QLabel(localized_label(L_ALIAS))
            _alias_label.setToolTip(_tooltip)
            self.__alias_text = QLineEdit()
            self.__alias_text.setStyleSheet(TEXT_FIELD_STYLE)
            self.__alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.__alias_text.setToolTip(_tooltip)
            _layout.addRow(_alias_label, self.__alias_text)
        else:
            self.__alias_text = None
        _tooltip = localized_label(T_CFG_SCOPE_COMMENT)
        _comment_label = QLabel(localized_label(L_COMMENT))
        _comment_label.setToolTip(_tooltip)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(_tooltip)
        _layout.addRow(_comment_label, self.__comment_text)
        _tooltip = localized_label(T_CFG_SCOPE_FILES_N_DIRS)
        _edit_label = QLabel(localized_label(L_FILES_N_DIRS))
        _edit_label.setToolTip(_tooltip)
        self.__edit_scope_button = QPushButton(localized_label(L_EDIT))
        self.__edit_scope_button.setToolTip(_tooltip)
        self.__edit_scope_button.clicked.connect(self._edit_files_n_dirs)
        _layout.addRow(_edit_label, self.__edit_scope_button)
        _tooltip = localized_label(T_CFG_SCOPE_IGNORES)
        _ignores_label = QLabel(localized_label(L_IGNORES))
        _ignores_label.setToolTip(_tooltip)
        self.__ignores_list = QTextEdit()
        self.__ignores_list.setStyleSheet(CONFIG_TEXT_EDIT_STYLE)
        self.__ignores_list.setMinimumHeight(_MIN_IGNORES_LIST_HEIGHT)
        self.__ignores_list.setMaximumHeight(_MAX_IGNORES_LIST_HEIGHT)
        self.__ignores_list.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.MinimumExpanding)
        self.__ignores_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__ignores_list.setToolTip(_tooltip)
        _layout.addRow(_ignores_label, self.__ignores_list)

    def get_data(self) -> dict:
        """
        :returns: Backup-Umfang
        """
        _data = {CFG_PAR_COMMENT: self.__comment_text.text(), CFG_PAR_INCLUDES: self.__includes_file_name}
        if self.__alias_text is not None:
            _data[CFG_PAR_ALIAS] = self.__alias_text.text()
        if self.__excludes_file_name is not None:
            _data[CFG_PAR_EXCLUDES] = self.__excludes_file_name
        _ignores_list = self.__ignores_list.toPlainText()
        if len(_ignores_list) > 0:
            _data[CFG_PAR_IGNORES] = _ignores_list.split(os.sep)
        return _data

    def set_data(self, scope_data: dict):
        """
        Überträgt die Daten eines Backup-Umfangs in die GUI widgets.
        :param scope_data: Backup-Umfang
        """
        if self.__alias_text is not None:
            self.__alias_text.setText(scope_data[CFG_PAR_ALIAS])
        self.__comment_text.setText(scope_data[CFG_PAR_COMMENT])
        self.__includes_file_name = scope_data[CFG_PAR_INCLUDES]
        self.__excludes_file_name = scope_data.get(CFG_PAR_EXCLUDES)
        self.__ignores_list.clear()
        _ignores = scope_data.get(CFG_PAR_IGNORES)
        if _ignores is not None:
            for _ignore_pattern in _ignores:
                self.__ignores_list.append(_ignore_pattern)

    def _edit_files_n_dirs(self):
        """
        Wird aufgerufen, wenn der Benutzer den "Editieren"-Button klickt.
        Startet den Scope-Editor zur Auswahl ein- und auszuschließender Dateien und Verzeichnisse.
        """
        _ignores = self.__ignores_list.toPlainText().split(os.linesep)
        _scope_editor = ScopeEditor(self, self.__config_path, self.__includes_file_name, self.__excludes_file_name,
                                    _ignores)
        if _scope_editor.exec() != QDialog.DialogCode.Accepted:
            return
        _editor_includes_file_name, _editor_excludes_file_name = _scope_editor.scope_files()
        self.__includes_file_name = relative_config_path_of(_editor_includes_file_name, self.__config_path)
        self.__excludes_file_name = relative_config_path_of(_editor_excludes_file_name, self.__config_path)


class ScopePane(QWidget):
    """
    Pane für die Backup-Umfänge.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent)
        self.__model_index = None
        _layout = QHBoxLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _layout.addWidget(ElementSelectorPane(self, CFG_GROUP_SCOPE, T_CFG_SCOPE_ALIAS,
                                              model_factory, model_factory.scope_names_model(),
                                              self._scope_selected), 1)
        _detail_group_box = QGroupBox('')
        _detail_group_box.setStyleSheet(CONFIG_GROUP_BOX_STYLE)
        _group_box_layout = QVBoxLayout(_detail_group_box)
        self.__detail_pane = ScopeDetailPane(self, model_factory.configuration_data().path())
        self.__detail_pane.setModel(model_factory.scope_model())
        _group_box_layout.addWidget(self.__detail_pane, alignment=Qt.AlignmentFlag.AlignTop)
        _update_button = QPushButton(localized_label(L_UPDATE))
        _update_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _update_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _update_button.clicked.connect(self._update_scope)
        _group_box_layout.addWidget(_update_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_detail_group_box, 2)

    def _scope_selected(self, index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Backup-Umfänge ausgewählt hat.
        """
        self.__model_index = self.__detail_pane.model().createIndex(index, 0)
        self.__detail_pane.set_data(self.__detail_pane.model().data(self.__model_index, Qt.ItemDataRole.DisplayRole))

    def _update_scope(self):
        """
        Wird aufgerufen, wenn der Aktualisieren-Button gedrückt wurde.
        :returns:
        """
        if self.__model_index is None:
            return
        self.__detail_pane.model().setData(self.__model_index, self.__detail_pane.get_data())


class TargetDetailPane(QListView):
    """
    Pane zum Anzeigen und Editieren von Backup-Zielen.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory, include_name: bool = False):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param model_factory: Factory für die Qt-Models
        :param include_name: zeigt an, ob ein Eingabefeld für den Aliasnamen vorhanden sein soll
        """
        super().__init__(parent)
        self.setStyleSheet(CONFIG_LIST_VIEW_STYLE)
        _layout = QFormLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        if include_name:
            _tooltip = localized_label(T_CFG_TARGET_ALIAS)
            _alias_label = QLabel(localized_label(L_ALIAS))
            _alias_label.setToolTip(_tooltip)
            self.__alias_text = QLineEdit()
            self.__alias_text.setStyleSheet(TEXT_FIELD_STYLE)
            self.__alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.__alias_text.setToolTip(_tooltip)
            _layout.addRow(_alias_label, self.__alias_text)
        else:
            self.__alias_text = None
        _tooltip = localized_label(T_CFG_TARGET_COMMENT)
        _comment_label = QLabel(localized_label(L_COMMENT))
        _comment_label.setToolTip(_tooltip)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(_tooltip)
        _layout.addRow(_comment_label, self.__comment_text)
        _tooltip = localized_label(T_CFG_TARGET_LOCATION)
        _location_label = QLabel(localized_label(L_LOCATION))
        _location_label.setToolTip(_tooltip)
        self.__location_text = QLineEdit()
        self.__location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__location_text.setToolTip(_tooltip)
        _layout.addRow(_location_label, self.__location_text)
        _tooltip = localized_label(T_CFG_TARGET_CREDENTIALS)
        _credentials_label = QLabel(localized_label(L_CREDENTIALS))
        _credentials_label.setToolTip(_tooltip)
        self.__credential_combo = QComboBox()
        self.__credential_combo.setMinimumWidth(MIN_COMBO_WIDTH)
        self.__credential_combo.setToolTip(_tooltip)
        self.__credential_combo.setModel(model_factory.credential_names_model())
        _layout.addRow(_credentials_label, self.__credential_combo)
        _tooltip = localized_label(T_CFG_TARGET_SCOPE)
        _scope_label = QLabel(localized_label(L_SCOPE))
        _scope_label.setToolTip(_tooltip)
        self.__scope_combo = QComboBox()
        self.__scope_combo.setMinimumWidth(MIN_COMBO_WIDTH)
        self.__scope_combo.setToolTip(_tooltip)
        self.__scope_combo.setModel(model_factory.scope_names_model())
        _layout.addRow(_scope_label, self.__scope_combo)

    def get_data(self) -> dict:
        """
        :returns: Backup-Ziel
        """
        _data = {CFG_PAR_COMMENT: self.__comment_text.text(), CFG_PAR_LOCATION: self.__location_text.text(),
                 CFG_PAR_SCOPE: self.__scope_combo.currentText(),
                 CFG_PAR_CREDENTIALS: self.__credential_combo.currentText()}
        if self.__alias_text is not None:
            _data[CFG_PAR_ALIAS] = self.__alias_text.text()
        return _data


    def set_data(self, target_data: dict):
        """
        Überträgt die Daten eines Backup-Ziels in die GUI widgets.
        :param target_data: Backup-Ziel
        """
        if self.__alias_text is not None:
            self.__alias_text.setText(target_data[CFG_PAR_ALIAS])
        self.__comment_text.setText(target_data[CFG_PAR_COMMENT])
        self.__location_text.setText(target_data[CFG_PAR_LOCATION])
        self.__credential_combo.setCurrentText(target_data[CFG_PAR_CREDENTIALS])
        self.__scope_combo.setCurrentText(target_data[CFG_PAR_SCOPE])


class TargetPane(QGroupBox):
    """
    Pane für die Backup-Ziele.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent)
        self.__model_index = None
        _layout = QHBoxLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _layout.addWidget(ElementSelectorPane(self, CFG_GROUP_TARGET, T_CFG_TARGET_ALIAS,
                                              model_factory, model_factory.target_names_model(),
                                              self._target_selected), 1)
        _detail_group_box = QGroupBox('')
        _detail_group_box.setStyleSheet(CONFIG_GROUP_BOX_STYLE)
        _group_box_layout = QVBoxLayout(_detail_group_box)
        self.__detail_pane = TargetDetailPane(self, model_factory)
        self.__detail_pane.setModel(model_factory.target_model())
        _group_box_layout.addWidget(self.__detail_pane, alignment=Qt.AlignmentFlag.AlignTop)
        _update_button = QPushButton(localized_label(L_UPDATE))
        _update_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _update_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _update_button.clicked.connect(self._update_target)
        _group_box_layout.addWidget(_update_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_detail_group_box, 2)

    def _target_selected(self, index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Backup-Ziele ausgewählt hat.
        """
        self.__model_index = self.__detail_pane.model().createIndex(index, 0)
        self.__detail_pane.set_data(self.__detail_pane.model().data(self.__model_index, Qt.ItemDataRole.DisplayRole))

    def _update_target(self):
        """
        Wird aufgerufen, wenn der Aktualisieren-Button gedrückt wurde.
        """
        if self.__model_index is None:
            return
        self.__detail_pane.model().setData(self.__model_index, self.__detail_pane.get_data())


class ConfigurationPane(QTabWidget):
    """
    Pane für die arestix-Konfiguration.
    Enthält je ein Tab für Zugangsdaten, Backup-Umfänge und Backup-Ziele.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: zentrale arestix Pane
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent, tabsClosable=False)
        self.setContentsMargins(DEFAULT_CONTENT_MARGIN, DEFAULT_CONTENT_MARGIN,
                                DEFAULT_CONTENT_MARGIN, DEFAULT_CONTENT_MARGIN)
        self.setStyleSheet(TAB_FOLDER_STYLE)
        self.addTab(CredentialsPane(self, model_factory), localized_label(L_CREDENTIALS))
        self.addTab(ScopePane(self, model_factory), localized_label(L_SCOPES))
        self.addTab(TargetPane(self, model_factory), localized_label(L_TARGETS))


_MAX_IGNORES_LIST_HEIGHT = 200
_MIN_IGNORES_LIST_HEIGHT = 100

_NEW_ELEMENT_DLG_HEIGHT = 480
_NEW_ELEMENT_DLG_OFFSET = 10
_NEW_ELEMENT_DLG_WIDTH = 640

_RENAME_ELEMENT_DLG_HEIGHT = 320
_RENAME_ELEMENT_DLG_OFFSET = 10
_RENAME_ELEMENT_DLG_WIDTH = 480
