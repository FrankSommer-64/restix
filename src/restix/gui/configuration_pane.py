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

from PySide6.QtCore import Qt, QDir, Signal
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QComboBox, QFormLayout,
                               QLabel, QLineEdit, QSizePolicy, QPushButton, QFileDialog, QScrollArea, QTextEdit)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.gui import EDITOR_STYLE, TEXT_FIELD_STYLE
from restix.gui.panes import GROUP_BOX_STYLE, option_label




class ClickButton(QPushButton):
    """
    Push-Button mit unterschiedlichen Handlern für Links- und Rechts-Klicks.
    """
    right_clicked = Signal()

    def __init__(self):
        """
        Konstruktor
        """
        super().__init__()

    def mouseReleaseEvent(self, e, /):
        if e.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
            return
        super().mouseReleaseEvent(e)


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
        self.__filename_text = None
        self.__password_text = None
        self.setLayout(self.__layout)

    def set_data(self, credential_data: dict):
        """
        Überträgt die Zugriffsdaten in die GUI widgets.
        :param credential_data: Zugriffsdaten
        """
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
                self.__layout.removeRow(2)
                self.__password_text = None
            if self.__filename_text is None:
                self.__filename_text = QLineEdit()
                self.__filename_text.setStyleSheet(TEXT_FIELD_STYLE)
                self.__filename_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
                self.__filename_text.setToolTip(localized_label(T_CFG_CREDENTIAL_FILE_NAME))
                self.__layout.insertRow(2, QLabel(localized_label(L_FILE_NAME)), self.__filename_text)
            self.__filename_text.setText(value)
        elif credential_type == CFG_VALUE_CREDENTIALS_TYPE_TEXT:
            if self.__filename_text is not None:
                self.__layout.removeRow(2)
                self.__filename_text = None
            if self.__password_text is None:
                self.__password_text = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
                self.__password_text.setStyleSheet(TEXT_FIELD_STYLE)
                self.__password_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
                self.__password_text.setToolTip(localized_label(T_CFG_CREDENTIAL_PASSWORD))
                self.__layout.insertRow(2, QLabel(localized_label(L_PASSWORD)), self.__password_text)
            self.__password_text.setText(value)
        else:
            if self.__filename_text is not None or self.__password_text is not None:
                self.__layout.removeRow(2)
            self.__filename_text = None
            self.__password_text = None


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
        self.__credentials_combo = _create_config_group_combo(_layout, L_NAME, T_CFG_CREDENTIALS, credentials,
                                                              self._credential_selected)
        self.__detail_pane = CredentialsDetailPane(self)
        _layout.addWidget(self.__detail_pane)
        self.setLayout(_layout)

    def _credential_selected(self, _index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Zugriffsdaten ausgewählt hat.
        """
        self.__detail_pane.set_data(self.__credentials_combo.currentData(Qt.ItemDataRole.UserRole))


class ScopeDetailPane(QWidget):
    """
    Pane zum Anzeigen und Editieren von Backup-Umfängen.
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
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(localized_label(T_CFG_SCOPE_COMMENT))
        self.__layout.addRow(QLabel(localized_label(L_COMMENT)), self.__comment_text)
        self.__includes_button = QPushButton(localized_label(L_EDIT))
        self.__includes_button.setToolTip(localized_label(T_CFG_SCOPE_FILES_N_DIRS))
        self.__includes_button.clicked.connect(self._edit_files_n_dirs)
        self.__layout.addRow(QLabel(localized_label(L_FILES_N_DIRS)), self.__includes_button)
        self.__ignores_list = QTextEdit()
        self.__ignores_list.setStyleSheet(EDITOR_STYLE)
        self.__ignores_list.setMinimumHeight(60)
        self.__ignores_list.setMaximumHeight(100)
        self.__ignores_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__layout.addRow(QLabel(localized_label(L_IGNORES)), self.__ignores_list)
        self.setLayout(self.__layout)

    def set_data(self, scope_data: dict):
        """
        Überträgt die Daten eines Backup-Umfangs in die GUI widgets.
        :param scope_data: Backup-Umfang
        """
        self.__orig_data = scope_data
        self.__data = scope_data.copy()
        self.__is_empty = False
        self.__comment_text.setText(scope_data[CFG_PAR_COMMENT])
        self.__ignores_list.clear()
        _ignores = scope_data.get(CFG_PAR_IGNORES)
        if _ignores is not None:
            for _ignore_pattern in _ignores:
                self.__ignores_list.append(_ignore_pattern)

    def _edit_files_n_dirs(self):
        print('_edit_files_n_dirs')


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
        self.__scope_combo = _create_config_group_combo(_layout, L_NAME, T_CFG_SCOPE, scopes,
                                                              self._scope_selected)
        self.__detail_pane = ScopeDetailPane(self, config_path)
        _layout.addWidget(self.__detail_pane)
        self.setLayout(_layout)

    def _scope_selected(self, _index: int):
        """
        Wird aufgerufen, wenn der Benutzer einen Eintrag der Backup-Umfänge ausgewählt hat.
        """
        self.__detail_pane.set_data(self.__scope_combo.currentData(Qt.ItemDataRole.UserRole))


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
        self.__targets_combo = _create_config_group_combo(_layout, L_ALIAS, T_CFG_TARGET, self.__targets,
                                                          self._target_selected)
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
        _pane_layout = QVBoxLayout(self)
        _scroll_pane = QScrollArea(self)
        _scroll_pane_layout = QVBoxLayout(_scroll_pane)
        # Group für die Zugriffsdaten
        _scroll_pane_layout.addWidget(CredentialsPane(self, local_config.credentials()))
        # Group für die Backup-Umfänge
        _scroll_pane_layout.addWidget(ScopePane(self, local_config.path(), local_config.scopes()))
        # Group für die Backup-Ziele
        _scroll_pane_layout.addWidget(TargetPane(self, local_config))
        _pane_layout.addWidget(_scroll_pane)

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
