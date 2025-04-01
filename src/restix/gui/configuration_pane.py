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
GUI-Bereich für die restix-Konfiguration.
"""

from typing import Callable

from PySide6.QtCore import Qt, QAbstractListModel, QPoint
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QFormLayout,
                               QLabel, QLineEdit, QSizePolicy, QPushButton, QTextEdit, QDialog, QTabWidget,
                               QMenu, QMessageBox, QListView)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.gui import *
from restix.gui.dialogs import ScopeEditorDialog
from restix.gui.model import ConfigModelFactory
from restix.gui.panes import GROUP_BOX_STYLE


class CredentialsDetailPane(QListView):
    """
    Pane zum Anzeigen und Editieren von Zugriffsdaten.
    """
    def __init__(self, parent: QWidget, include_name: bool = False):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param include_name: zeigt an, ob ein Eingabefeld für den Namen vorhanden sein soll
        """
        super().__init__(parent)
        self.__layout = QFormLayout()
        self.__layout.setContentsMargins(20, 20, 20, 20)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        if include_name:
            self.__name_text = QLineEdit()
            self.__name_text.setStyleSheet(TEXT_FIELD_STYLE)
            self.__name_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.__name_text.setToolTip(localized_label(T_CFG_CREDENTIAL_NAME))
            self.__layout.addRow(QLabel(localized_label(L_NAME)), self.__name_text)
        else:
            self.__name_text = None
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(localized_label(T_CFG_CREDENTIAL_COMMENT))
        self.__layout.addRow(QLabel(localized_label(L_COMMENT)), self.__comment_text)
        self.__type_combo = QComboBox()
        self.__type_combo.setMinimumWidth(240)
        self.__type_combo.setToolTip(localized_label(T_CFG_CREDENTIAL_TYPE))
        for _i, _type in enumerate(CFG_CREDENTIAL_TYPES):
            self.__type_combo.addItem(_type, _i)
        self.__type_combo.setCurrentIndex(-1)
        self.__type_combo.currentIndexChanged.connect(self._type_changed)
        self.__layout.addRow(QLabel(localized_label(L_TYPE)), self.__type_combo)
        self.__value_label = QLabel('')
        self.__value_text = QLineEdit()
        self.__value_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__value_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__value_text.setVisible(False)
        self.__layout.addRow(self.__value_label, self.__value_text)
        self.setLayout(self.__layout)

    def get_data(self) -> dict:
        """
        :returns: Zugriffsdaten
        """
        _data = {CFG_PAR_COMMENT: self.__comment_text.text(), CFG_PAR_TYPE: self.__type_combo.currentText()}
        if self.__name_text is not None:
            _data[CFG_PAR_ALIAS] = self.__name_text.text()
        if self.__value_text.isVisible():
            _data[CFG_PAR_VALUE] = self.__value_text.text()
        return _data

    def set_data(self, credential_data: dict):
        """
        Überträgt die Zugriffsdaten in die GUI widgets.
        :param credential_data: Zugriffsdaten
        """
        if self.__name_text is not None:
            self.__name_text.setText(credential_data[CFG_PAR_ALIAS])
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
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_PROMPT or credential_type == CFG_VALUE_CREDENTIALS_TYPE_TOKEN:
            self.__value_label.setText('')
            self.__value_label.setToolTip('')
            self.__value_text.setVisible(False)
            return
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_FILE:
            _tooltip = localized_label(T_CFG_CREDENTIAL_FILE_NAME)
            self.__value_label.setText(localized_label(L_FILE_NAME))
            self.__value_label.setToolTip(_tooltip)
            self.__value_text.setEchoMode(QLineEdit.EchoMode.Normal)
            self.__value_text.setText(value)
            self.__value_text.setVisible(True)
            return
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_TEXT:
            _tooltip = localized_label(T_CFG_CREDENTIAL_PASSWORD)
            self.__value_label.setText(localized_label(L_PASSWORD))
            self.__value_label.setToolTip(_tooltip)
            self.__value_text.setEchoMode(QLineEdit.EchoMode.Password)
            self.__value_text.setText(value)
            self.__value_text.setVisible(True)


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
        :param local_config: lokale restix-Konfiguration
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
        except RestixException as _e:
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
    def __init__(self, parent: QWidget, local_config: LocalConfig, title_id: str):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param local_config: lokale restix-Konfiguration
        :param title_id: Resource-ID für die Fensterüberschrift
        """
        super().__init__(parent)
        self.local_config = local_config
        self.data = {}
        self.setWindowTitle(localized_label(title_id))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _NEW_ELEMENT_DLG_OFFSET, _parent_rect.y() + _NEW_ELEMENT_DLG_OFFSET,
                         _NEW_ELEMENT_DLG_WIDTH, _NEW_ELEMENT_DLG_HEIGHT)
        self.setStyleSheet(EDITOR_STYLE)
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
        Wird aufgerufen, wenn der Benutzer den Hinzufügen-Button geklickt hat
        """
        pass

    @classmethod
    def for_group(cls, group: str, parent: QWidget, local_config: LocalConfig):
        if group == CFG_GROUP_CREDENTIALS:
            return NewCredentialDialog(parent, local_config)
        if group == CFG_GROUP_SCOPE:
            return NewScopeDialog(parent, local_config)


