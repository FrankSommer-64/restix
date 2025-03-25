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


from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QWidget, QGridLayout, QGroupBox, QSizePolicy

from restix.core import *
from restix.core.action import RestixAction
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.gui.panes import ResticActionPane, create_checkbox, GROUP_BOX_STYLE
from restix.gui.settings import GuiSettings
from restix.gui.worker import Worker


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
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__auto_create_option = create_checkbox(_layout, L_AUTO_CREATE, T_OPT_BAK_AUTO_CREATE, True)
        self.__auto_tag_option = create_checkbox(_layout, L_AUTO_TAG, T_OPT_BAK_AUTO_TAG, True)
        self.__dry_run_option = create_checkbox(_layout, L_DRY_RUN, T_OPT_BAK_DRY_RUN, False)
        self.setLayout(_layout)

    def selected_options(self) -> dict:
        """
        :returns: Status der unterstützten Backup-Optionen (auto-create, auto-tag und dry-run)
        """
        return {OPTION_AUTO_CREATE: self.__auto_create_option.isChecked(),
                OPTION_AUTO_TAG: self.__auto_tag_option.isChecked(),
                OPTION_DRY_RUN: self.__dry_run_option.isChecked()}


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
        super().__init__(parent, [L_DO_BACKUP], [T_DO_BAK_BACKUP], [self.start_button_clicked],
                         local_config, gui_settings)
        self.__worker = None
        # option pane
        self.__options_pane = BackupOptionsPane(self)
        self.pane_layout.addWidget(self.__options_pane, 0, 1)
        self.setLayout(self.pane_layout)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

    def start_button_clicked(self):
        """
        Wird aufgerufen, wenn der 'Start Backup'-Button geklickt wurde.
        """
        super().start_button_clicked()
        _options = self.__options_pane.selected_options()
        _backup_action = RestixAction.for_action_id(ACTION_BACKUP, self.selected_target[CFG_PAR_ALIAS],
                                                    self.restix_config, _options)
        self.__worker = Worker.for_action(_backup_action)
        self.__worker.connect_signals(self.handle_progress, self.handle_finish, self.handle_result, self.handle_error)
        QThreadPool.globalInstance().start(self.__worker)

    def cancel_button_clicked(self):
        """
        Wird aufgerufen, wenn der 'Cancel'-Button geklickt wurde.
        """
        super().cancel_button_clicked()
        if self.__worker is not None:
            self.__worker.abort()
