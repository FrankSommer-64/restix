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
Zentraler Arbeitsbereich der restix GUI.
"""

from copy import deepcopy

import os.path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import (QApplication, QDialog, QMenu, QMessageBox, QSizePolicy,
                               QVBoxLayout, QWidget)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.gui import *
from restix.gui.backup_pane import BackupPane
from restix.gui.configuration_pane import ConfigurationPane
from restix.gui.dialogs import AboutDialog, PdfViewerDialog, SaveConfigDialog
from restix.gui.maintenance_pane import MaintenancePane
from restix.gui.model import ConfigModelFactory
from restix.gui.panes import ActionSelectionPane
from restix.gui.restore_pane import RestorePane
from restix.gui.settings import GuiSettings


class CentralPane(QWidget):
    """
    Arbeitsbereich der restix GUI.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: Hauptfenster
        :param local_config: lokale restix-Konfiguration
        :param gui_settings: GUI-Einstellungen des Benutzers
        """
        super().__init__(parent)
        self.__config = local_config
        self.__original_config = deepcopy(local_config)
        self.__gui_settings = gui_settings
        self.__model_factory = ConfigModelFactory(local_config)
        self.__layout = QVBoxLayout(self)
        self.__layout.setSpacing(DEFAULT_SPACING)
        self.__layout.setContentsMargins(SMALL_CONTENT_MARGIN, SMALL_CONTENT_MARGIN,
                                         SMALL_CONTENT_MARGIN, SMALL_CONTENT_MARGIN)
        _actions = ((BUTTON_ICON_BACKUP, L_BACKUP, self._backup_selected, False),
                    (BUTTON_ICON_RESTORE, L_RESTORE, self._restore_selected, False),
                    (BUTTON_ICON_MAINTENANCE, L_MAINTENANCE, self._maintenance_selected, False),
                    (BUTTON_ICON_CONFIGURATION, L_CONFIGURATION, self._config_selected, False),
                    (BUTTON_ICON_INFO, L_INFO, self._info_selected, True),
                    (BUTTON_ICON_EXIT, L_EXIT, QApplication.instance().quit, False))
        self.__action_selection_pane = ActionSelectionPane(self, _actions)
        self.__layout.addWidget(self.__action_selection_pane)
        _welcome_pane = QWidget(self)
        _welcome_pane.setStyleSheet(_WELCOME_PANE_STYLE)
        _welcome_pane.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.__layout.addWidget(_welcome_pane)
        self.__work_pane = _welcome_pane

    def save_config(self):
        """
        Speichert die lokale restix-Konfiguration, falls sie geändert wurde.
        """
        if self.__original_config != self.__config:
            _dlg = SaveConfigDialog(self)
            if _dlg.exec() == QDialog.DialogCode.Accepted:
                try:
                    self.__config.to_file(_dlg.save_as_file_path())
                except RestixException as _e:
                    QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR), str(_e),
                                         QMessageBox.StandardButton.Ok)
                    return
                self.__original_config = deepcopy(self.__config)
            else:
                self.__config = deepcopy(self.__original_config)

    def _backup_selected(self):
        """
        Zeigt die GUI-Bereiche für Backup an.
        """
        self.save_config()
        self._activate_pane(BackupPane(self, self.__config, self.__gui_settings), L_BACKUP)

    def _restore_selected(self):
        """
        Zeigt die GUI-Bereiche für Restore an.
        """
        self.save_config()
        self._activate_pane(RestorePane(self, self.__config, self.__gui_settings), L_RESTORE)

    def _maintenance_selected(self):
        """
        Zeigt die GUI-Bereiche für Wartung an.
        """
        self.save_config()
        self._activate_pane(MaintenancePane(self, self.__config, self.__gui_settings), L_MAINTENANCE)

    def _config_selected(self):
        """
        Zeigt die GUI-Bereiche für Konfiguration an.
        """
        self._activate_pane(ConfigurationPane(self, self.__model_factory), L_CONFIGURATION)

    def _info_selected(self, mouse_x: int, mouse_y: int):
        """
        Zeigt das Info-Menü an.
        :param mouse_x: X-Position des Mausklicks
        :param mouse_y: Y-Position des Mausklicks
        """
        self.save_config()
        _context_menu = QMenu(self)
        _context_menu.setStyleSheet(INFO_CONTEXT_MENU_STYLE)
        _context_menu.setContentsMargins(DEFAULT_CONTENT_MARGIN, DEFAULT_CONTENT_MARGIN,
                                         DEFAULT_CONTENT_MARGIN, DEFAULT_CONTENT_MARGIN)
        _context_menu.addAction(localized_label(L_MENU_USER_MANUAL)).triggered.connect(self._show_manual)
        _context_menu.addSeparator()
        _context_menu.addAction(localized_label(L_MENU_ABOUT)).triggered.connect(self._show_about)
        _context_menu.exec(QPoint(mouse_x, mouse_y))

    def _activate_pane(self, pane: QWidget, button_label_id: str):
        """
        Zeigt die übergebene Pane als Work-Pane an.
        :param pane: neue Work-Pane
        :param button_label_id: Resource-ID des zur Pane gehörenden Image-Buttons
        """
        self.__work_pane.hide()
        pane.show()
        self.__layout.replaceWidget(self.__work_pane, pane)
        self.update()
        self.__work_pane = pane
        self.__action_selection_pane.action_selected(button_label_id)

    def _show_manual(self):
        """
        Zeigt das restix-Benutzerhandbuch an.
        """
        _locale = platform_locale()
        _cur_dir = str(os.path.dirname(__file__))
        _assets_path = os.path.join(_cur_dir, RESTIX_ASSETS_DIR)
        _manual_file_path = os.path.join(_assets_path, f'{USER_MANUAL_STEM}{_locale}.pdf')
        if not os.path.isfile(_manual_file_path):
            _manual_file_path = os.path.join(_assets_path, f'{USER_MANUAL_STEM}en.pdf')
        _dlg = PdfViewerDialog(self, L_DLG_TITLE_USER_MANUAL, _manual_file_path)
        _dlg.exec()

    def _show_about(self):
        """
        Zeigt ein Dialogfenster mit Informationen über die restix-Applikation an.
        """
        _about_dlg = AboutDialog(self)
        _about_dlg.exec()


_WELCOME_PANE_STYLE = f'border-image: url({RESTIX_ASSETS_DIR}:restix_background.jpg)'
