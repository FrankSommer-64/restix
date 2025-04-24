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
GUI-Bereich für die Wartung.
"""

import datetime
import platform

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QGridLayout, QGroupBox, QMessageBox, QWidget

from arestix.core import *
from arestix.core.action import ArestixAction
from arestix.core.arestix_exception import ArestixException
from arestix.core.config import LocalConfig
from arestix.core.messages import *
from arestix.gui import GROUP_BOX_STYLE, PAST_YEARS_COUNT, WIDE_CONTENT_MARGIN
from arestix.gui.panes import create_checkbox, create_combo, create_text, ResticActionPane
from arestix.gui.settings import GuiSettings
from arestix.gui.worker import Worker


class MaintenanceOptionsPane(QGroupBox):
    """
    Pane für die Optionen.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        """
        super().__init__(localized_label(L_OPTIONS), parent)
        self.__target_alias = None
        self.__tag_name = None
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QGridLayout(self)
        _layout.setColumnStretch(3, 1)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__host_text = create_text(_layout, L_HOST, T_OPT_MNT_HOST)
        self.__host_text.setText(platform.node())
        _current_year = datetime.datetime.now().year
        self.__year_combo = create_combo(_layout, L_YEAR, T_OPT_MNT_YEAR)
        self.__year_combo.addItems([str(_y) for _y in range(_current_year, _current_year - PAST_YEARS_COUNT, -1)])
        self.__year_combo.setCurrentIndex(0)
        self.__dry_run_option = create_checkbox(_layout, L_DRY_RUN, T_OPT_MNT_DRY_RUN, False)

    def selected_options(self) -> dict:
        """
        :returns: Status der unterstützten Optionen (host, jahr und dry-run)
        """
        _options = {OPTION_YEAR: self.__year_combo.currentText(), OPTION_DRY_RUN: self.__dry_run_option.isChecked()}
        _host = self.__host_text.text()
        if len(_host) > 0:
            _options[OPTION_HOST] = _host
        return _options


class MaintenancePane(ResticActionPane):
    """
    Pane für die Wartung, aktuell nur Jahresabschluss.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: zentrale arestix Pane
        :param local_config: lokale arestix-Konfiguration
        :param gui_settings: die GUI-Einstellungen des Benutzers
        """
        super().__init__(parent, [L_DO_INIT_REPO, L_DO_YEAR_END], [T_DO_MNT_INIT_REPO, T_DO_MNT_YEAR_END],
                         None,
                         [self._init_repo_clicked, self._year_end_clicked], local_config, gui_settings)
        self.__worker = None
        # Optionen
        self.__options_pane = MaintenanceOptionsPane(self)
        self.pane_layout.addWidget(self.__options_pane, 0, 1)
        self.setLayout(self.pane_layout)

    def _init_repo_clicked(self):
        """
        Wird aufgerufen, wenn der 'Repository anlegen'-Button geklickt wurde.
        """
        _ok, _pw = super().start_button_clicked()
        if not _ok:
            return
        _options = None if _pw is None else {OPTION_PASSWORD: _pw}
        try:
            _init_action = ArestixAction.for_action_id(ACTION_INIT, self.selected_target[CFG_PAR_ALIAS],
                                                       self.arestix_config, _options)
            if _pw is not None:
                _init_action.set_option(OPTION_PASSWORD, _pw)
            self.__worker = Worker.for_action(_init_action)
            self.__worker.connect_signals(self.handle_progress, self.handle_finish, self.handle_result,
                                          self.handle_error)
        except ArestixException as _e:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
            return
        QThreadPool.globalInstance().start(self.__worker)

    def _year_end_clicked(self):
        """
        Wird aufgerufen, wenn der 'Jahresabschluss'-Button geklickt wurde.
        """
        _ok, _pw = super().start_button_clicked()
        if not _ok:
            return
        try:
            _options = self.__options_pane.selected_options()
            if _pw is not None:
                _options[OPTION_PASSWORD] = _pw
            _forget_action = ArestixAction.for_action_id(ACTION_FORGET, self.selected_target[CFG_PAR_ALIAS],
                                                         self.arestix_config, _options)
            _forget_action.set_option(OPTION_KEEP_MONTHLY, '1')
            _forget_action.set_option(OPTION_PRUNE, True)
            self.__worker = Worker.for_action(_forget_action)
            self.__worker.connect_signals(self.handle_progress, self.handle_finish, self.handle_result,
                                          self.handle_error)
        except ArestixException as _e:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
            return
        QThreadPool.globalInstance().start(self.__worker)

    def cancel_button_clicked(self):
        """
        Wird aufgerufen, wenn der 'Cancel'-Button geklickt wurde.
        """
        super().cancel_button_clicked()
        if self.__worker is not None:
            self.__worker.abort()
