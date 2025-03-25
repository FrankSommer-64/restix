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

from PySide6.QtCore import Qt, QDir
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QFormLayout,
                               QLabel, QLineEdit, QSizePolicy, QPushButton, QFileDialog)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.gui import TEXT_FIELD_STYLE, ClickButton
from restix.gui.panes import GROUP_BOX_STYLE, option_label


class CredentialsDetailPane(QWidget):
    """
    Pane zum Anzeigen und Editieren von Zugriffsdaten.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        """
        super().__init__(parent)
        self.__layout = QFormLayout()
        self.__layout.setContentsMargins(20, 20, 20, 20)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__name_text = QLineEdit()
        self.__name_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__name_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.__name_text.setToolTip(localized_label(T_CFG_CREDENTIAL_NAME))
        self.__layout.addRow(QLabel(localized_label(L_NAME)), self.__name_text)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
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
        self.__filename_text = None
        self.__password_text = None
        self.setLayout(self.__layout)

    def set_data(self, credential_data: dict):
        """
        Überträgt die Zugriffsdaten in die GUI widgets.
        :param credential_data: Zugriffsdaten
        """
        self.__name_text.setText(credential_data[CFG_PAR_NAME])
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
        if credential_type == CFG_VALUE_CREDENTIALS_TYPE_FILE:
            if self.__password_text is not None:
                self.__layout.removeRow(3)
                self.__password_text = None
            if self.__filename_text is None:
                self.__filename_text = QLineEdit()
                self.__filename_text.setStyleSheet(TEXT_FIELD_STYLE)
                self.__filename_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                self.__filename_text.setToolTip(localized_label(T_CFG_CREDENTIAL_FILE_NAME))
                self.__layout.insertRow(3, QLabel(localized_label(L_FILE_NAME)), self.__filename_text)
            self.__filename_text.setText(value)
        elif credential_type == CFG_VALUE_CREDENTIALS_TYPE_TEXT:
            if self.__filename_text is not None:
                self.__layout.removeRow(3)
                self.__filename_text = None
            if self.__password_text is None:
                self.__password_text = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
                self.__password_text.setStyleSheet(TEXT_FIELD_STYLE)
                self.__password_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                self.__password_text.setToolTip(localized_label(T_CFG_CREDENTIAL_PASSWORD))
                self.__layout.insertRow(3, QLabel(localized_label(L_PASSWORD)), self.__password_text)
            self.__password_text.setText(value)
        else:
            if self.__filename_text is not None or self.__password_text is not None:
                self.__layout.removeRow(3)
            self.__filename_text = None
            self.__password_text = None


