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
from PySide6.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy,
                               QStyle, QVBoxLayout, QWizard, QWizardPage, QFormLayout, QGridLayout)

from restix.core import *
from restix.core.config import create_default_config
from restix.core.messages import *
from restix.gui import *


class CreateConfigWizardStartPage(QWizardPage):
    """
    Erste Seite des Konfigurations-Assistenten.
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
    Zweite Seite des Konfigurations-Assistenten.
    Festlegen des Sicherungsziels.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_2))
        _layout = QGridLayout(self)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _tooltip = localized_label(T_CFG_TARGET_ALIAS)
        _alias_label = QLabel(localized_label(L_ALIAS))
        _alias_label.setToolTip(_tooltip)
        _layout.addWidget(_alias_label, 0, 0)
        self.alias_text = QLineEdit()
        self.alias_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.alias_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.alias_text.setToolTip(_tooltip)
        _layout.addWidget(self.alias_text, 0, 1)
        _tooltip = localized_label(T_CFG_TARGET_COMMENT)
        _comment_label = QLabel(localized_label(L_COMMENT))
        _comment_label.setToolTip(_tooltip)
        _layout.addWidget(_comment_label, 1, 0)
        self.comment_text = QLineEdit()
        self.comment_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.comment_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.comment_text.setToolTip(_tooltip)
        _layout.addWidget(self.comment_text, 1, 1)
        # TODO Button für Verzeichnis-Auswahl
        _tooltip = localized_label(T_CFG_TARGET_LOCATION)
        _location_label = QLabel(localized_label(L_LOCATION))
        _location_label.setToolTip(_tooltip)
        _layout.addWidget(_location_label, 2, 0)
        self.location_text = QLineEdit()
        self.location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.location_text.setToolTip(_tooltip)
        _layout.addWidget(self.location_text, 2, 1)
        self.registerField('target.alias*', self.alias_text)
        self.registerField('target.comment', self.comment_text)


class CreateConfigWizardCredentialsPage(QWizardPage):
    """
    Dritte Seite des Konfigurations-Assistenten.
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
    Vierte Seite des Konfigurations-Assistenten.
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
        self.addPage(CreateConfigWizardTargetPage())
        self.addPage(CreateConfigWizardCredentialsPage())
        self.addPage(CreateConfigWizardScopePage())
        self.currentIdChanged.connect(self.page_changed)

    def page_changed(self, page_id):
        """
        Wird aufgerufen, wenn eine andere Seite des Assistenten aufgerufen wird
        """
        self.default_config_requested = self.default_config_requested and page_id <= 0


def run_config_wizard(config_root_path: str):
    """
    Startet den Assistenten zum Anlegen einer restix-Konfiguration.
    :param config_root_path: Verzeichnis, in der die restix Konfiguration angelegt werden soll.
    :raises RestixException: falls der Assistent abgebrochen wird oder die Konfiguration nicht
    erzeugt werden kann
    """
    _wizard = CreateConfigWizard(config_root_path)
    if _wizard.exec() == QDialog.DialogCode.Accepted:
        if _wizard.default_config_requested:
            create_default_config(config_root_path)
            QMessageBox.information(None, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_COMPLETE_CONFIG_LATER),
                                    QMessageBox.StandardButton.Ok)
    else:
        print('Abbruch')
