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
Assistenten für die restix GUI.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy,
                               QStyle, QVBoxLayout, QWizard, QWizardPage, QFormLayout, QGridLayout,
                               QFileDialog)

from restix.core import *
from restix.core.config import create_default_config
from restix.core.messages import *
from restix.gui import *


class CreateConfigWizardStartPage(QWizardPage):
    """
    Erste Seite des Assistenten für die restix-Konfiguration.
    Fragt ab, ob eine Default-Konfiguration oder eine benutzerdefinierte Konfiguration erzeugt werden soll.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_1))
        self.setFinalPage(True)
        _layout = QVBoxLayout()
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_DEFAULT), wordWrap=True))
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_USER), wordWrap=True))
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_CANCEL), wordWrap=True))
        self.setLayout(_layout)


class CreateConfigWizardTargetPage(QWizardPage):
    """
    Zweite Seite des Assistenten für die restix-Konfiguration.
    Festlegen des Sicherungsziels.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_2))
        _layout = QGridLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN,
                                   WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # oberer Teil Name und Beschreibung
        _desc_info = QLabel(localized_label(T_WIZ_TARGET_DESC_INFO), wordWrap=True)
        _desc_info.setStyleSheet(CAPTION_STYLE)
        _layout.addWidget(_desc_info, 0, 0, 1, 2)
        _alias_label, _alias_text = _text_input(L_ALIAS, r'[\p{L}0-9._-]+')
        _layout.addWidget(_alias_label, 1, 0)
        _layout.addWidget(_alias_text, 1, 1)
        _comment_label, _comment_text = _text_input(L_COMMENT)
        _layout.addWidget(_comment_label, 2, 0)
        _layout.addWidget(_comment_text, 2, 1)
        # unterer Teil Ort
        _location_info = QLabel(localized_label(T_WIZ_TARGET_LOCATION_INFO), wordWrap=True)
        _location_info.setStyleSheet(CAPTION_STYLE)
        _layout.addWidget(_location_info, 3, 0, 1, 2)
        self.__location_button = QPushButton(localized_label(L_LOCAL_TARGET))
        self.__location_button.clicked.connect(self._select_local_target)
        _layout.addWidget(self.__location_button, 4, 0)
        self.__location_text = QLineEdit()
        self.__location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        _layout.addWidget(self.__location_text, 4, 1)
        self.registerField(f'{_FIELD_TARGET_ALIAS}*', _alias_text)
        self.registerField(_FIELD_TARGET_COMMENT, _comment_text)
        self.registerField(f'{_FIELD_TARGET_LOCATION}*', self.__location_text)

    def _select_local_target(self):
        """
        Wird aufgerufen, wenn der Button zur Auswahl eines lokalen Ziels aufgerufen wird.
        """
        _dir = QFileDialog.getExistingDirectory(self, localized_label(L_SELECT))
        if len(_dir) > 0:
            self.__location_text.setText(_dir)


class CreateConfigWizardCredentialsPage(QWizardPage):
    """
    Dritte Seite des Assistenten für die restix-Konfiguration.
    Festlegen der Zugangsdaten.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_3))
        # TODO GridLayout
        _layout = QFormLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _tooltip = localized_label(T_CFG_TARGET_ALIAS)
        _alias_label = QLabel(localized_label(L_ALIAS))
        _alias_label.setToolTip(_tooltip)
        self.__alias_text = QLineEdit()
        self.__alias_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__alias_text.setToolTip(_tooltip)
        _layout.addRow(_alias_label, self.__alias_text)
        _tooltip = localized_label(T_CFG_TARGET_COMMENT)
        _comment_label = QLabel(localized_label(L_COMMENT))
        _comment_label.setToolTip(_tooltip)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(_tooltip)
        _layout.addRow(_comment_label, self.__comment_text)
        # TODO Button für Verzeichnis-Auswahl
        _tooltip = localized_label(T_CFG_TARGET_LOCATION)
        _location_label = QLabel(localized_label(L_LOCATION))
        _location_label.setToolTip(_tooltip)
        self.__location_text = QLineEdit()
        self.__location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__location_text.setToolTip(_tooltip)
        _layout.addRow(_location_label, self.__location_text)
        self.setLayout(_layout)


class CreateConfigWizardScopePage(QWizardPage):
    """
    Vierte Seite des Assistenten für die restix-Konfiguration.
    Festlegen des Sicherungsumfangs.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_4))
        # TODO GridLayout
        _layout = QFormLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _tooltip = localized_label(T_CFG_TARGET_ALIAS)
        _alias_label = QLabel(localized_label(L_ALIAS))
        _alias_label.setToolTip(_tooltip)
        self.__alias_text = QLineEdit()
        self.__alias_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__alias_text.setToolTip(_tooltip)
        _layout.addRow(_alias_label, self.__alias_text)
        _tooltip = localized_label(T_CFG_TARGET_COMMENT)
        _comment_label = QLabel(localized_label(L_COMMENT))
        _comment_label.setToolTip(_tooltip)
        self.__comment_text = QLineEdit()
        self.__comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__comment_text.setToolTip(_tooltip)
        _layout.addRow(_comment_label, self.__comment_text)
        # TODO Button für Verzeichnis-Auswahl
        _tooltip = localized_label(T_CFG_TARGET_LOCATION)
        _location_label = QLabel(localized_label(L_LOCATION))
        _location_label.setToolTip(_tooltip)
        self.__location_text = QLineEdit()
        self.__location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.__location_text.setToolTip(_tooltip)
        _layout.addRow(_location_label, self.__location_text)