class ScopeDetailPane(QWidget):
    """
    Pane zum Anzeigen und Editieren von Backup-Umfängen.
[[scope]]
includes = "minimal.list"
excludes = "minimal_excludes.list"
ignores = [".git", ".idea", ".pytest_cache", ".venv", "__pycache__"]
    """
    def __init__(self, parent: QWidget, config_path: str):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param config_path: Pfad zur lokalen restix-Konfiguration
        """
        super().__init__(parent)
        self.__config_path = config_path
        self.__orig_data = None
        self.__data = None
        self.__is_empty = True
        self.__layout = QFormLayout()
        self.__layout.setContentsMargins(20, 20, 20, 20)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__name_text = QLineEdit()
        self.__name_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__name_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.__name_text.setToolTip(localized_label(T_CFG_SCOPE_NAME))
        self.__layout.addRow(QLabel(localized_label(L_NAME)), self.__name_text)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.__comment_text.setToolTip(localized_label(T_CFG_SCOPE_COMMENT))
        self.__layout.addRow(QLabel(localized_label(L_COMMENT)), self.__comment_text)
        self.__includes_button = ClickButton()
        self.__includes_button.setToolTip(localized_label(T_CFG_SCOPE_INCLUDES))
        self.__includes_button.clicked.connect(self._edit_includes_file)
        self.__includes_button.right_clicked.connect(self._change_includes_file)
        self.__layout.addRow(QLabel(localized_label(L_INCLUDES_FILE)), self.__includes_button)
        self.__excludes_button = ClickButton()
        self.__excludes_button.setToolTip(localized_label(T_CFG_SCOPE_INCLUDES))
        self.__excludes_button.clicked.connect(self._edit_excludes_file)
        self.__excludes_button.right_clicked.connect(self._change_excludes_file)
        self.__layout.addRow(QLabel(localized_label(L_EXCLUDES_FILE)), self.__excludes_button)
        self.setLayout(self.__layout)

    def set_data(self, scope_data: dict):
        """
        Überträgt die Daten eines Backup-Umfangs in die GUI widgets.
        :param scope_data: Backup-Umfang
        """
        self.__orig_data = scope_data
        self.__data = scope_data.copy()
        self.__is_empty = False
        self.__name_text.setText(scope_data[CFG_PAR_NAME])
        self.__comment_text.setText(scope_data[CFG_PAR_COMMENT])
        _includes_file_path = scope_data[CFG_PAR_INCLUDES]
        if os.path.isabs(_includes_file_path):
            self.__includes_button.setText(os.path.basename(_includes_file_path))
        else:
            self.__includes_button.setText(_includes_file_path)
        _excludes_file_path = scope_data.get(CFG_PAR_EXCLUDES)
        if _excludes_file_path is not None:
            if os.path.isabs(_excludes_file_path):
                self.__excludes_button.setText(os.path.basename(_excludes_file_path))
            else:
                self.__excludes_button.setText(_excludes_file_path)

    def _edit_includes_file(self):
        print('_edit_includes')

    def _change_includes_file(self):
        """
        Wird aufgerufen, wenn der Benutzer mit der rechten Maustaste auf den Includes-Button klickt.
        """
        if self.__is_empty:
            return
        _dlg = QFileDialog(self, localized_label(L_DLG_TITLE_SELECT_INCLUDES_FILE), self.__config_path)
        _dlg.setOptions(QFileDialog.Option.DontUseNativeDialog)
        _dlg.setFilter(QDir.Filter.AllDirs | QDir.Filter.Hidden)
        _dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        _dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        if _dlg.exec():
            self.__data[CFG_PAR_INCLUDES] = _dlg.selectedFiles()[0]
        _dlg.close()

    def _edit_excludes_file(self):
        print('_edit_excludes')

    def _change_excludes_file(self):
        """
        Wird aufgerufen, wenn der Benutzer mit der rechten Maustaste auf den Excludes-Button klickt.
        """
        if self.__is_empty:
            return
        _dlg = QFileDialog(self, localized_label(L_DLG_TITLE_SELECT_EXCLUDES_FILE), self.__config_path)
        _dlg.setOptions(QFileDialog.Option.DontUseNativeDialog)
        _dlg.setFilter(QDir.Filter.AllDirs | QDir.Filter.Hidden)
        _dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        _dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        if _dlg.exec():
            self.__data[CFG_PAR_EXCLUDES] = _dlg.selectedFiles()[0]
        _dlg.close()


class CredentialsPane(QGroupBox):
    """
    Pane für die Zugriffsdaten.
    """
    def __init__(self, parent: QWidget, credentials: dict):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param credentials: aktuell konfigurierte Zugriffsdaten
        """
        super().__init__(localized_label(L_CREDENTIALS), parent)
        self.__credentials = credentials
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QHBoxLayout()
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__credentials_combo = _create_config_group_combo(_layout, L_CREDENTIALS, T_CFG_CREDENTIALS, credentials,
                                                              self._credential_selected)
        self.__detail_pane = CredentialsDetailPane(self)
        _layout.addWidget(self.__detail_pane)
        self.setLayout(_layout)

    def _credential_selected(self, _index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Zugriffsdaten ausgewählt hat.
        """
        self.__detail_pane.set_data(self.__credentials_combo.currentData(Qt.ItemDataRole.UserRole))


class ScopePane(QGroupBox):
    """
    Pane für die Backup-Umfänge.
    """
    def __init__(self, parent: QWidget, config_path: str, scopes: dict):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param config_path: Pfad zur lokalen restix-Konfiguration
        :param scopes: aktuell konfigurierte Backup-Umfänge
        """
        super().__init__(localized_label(L_SCOPES), parent)
        self.__scopes = scopes
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QHBoxLayout()
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__scope_combo = _create_config_group_combo(_layout, L_SCOPE, T_CFG_SCOPE, scopes,
                                                              self._scope_selected)
        self.__detail_pane = ScopeDetailPane(self, config_path)
        _layout.addWidget(self.__detail_pane)
        self.setLayout(_layout)

    def _scope_selected(self, _index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Backup-Umfänge ausgewählt hat.
        """
        self.__detail_pane.set_data(self.__scope_combo.currentData(Qt.ItemDataRole.UserRole))


class ConfigurationPane(QWidget):
    """
    Pane für den Backup.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: die zentrale restix Pane
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__(parent)
        self.__local_config = local_config
        _layout = QVBoxLayout(self)
        # Group für die Zugriffsdaten
        _layout.addWidget(CredentialsPane(self, local_config.credentials()))
        # Group für die Backup-Umfänge
        _layout.addWidget(ScopePane(self, local_config.path(), local_config.scopes()))
        # Group für die Backup-Ziele
        self.setLayout(_layout)

def _create_config_group_combo(parent_layout: QHBoxLayout, caption_id: str, tooltip_id: str, data: dict,
                               selection_handler: Callable) -> QComboBox:
    """

    :return:
    """
    _layout = QHBoxLayout()
    _tooltip = localized_label(tooltip_id)
    _layout.addWidget(option_label(caption_id, _tooltip))
    _combo_box = QComboBox()
    _combo_box.setMinimumWidth(240)
    _combo_box.setToolTip(_tooltip)
    for _name, _credential_data in sorted(data.items()):
        _combo_box.addItem(_name, _credential_data)
    _combo_box.setCurrentIndex(-1)
    _combo_box.currentIndexChanged.connect(selection_handler)
    _layout.addWidget(_combo_box)
    parent_layout.addLayout(_layout)
    return _combo_box
