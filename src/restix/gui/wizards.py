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

from PySide6.QtWidgets import (QDialog, QLabel,
                               QMessageBox, QPushButton, QSizePolicy, QStyle, QTextEdit,
                               QVBoxLayout, QWidget, QCheckBox,
                               QWizard, QWizardPage)

from restix.core import *
from restix.core.config import create_default_config
from restix.core.messages import *


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
        layout = QVBoxLayout()
        layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_DEFAULT), wordWrap=True))
        layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_USER), wordWrap=True))
        layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_CANCEL), wordWrap=True))
        self.setLayout(layout)


class CreateConfigWizardTargetPage(QWizardPage):
    """
    Zweite Seite des Konfigurations-Assistenten.
    Auswahl des Sicherungsziels.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_2))
        layout = QVBoxLayout()
        layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_DEFAULT), wordWrap=True))
        layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_USER), wordWrap=True))
        layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_CANCEL), wordWrap=True))
        self.setLayout(layout)


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