class CreateConfigWizard(QWizard):
    """
    Assistent zum Anlegen der initialen restix-Konfiguration.
    :param config_root_path: Verzeichnis, in der die restix Konfiguration angelegt werden soll.
    """
    def __init__(self, config_root_path: str):
        """
        Konstruktor.
        """
        super().__init__()
        self.default_config_requested = True
        self.setWindowTitle(localized_label(L_WIZ_TITLE_CREATE_CONFIG))
        self.setButtonText(QWizard.WizardButton.BackButton, localized_label(L_WIZ_BUTTON_BACK))
        self.setButtonText(QWizard.WizardButton.CancelButton, localized_label(L_WIZ_BUTTON_CANCEL))
        self.setButtonText(QWizard.WizardButton.NextButton, localized_label(L_WIZ_BUTTON_NEXT))
        self.setButtonText(QWizard.WizardButton.FinishButton, localized_label(L_WIZ_BUTTON_FINISH))
        self.addPage(CreateConfigWizardStartPage())
        self.__target_page = CreateConfigWizardTargetPage()
        self.addPage(self.__target_page)
        self.addPage(CreateConfigWizardCredentialsPage())
        self.addPage(CreateConfigWizardScopePage())
        self.currentIdChanged.connect(self.page_changed)

    def page_changed(self, page_id):
        """
        Wird aufgerufen, wenn eine andere Seite des Assistenten aufgerufen wird
        """
        self.default_config_requested = self.default_config_requested and page_id <= 0

    def fields(self) -> dict:
        """
        :return: vom Benutzer eingegebene Werte
        """
        _fields = {}
        if not self.default_config_requested:
            _fields[_FIELD_TARGET_ALIAS] = self.__target_page.field(_FIELD_TARGET_ALIAS)
            _fields[_FIELD_TARGET_COMMENT] = self.__target_page.field(_FIELD_TARGET_COMMENT)
            _fields[_FIELD_TARGET_LOCATION] = self.__target_page.field(_FIELD_TARGET_LOCATION)
        return _fields


def run_config_wizard(config_root_path: str):
    """
    Startet den Assistenten zum Anlegen einer restix-Konfiguration.
    :param config_root_path: Verzeichnis, in der die restix Konfiguration angelegt werden soll.
    :raises RestixException: falls der Assistent abgebrochen wird oder die Konfiguration nicht
    erzeugt werden kann
    """
    _wizard = CreateConfigWizard(config_root_path)
    if _wizard.exec() == QDialog.DialogCode.Accepted:
        print(_wizard.fields())
        if _wizard.default_config_requested:
            create_default_config(config_root_path)
            QMessageBox.information(None, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_COMPLETE_CONFIG_LATER),
                                    QMessageBox.StandardButton.Ok)
    else:
        print(_wizard.fields())
        print('Abbruch')

def _text_input(label_id, allowed_chars=None) -> tuple[QLabel, QLineEdit]:
    _label = QLabel(localized_label(label_id))
    _text = QLineEdit()
    _text.setStyleSheet(TEXT_FIELD_STYLE)
    _text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    if allowed_chars is not None:
        _text.setValidator(QRegularExpressionValidator(allowed_chars))
    return _label, _text


_FIELD_TARGET_ALIAS = 'target.alias'
_FIELD_TARGET_COMMENT = 'target.comment'
_FIELD_TARGET_LOCATION = 'target.location'
