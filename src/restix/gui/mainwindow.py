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
Hauptfenster der restix GUI.
"""

from copy import deepcopy

from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox

from restix.core.action import ResticVersion
from restix.core.restic_interface import determine_version
from restix.core.restix_exception import RestixException
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.gui import SMALL_CONTENT_MARGIN, MIN_MAIN_WIN_HEIGHT, MIN_MAIN_WIN_WIDTH
from restix.gui.central_pane import CentralPane
from restix.gui.dialogs import SaveConfigDialog
from restix.gui.settings import GuiSettings


class MainWindow(QMainWindow):
    """
    Hauptfenster der restix GUI.
    """
    def __init__(self, local_config: LocalConfig):
        """
        Konstruktor.
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__()
        self.__config = local_config
        self.__original_config = deepcopy(local_config)
        self.__settings = GuiSettings.from_file()
        self.setMinimumSize(MIN_MAIN_WIN_WIDTH, MIN_MAIN_WIN_HEIGHT)
        self.setGeometry(self.__settings.win_geometry())
        self.setWindowTitle(localized_label(L_MAIN_WIN_TITLE))
        self.setCentralWidget(CentralPane(self, local_config, self.__settings))
        self.layout().setContentsMargins(SMALL_CONTENT_MARGIN, SMALL_CONTENT_MARGIN,
                                         SMALL_CONTENT_MARGIN, SMALL_CONTENT_MARGIN)
        self.layout().update()
        try:
            _restic_version = ResticVersion.from_version_command(determine_version(local_config.restic_executable()))
            if not _restic_version.suitable_for_restix():
                QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                    localized_message(E_UNSUPPORTED_RESTIC_VERSION, _restic_version.version()),
                                    QMessageBox.StandardButton.Ok)
                self.close()
        except RestixException as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
            self.close()

    def save_settings(self):
        """
        Speichert die lokale restix-Konfiguration und die GUI-Einstellungen in einer Datei.
        """
        if self.__original_config != self.__config:
            _dlg = SaveConfigDialog(self)
            if _dlg.exec() == QDialog.DialogCode.Accepted:
                try:
                    self.__config.to_file(_dlg.save_as_file_path())
                except RestixException as _e:
                    QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e),
                                         QMessageBox.StandardButton.Ok)
        self.__settings.set_win_geometry(self.rect())
        try:
            self.__settings.save()
        except RestixException as _e:
            QMessageBox.warning(self, localized_label(L_MBOX_TITLE_WARNING), str(_e), QMessageBox.StandardButton.Ok)
