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

import os.path

from PySide6.QtCore import QSize, Qt, Signal, QObject, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout,
                               QPushButton, QLabel, QHBoxLayout, QSizePolicy, QMenu)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.restix_exception import RestixException
from restix.core.messages import *
from restix.gui.panes import ActionSelectionPane
from restix.gui.dialogs import (AboutDialog, PdfViewerDialog)
from restix.gui.settings import GuiSettings


class CentralPane(QWidget):
    """
    Arbeitsbereich der restix GUI.
    """
    def __init__(self, parent: QWidget, config_path: str, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: das Hauptfenster
        :param config_path: restix-Konfigurationsverzeichnis
        :param local_config: lokale restix-Konfiguration
        :param gui_settings: die personalisierten GUI-Einstellungen
        """
        super().__init__(parent)
        self._local_config = local_config
        _layout = QVBoxLayout()
        _layout.setSpacing(10)
        _layout.setContentsMargins(5, 5, 5, 5)
        _actions = (('backup_icon.png', L_BACKUP, self._backup_selected, False),
                    ('restore_icon.png', L_RESTORE, self._restore_selected, False),
                    ('configuration_icon.png', L_CONFIGURATION, self._config_selected, False),
                    ('maintenance_icon.png', L_MAINTENANCE, self._maintenance_selected, False),
                    ('help_icon.png', L_HELP, self._help_selected, True),
                    ('exit_icon.png', L_EXIT, QApplication.instance().quit, False))
        _layout.addWidget(ActionSelectionPane(self, _actions))
        _welcome_pane = QWidget(self)
        _welcome_pane.setStyleSheet(_WELCOME_PANE_STYLE)
        _welcome_pane.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        _layout.addWidget(_welcome_pane)
        self.setLayout(_layout)

    def _backup_selected(self):
        """
        Zeigt das Hilfe-Menü an.
        :param mouse_x: X-Position des Mausklicks
        :param mouse_y: Y-Position des Mausklicks
        """
        print('_backup_selected')

    def _restore_selected(self):
        print('_restore_selected')

    def _config_selected(self):
        print('_config_selected')

    def _maintenance_selected(self):
        print('_maintenance_selected')

    def _help_selected(self, mouse_x: int, mouse_y: int):
        """
        Zeigt das Hilfe-Menü an.
        :param mouse_x: X-Position des Mausklicks
        :param mouse_y: Y-Position des Mausklicks
        """
        _context_menu = QMenu(self)
        _context_menu.addAction(localized_label(L_MENU_USER_MANUAL)).triggered.connect(self._show_manual)
        _context_menu.addAction(localized_label(L_MENU_ABOUT)).triggered.connect(self._show_about)
        _context_menu.exec(QPoint(mouse_x, mouse_y))

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


_WELCOME_PANE_STYLE = f'border-image: url({RESTIX_ASSETS_DIR}:restix-aq.jpg)'