class NewCredentialDialog(NewElementDialog):
    """
    Dialogfenster für neue Zugriffsdaten.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__(parent, local_config, localized_label(L_DLG_TITLE_NEW_CREDENTIALS))
        self.__credentials_pane = CredentialsDetailPane(self, True)
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
        if _data[CFG_PAR_ALIAS] in self.local_config.credentials():
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
    def __init__(self, parent: QWidget, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__(parent, local_config, localized_label(L_DLG_TITLE_NEW_SCOPE))
        self.__scope_pane = ScopeDetailPane(self, True)
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
        if _data[CFG_PAR_ALIAS] in self.local_config.credentials():
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_SCOPE_EXISTS, _data[CFG_PAR_ALIAS]),
                                    QMessageBox.StandardButton.Ok)
            return
        self.data = _data
        self.accept()


class ElementSelectorPane(QWidget):
    """
    Pane zur Auswahl eines Elements in einer Group von Konfigurationsdaten.
    """
    def __init__(self, parent: QWidget, group: str, tooltip_id: str, local_config: LocalConfig,
                 combo_model: QAbstractListModel, selected_handler: Callable):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param group: die Element-Gruppe
        :param tooltip_id: Resource ID für den Tooltip-Text der Combo-Box
        :param local_config: lokale restix-Konfiguration
        :param combo_model: Model für die Combo-Box zur Auswahl der Elemente
        :param selected_handler: Handler, wenn ein Element in der Combo-Box ausgewählt wird
        """
        super().__init__(parent)
        self.__group = group
        self.__local_config = local_config
        _layout = QVBoxLayout(self)
        _layout.setContentsMargins(5, 5, 5, 5)
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
        _context_menu.setStyleSheet(CONTEXT_MENU_STYLE)
        _context_menu.exec(self.mapToGlobal(position))

    def _add_element(self):
        """
        Wird aufgerufen, wenn der Benutzer den "Neu"-Button geklickt hat.
        """
        _dlg = NewElementDialog.for_group(self.__group, self, self.__local_config)
        if _dlg.exec() == QDialog.DialogCode.Accepted:
            _index = self.__combo.model().index(self.__combo.count(), 0)
            self.__combo.model().setData(_index, _dlg.get_data())

    def _rename_element(self):
        """
        Wird aufgerufen, wenn der Benutzer den Eintrag "Umbenennen" im Kontextmenü ausgewählt hat
        """
        _dlg = RenameElementDialog(self, self.__group, self.__combo.currentText(), self.__local_config)
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
        try:
            self.__local_config.pre_check_remove(self.__group, _element_alias)
        except RestixException as _e:
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
        :param parent: die übergeordnete Pane
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent)
        self.__model_index = None
        _layout = QHBoxLayout(self)
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _layout.addWidget(ElementSelectorPane(self, CFG_GROUP_CREDENTIALS, T_CFG_CREDENTIAL_NAME,
                                              model_factory.configuration_data(),
                                              model_factory.credential_names_model(),
                                              self._credential_selected))
        _detail_group_box = QGroupBox('')
        _group_box_layout = QVBoxLayout(_detail_group_box)
        self.__detail_pane = CredentialsDetailPane(self)
        self.__detail_pane.setModel(model_factory.credentials_model())
        _group_box_layout.addWidget(self.__detail_pane)
        _update_button = QPushButton(localized_label(L_UPDATE))
        _update_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _update_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _update_button.clicked.connect(self._update_credential)
        _group_box_layout.addWidget(_update_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_detail_group_box)

    def _credential_selected(self, index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Zugriffsdaten ausgewählt hat.
        """
        self.__model_index = self.__detail_pane.model().createIndex(index, 0)
        self.__detail_pane.set_data(self.__detail_pane.model().data(self.__model_index, Qt.ItemDataRole.DisplayRole))

    def _update_credential(self):
        """
        Wird aufgerufen, wenn der Aktualisieren-Button gedrückt wurde.
        :return:
        """
        if self.__model_index is None:
            return
        self.__detail_pane.model().setData(self.__model_index, self.__detail_pane.get_data())


class ScopeDetailPane(QListView):
    """
    Pane zum Anzeigen und Editieren von Backup-Umfängen.
    """
    def __init__(self, parent: QWidget, include_name: bool = False):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param include_name: zeigt an, ob ein Eingabefeld für den Aliasnamen vorhanden sein soll
        """
        super().__init__(parent)
        self.__includes_file_name = None
        self.__excludes_file_name = None
        _layout = QFormLayout(self)
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        if include_name:
            self.__alias_text = QLineEdit()
            self.__alias_text.setStyleSheet(TEXT_FIELD_STYLE)
            self.__alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            self.__alias_text.setToolTip(localized_label(T_CFG_SCOPE_NAME))
            _layout.addRow(QLabel(localized_label(L_ALIAS)), self.__alias_text)
        else:
            self.__alias_text = None
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(localized_label(T_CFG_SCOPE_COMMENT))
        _layout.addRow(QLabel(localized_label(L_COMMENT)), self.__comment_text)
        self.__includes_button = QPushButton(localized_label(L_EDIT))
        self.__includes_button.setToolTip(localized_label(T_CFG_SCOPE_FILES_N_DIRS))
        self.__includes_button.clicked.connect(self._edit_files_n_dirs)
        _layout.addRow(QLabel(localized_label(L_FILES_N_DIRS)), self.__includes_button)
        self.__ignores_list = QTextEdit()
        self.__ignores_list.setStyleSheet(EDITOR_STYLE)
        self.__ignores_list.setMinimumHeight(100)
        self.__ignores_list.setMaximumHeight(200)
        self.__ignores_list.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.MinimumExpanding)
        self.__ignores_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        _layout.addRow(QLabel(localized_label(L_IGNORES)), self.__ignores_list)

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
        _scope_editor = ScopeEditorDialog(self, self.__includes_file_name, self.__excludes_file_name)
        if _scope_editor.exec_() != QDialog.DialogCode.Accepted:
            return


