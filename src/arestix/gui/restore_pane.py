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
GUI-Bereich für den Restore.
"""
import datetime
import platform
import tempfile

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QWidget, QGridLayout, QGroupBox, QMessageBox, QRadioButton, QPushButton, QDialog

from arestix.core import *
from arestix.core.action import ArestixAction
from arestix.core.config import LocalConfig
from arestix.core.messages import *
from arestix.core.arestix_exception import ArestixException
from arestix.core.restic_interface import determine_snapshots
from arestix.core.task import TaskMonitor
from arestix.gui import PAST_YEARS_COUNT
from arestix.gui.dialogs import SnapshotViewerDialog
from arestix.gui.panes import (ResticActionPane, create_combo, create_dir_selector, create_checkbox, create_text,
                               GROUP_BOX_STYLE, option_label)
from arestix.gui.settings import GuiSettings
from arestix.gui.worker import Worker


class RestoreOptionsPane(QGroupBox):
    """
    Pane für die Restore-Optionen.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: die übergeordnete Pane
        :param local_config: lokale arestix-Konfiguration
        """
        super().__init__(localized_label(L_OPTIONS), parent)
        self.__local_config = local_config
        self.__target_alias = None
        self.__selected_elements = None
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QGridLayout()
        _layout.setColumnStretch(3, 1)
        _layout.setContentsMargins(20, 20, 20, 20)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__snapshot_combo = create_combo(_layout, L_MANDATORY_SNAPSHOT, T_OPT_RST_SNAPSHOT)
        self.__restore_path_selector = create_dir_selector(_layout, L_RESTORE_PATH, T_OPT_RST_RESTORE_PATH)
        _layout.addWidget(option_label(L_RESTORE_SCOPE, localized_label(T_OPT_RST_RESTORE_SCOPE)), 3, 0)
        self.__full_radio = QRadioButton(localized_label(L_FULL))
        self.__full_radio.setToolTip(localized_label(T_OPT_RST_RESTORE_SCOPE_FULL))
        self.__full_radio.setChecked(True)
        _layout.addWidget(self.__full_radio, 3, 1)
        self.__some_radio = QRadioButton(localized_label(L_SOME))
        self.__some_radio.setToolTip(localized_label(T_OPT_RST_RESTORE_SCOPE_SOME))
        _layout.addWidget(self.__some_radio, 4, 1)
        _select_some_button = QPushButton(localized_label(L_SELECT))
        _select_some_button.clicked.connect(self._scope_button_clicked)
        _layout.addWidget(_select_some_button, 4, 2)
        self.__host_text = create_text(_layout, L_HOST, T_OPT_RST_HOST)
        self.__host_text.setText(platform.node())
        _current_year = datetime.datetime.now().year
        self.__year_combo = create_combo(_layout, L_YEAR, T_OPT_RST_YEAR)
        self.__year_combo.addItems([str(_y) for _y in range(_current_year, _current_year - PAST_YEARS_COUNT, -1)])
        self.__year_combo.setCurrentIndex(0)
        self.__dry_run_option = create_checkbox(_layout, L_DRY_RUN, T_OPT_RST_DRY_RUN, False)
        self.setLayout(_layout)

    def clear_snapshot_combo(self):
        """
        Leert die Combo-Box zur Auswahl eines Snapshots.
        """
        self.__snapshot_combo.clear()

    def fill_snapshot_combo(self, snapshots: list[str]):
        """
        Befüllt die Combo-Box zur Auswahl eines Snapshots mit den übergebenen Daten.
        :param snapshots: Daten aller Snapshots
        """
        self.__snapshot_combo.addItems(snapshots)
        for _i, _snapshot in enumerate(snapshots):
            _snapshot_id = _snapshot.split(' ')[-1]
            self.__snapshot_combo.setItemData(_i, _snapshot_id)

    def selected_options(self) -> dict:
        """
        :returns: Status der unterstützten Restore-Optionen (snapshot, restore-path, host, jahr und dry-run)
        """
        _snapshot = self.__snapshot_combo.currentData()
        if _snapshot is None or len(_snapshot) == 0:
            raise ArestixException(E_GUI_NO_SNAPSHOT_SELECTED)
        _options = {OPTION_SNAPSHOT: _snapshot, OPTION_YEAR: self.__year_combo.currentText(),
                    OPTION_DRY_RUN: self.__dry_run_option.isChecked()}
        _host = self.__host_text.text()
        if len(_host) > 0:
            _options[OPTION_HOST] = _host
        return _options

    def selected_elements(self) -> list[str]:
        """
        :returns: ausgewählte Elemente
        """
        return self.__selected_elements

    def selected_restore_path(self) -> str:
        """
        :returns: ausgewählter Pfad für die Wiederherstellung
        """
        return self.__restore_path_selector.text()

    def target_selected(self, target: dict):
        """
        Wird aufgerufen, wenn der Benutzer ein Backup-Ziel auswählt.
        Befüllt die Combo-Box mit den Snapshots des ausgewählten Backup-Ziels.
        """
        if target is None:
            return
        try:
            self.clear_snapshot_combo()
            self.__target_alias = target[CFG_PAR_ALIAS]
            _snapshots_action = ArestixAction.for_action_id(ACTION_SNAPSHOTS, target[CFG_PAR_ALIAS],
                                                            self.__local_config)
            _snapshots = determine_snapshots(_snapshots_action, TaskMonitor(None, True))
            _combo_data = [_s.combo_label() for _s in _snapshots]
            _combo_data.insert(0, RESTIC_SNAPSHOT_LATEST)
            self.fill_snapshot_combo(_combo_data)
        except ArestixException as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_RESTIC_CMD_FAILED, ACTION_SNAPSHOTS, str(_e)),
                                 QMessageBox.StandardButton.Ok)

    def _scope_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den Button zur Auswahl einzelner Dateien für die Wiederherstellung geklickt
        :returns:
        """
        if self.__target_alias is None:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_NO_TARGET_SELECTED), QMessageBox.StandardButton.Ok)
            return
        _snapshot_id = self.__snapshot_combo.currentData()
        if _snapshot_id is None or len(_snapshot_id) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_message(I_GUI_NO_SNAPSHOT_SELECTED), QMessageBox.StandardButton.Ok)
            return
        self.__some_radio.setChecked(True)
        _snapshot_viewer = SnapshotViewerDialog(self, _snapshot_id, self.__target_alias, self.__local_config,
                                                self.__host_text.text(), self.__year_combo.currentText())
        if _snapshot_viewer.exec_() != QDialog.DialogCode.Accepted:
            return
        self.__selected_elements = _snapshot_viewer.selected_elements()


