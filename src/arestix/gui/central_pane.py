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
Zentraler Arbeitsbereich der arestix GUI.
"""

import os.path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSizePolicy, QMenu

from arestix.core import *
from arestix.core.config import LocalConfig
from arestix.core.messages import *
from arestix.gui import *
from arestix.gui.backup_pane import BackupPane
from arestix.gui.configuration_pane import ConfigurationPane
from arestix.gui.maintenance_pane import MaintenancePane
from arestix.gui.model import ConfigModelFactory
from arestix.gui.panes import ActionSelectionPane
from arestix.gui.dialogs import AboutDialog, PdfViewerDialog
from arestix.gui.restore_pane import RestorePane
from arestix.gui.settings import GuiSettings


class CentralPane(QWidget):
    """
    Arbeitsbereich der arestix GUI.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: das Hauptfenster
        :param local_config: lokale arestix-Konfiguration
        :param gui_settings: die personalisierten GUI-Einstellungen
        """
        super().__init__(parent)
        self._local_config = local_config
        self._gui_settings = gui_settings
        self.__model_factory = ConfigModelFactory(local_config)
        self._layout = QVBoxLayout()
        self._layout.setSpacing(10)
        self._layout.setContentsMargins(5, 5, 5, 5)
        _actions = ((BUTTON_ICON_BACKUP, L_BACKUP, self._backup_selected, False),
                    (BUTTON_ICON_RESTORE, L_RESTORE, self._restore_selected, False),
                    (BUTTON_ICON_MAINTENANCE, L_MAINTENANCE, self._maintenance_selected, False),
                    (BUTTON_ICON_CONFIGURATION, L_CONFIGURATION, self._config_selected, False),
                    (BUTTON_ICON_INFO, L_INFO, self._info_selected, True),
                    (BUTTON_ICON_EXIT, L_EXIT, QApplication.instance().quit, False))
        self._layout.addWidget(ActionSelectionPane(self, _actions))
        _welcome_pane = QWidget(self)
        _welcome_pane.setStyleSheet(_WELCOME_PANE_STYLE)
        _welcome_pane.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self._layout.addWidget(_welcome_pane)
        self._work_pane = _welcome_pane
        self.setStyleSheet(_STANDARD_PANE_STYLE)
        self.setLayout(self._layout)

    def _backup_selected(self):
        """
        Zeigt die GUI-Bereiche für Backup an.
        """
        self._activate_pane(BackupPane(self, self._local_config, self._gui_settings))

    def _restore_selected(self):
        """
        Zeigt die GUI-Bereiche für Restore an.
        """
        self._activate_pane(RestorePane(self, self._local_config, self._gui_settings))

    def _maintenance_selected(self):
        """
        Zeigt die GUI-Bereiche für Wartung an.
        """
        self._activate_pane(MaintenancePane(self, self._local_config, self._gui_settings))

    def _config_selected(self):
        """
        Zeigt die GUI-Bereiche für Konfiguration an.
        """
        self._activate_pane(ConfigurationPane(self, self.__model_factory))

    def _info_selected(self, mouse_x: int, mouse_y: int):
        """
        Zeigt das Info-Menü an.
        :param mouse_x: X-Position des Mausklicks
        :param mouse_y: Y-Position des Mausklicks
        """
        _context_menu = QMenu(self)
        _context_menu.addAction(localized_label(L_MENU_USER_MANUAL)).triggered.connect(self._show_manual)
        _context_menu.addAction(localized_label(L_MENU_ABOUT)).triggered.connect(self._show_about)
        _context_menu.exec(QPoint(mouse_x, mouse_y))

    def _activate_pane(self, pane: QWidget):
        """
        Zeigt die übergebene Pane als Work-Pane an.
        :param pane: die neue Work-Pane
        """
        self._work_pane.hide()
        pane.show()
        self._layout.replaceWidget(self._work_pane, pane)
        self.update()
        self._work_pane = pane

    def _show_manual(self):
        """
        Zeigt das arestix-Benutzerhandbuch an.
        """
        _locale = platform_locale()
        _cur_dir = str(os.path.dirname(__file__))
        _assets_path = os.path.join(_cur_dir, ARESTIX_ASSETS_DIR)
        _manual_file_path = os.path.join(_assets_path, f'{USER_MANUAL_STEM}{_locale}.pdf')
        if not os.path.isfile(_manual_file_path):
            _manual_file_path = os.path.join(_assets_path, f'{USER_MANUAL_STEM}en.pdf')
        _dlg = PdfViewerDialog(self, L_DLG_TITLE_USER_MANUAL, _manual_file_path)
        _dlg.exec()

    def _show_about(self):
        """
        Zeigt ein Dialogfenster mit Informationen über die arestix-Applikation an.
        """
        _about_dlg = AboutDialog(self)
        _about_dlg.exec()


_WELCOME_PANE_STYLE = f'border-image: url({ARESTIX_ASSETS_DIR}:arestix.jpg)'
_STANDARD_PANE_STYLE = 'background-color: #eeeeee'