class ScopePane(QWidget):
    """
    Pane für die Backup-Umfänge.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param model_factory: Factory für die Qt-Models
        """
        super().__init__(parent)
        self.__model_index = None
        _layout = QHBoxLayout(self)
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _layout.addWidget(ElementSelectorPane(self, CFG_GROUP_SCOPE, T_CFG_SCOPE_NAME,
                                              model_factory.configuration_data(),
                                              model_factory.scope_names_model(),
                                              self._scope_selected))
        _detail_group_box = QGroupBox('')
        _group_box_layout = QVBoxLayout(_detail_group_box)
        self.__detail_pane = ScopeDetailPane(self)
        self.__detail_pane.setModel(model_factory.scope_model())
        _group_box_layout.addWidget(self.__detail_pane, alignment=Qt.AlignmentFlag.AlignTop)
        _update_button = QPushButton(localized_label(L_UPDATE))
        _update_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _update_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _update_button.clicked.connect(self._update_scope)
        _group_box_layout.addWidget(_update_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_detail_group_box)

    def _scope_selected(self, index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Backup-Umfänge ausgewählt hat.
        """
        self.__model_index = self.__detail_pane.model().createIndex(index, 0)
        self.__detail_pane.set_data(self.__detail_pane.model().data(self.__model_index, Qt.ItemDataRole.DisplayRole))

    def _update_scope(self):
        """
        Wird aufgerufen, wenn der Aktualisieren-Button gedrückt wurde.
        :return:
        """
        if self.__model_index is None:
            return
        self.__detail_pane.model().setData(self.__model_index, self.__detail_pane.get_data())


class TargetDetailPane(QWidget):
    """
    Pane zum Anzeigen und Editieren von Backup-Zielen.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        """
        super().__init__(parent)
        self.__orig_data = None
        self.__data = None
        self.__credential_names = []
        self.__scope_names = []
        _layout = QFormLayout(self)
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(localized_label(T_CFG_TARGET_COMMENT))
        _layout.addRow(QLabel(localized_label(L_COMMENT)), self.__comment_text)
        self.__location_text = QLineEdit()
        self.__location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__location_text.setToolTip(localized_label(T_CFG_TARGET_LOCATION))
        _layout.addRow(QLabel(localized_label(L_LOCATION)), self.__location_text)
        self.__credential_combo = QComboBox()
        self.__credential_combo.setMinimumWidth(240)
        self.__credential_combo.setToolTip(localized_label(T_CFG_TARGET_CREDENTIALS))
        self.__credential_combo.currentIndexChanged.connect(self._credentials_selected)
        _layout.addRow(QLabel(localized_label(L_CREDENTIALS)), self.__credential_combo)
        self.__scope_combo = QComboBox()
        self.__scope_combo.setMinimumWidth(240)
        self.__scope_combo.setToolTip(localized_label(T_CFG_TARGET_SCOPE))
        self.__scope_combo.currentIndexChanged.connect(self._scope_selected)
        _layout.addRow(QLabel(localized_label(L_SCOPE)), self.__scope_combo)

    def set_data(self, target_data: dict, credential_names: list[str], scope_names: list[str]):
        """
        Überträgt die Daten eines Backup-Ziels in die GUI widgets.
        :param target_data: Backup-Ziel
        """
        self.__orig_data = target_data
        self.__data = target_data.copy()
        self.__comment_text.setText(target_data[CFG_PAR_COMMENT])
        self.__location_text.setText(target_data[CFG_PAR_LOCATION])
        self.__credential_combo.currentIndexChanged.disconnect()
        self.__credential_combo.clear()
        self.__credential_combo.addItems(scope_names)
        self.__credential_combo.setCurrentText(target_data[CFG_PAR_CREDENTIALS])
        self.__credential_combo.currentIndexChanged.connect(self._credentials_selected)
        self.__scope_combo.currentIndexChanged.disconnect()
        self.__scope_combo.clear()
        self.__scope_combo.addItems(scope_names)
        self.__scope_combo.setCurrentText(target_data[CFG_PAR_SCOPE])
        self.__scope_combo.currentIndexChanged.connect(self._scope_selected)

    def _credentials_selected(self):
        print('_credentials_selected')

    def _scope_selected(self):
        print('_scope_selected')


class TargetPane(QGroupBox):
    """
    Pane für die Backup-Ziele.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__(localized_label(L_TARGETS), parent)
        self.__targets = local_config.targets()
        self.__config = local_config
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QHBoxLayout()
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__targets_combo = QComboBox()
        self.__detail_pane = TargetDetailPane(self)
        _layout.addWidget(self.__detail_pane)
        self.setLayout(_layout)

    def _target_selected(self, _index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Backup-Ziele ausgewählt hat.
        """
        _credential_names = [_c for _c in self.__config.credentials().keys()]
        _scope_names = [_s for _s in self.__config.scopes().keys()]
        self.__detail_pane.set_data(self.__targets_combo.currentData(Qt.ItemDataRole.UserRole),
                                    _credential_names, _scope_names)


class ConfigurationPane(QTabWidget):
    """
    Pane für die restix-Konfiguration.
    Enthält je ein Tab für Zugangsdaten, Backup-Umfänge und Backup-Ziele.
    """
    def __init__(self, parent: QWidget, model_factory: ConfigModelFactory):
        """
        Konstruktor.
        :param parent: die zentrale restix Pane
        :param model_factory: Factory für die Models
        """
        super().__init__(parent, tabsClosable=False)
        self.setStyleSheet(TAB_FOLDER_STYLE)
        self.addTab(CredentialsPane(self, model_factory), localized_label(L_CREDENTIALS))
        self.addTab(ScopePane(self, model_factory), localized_label(L_SCOPES))
        #self.addTab(TargetPane(self, local_config), localized_label(L_TARGETS))


_NEW_ELEMENT_DLG_HEIGHT = 480
_NEW_ELEMENT_DLG_OFFSET = 10
_NEW_ELEMENT_DLG_WIDTH = 640

_RENAME_ELEMENT_DLG_HEIGHT = 320
_RENAME_ELEMENT_DLG_OFFSET = 10
_RENAME_ELEMENT_DLG_WIDTH = 480