class RestorePane(ResticActionPane):
    """
    Pane für den Backup.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: die zentrale arestix Pane
        :param local_config: lokale arestix-Konfiguration
        :param gui_settings: die GUI-Einstellungen des Benutzers
        """
        super().__init__(parent, [L_DO_RESTORE], [T_RST_DO_RESTORE], self._target_selected,
                         [self.start_button_clicked], local_config, gui_settings)
        self.__worker = None
        # option pane
        self.__options_pane = RestoreOptionsPane(self, local_config)
        self.pane_layout.addWidget(self.__options_pane, 0, 1)
        self.setLayout(self.pane_layout)

    def start_button_clicked(self):
        """
        Wird aufgerufen, wenn der 'Start Restore'-Button geklickt wurde.
        """
        super().start_button_clicked()
        try:
            _options = self.__options_pane.selected_options()
            _restore_action = ArestixAction.for_action_id(ACTION_RESTORE, self.selected_target[CFG_PAR_ALIAS],
                                                          self.restix_config, _options)
            _restore_action.set_option(OPTION_SNAPSHOT, _options.get(OPTION_SNAPSHOT))
            _restore_path = self.__options_pane.selected_restore_path()
            if _restore_path is not None and os.path.isdir(_restore_path):
                _restore_action.set_option(OPTION_RESTORE_PATH, _restore_path)
            _selected_elements = self.__options_pane.selected_elements()
            if _selected_elements is not None and len(_selected_elements) > 0:
                _f = tempfile.NamedTemporaryFile('wt', delete=False)
                for _element in _selected_elements:
                    _f.write(f'{_element}{os.linesep}')
                _restore_action.set_option(OPTION_INCLUDE_FILE, _f.name)
            self.__worker = Worker.for_action(_restore_action)
            self.__worker.connect_signals(self.handle_progress, self.handle_finish, self.handle_result, self.handle_error)
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

    def _target_selected(self):
        """
        Wird aufgerufen, wenn der Benutzer ein Backup-Ziel auswählt.
        Befüllt die Combo-Box mit den Snapshots des ausgewählten Backup-Ziels.
        """
        _selected_target = self.target_selection_pane.selected_target()
        self.__options_pane.target_selected(_selected_target)
