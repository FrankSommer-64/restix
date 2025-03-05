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
GUI-Bereich für den Backup.
"""


from PySide6.QtCore import QSize, Qt, Signal, QObject, QAbstractTableModel
from PySide6.QtGui import QMouseEvent, QBrush
from PySide6.QtWidgets import (QWidget, QVBoxLayout,
                               QPushButton, QLabel, QHBoxLayout, QSizePolicy, QGridLayout, QListWidget,
                               QListWidgetItem, QGroupBox, QTableView, QAbstractItemView, QFormLayout)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.restix_exception import RestixException
from restix.core.messages import *
from restix.gui.panes import ResticActionPane, create_option, GROUP_BOX_STYLE
from restix.gui.settings import GuiSettings


class BackupOptionsPane(QGroupBox):
    """
    Pane für die Backup-Optionen.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        """
        super().__init__(localized_label(L_OPTIONS), parent)
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QGridLayout()
        _layout.setColumnStretch(3, 1)
        self.__auto_tag_option = create_option(_layout, L_AUTO_TAG, T_OPT_BAK_AUTO_TAG, False)
        self.__dry_run_option = create_option(_layout, L_DRY_RUN, T_OPT_BAK_DRY_RUN, False)
        self.setLayout(_layout)


class BackupPane(ResticActionPane):
    """
    Pane für den Backup.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: die zentrale restix Pane
        :param local_config: lokale restix-Konfiguration
        :param gui_settings: die GUI-Einstellungen des Benutzers
        """
        super().__init__(parent, local_config, gui_settings)
        # option pane
        self.pane_layout.addWidget(BackupOptionsPane(self), 0, 1)
        # action button pane
        self.pane_layout.addWidget(QWidget(self), 1, 0, 1, -1)
        self.setLayout(self.pane_layout)

