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
GUI-Bereich für den Restore.
"""

import datetime
import platform
import tempfile

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QDialog, QGridLayout, QGroupBox, QMessageBox, QPushButton, QRadioButton, QWidget

from restix.core import *
from restix.core.action import RestixAction
from restix.core.restix_exception import RestixException
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.core.restic_interface import determine_snapshots
from restix.core.task import TaskMonitor
from restix.gui import PAST_YEARS_COUNT, WIDE_CONTENT_MARGIN
from restix.gui.dialogs import PasswordDialog, SnapshotViewerDialog
from restix.gui.panes import (create_checkbox, create_combo, create_dir_selector, create_text,
                              GROUP_BOX_STYLE, option_label, ResticActionPane)
from restix.gui.settings import GuiSettings
from restix.gui.worker import Worker


class RestoreOptionsPane(QGroupBox):
    """
    Pane für die Restore-Optionen.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig):
        """
        Konstruktor.
        :param parent: übergeordnete Pane
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__(localized_label(L_OPTIONS), parent)
        self.__local_config = local_config
        self.__target_alias = None
        self.__selected_elements = None
        self.__pw = ''
        self.setStyleSheet(GROUP_BOX_STYLE)
        _layout = QGridLayout(self)
        _layout.setColumnStretch(3, 1)
        _layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__host_text = create_text(_layout, L_HOST, T_OPT_RST_HOST)
        self.__host_text.setText(platform.node())
        self.__host_text.editingFinished.connect(self._host_edited)
        _current_year = datetime.datetime.now().year
        self.__year_combo = create_combo(_layout, L_YEAR, T_OPT_RST_YEAR)
        self.__year_combo.addItems([str(_y) for _y in range(_current_year, _current_year - PAST_YEARS_COUNT, -1)])
        self.__year_combo.setCurrentIndex(0)
        self.__year_combo.currentIndexChanged.connect(self._year_selected)
        self.__snapshot_combo = create_combo(_layout, L_SNAPSHOT, T_OPT_RST_SNAPSHOT)
        self.__restore_path_selector = create_dir_selector(_layout, L_RESTORE_PATH, T_OPT_RST_RESTORE_PATH)
        _scope_row = _layout.rowCount()
        _layout.addWidget(option_label(L_RESTORE_SCOPE, localized_label(T_OPT_RST_RESTORE_SCOPE)), _scope_row, 0)
        self.__full_radio = QRadioButton(localized_label(L_FULL))
        self.__full_radio.setToolTip(localized_label(T_OPT_RST_RESTORE_SCOPE_FULL))
        self.__full_radio.setChecked(True)
        self.__full_radio.toggled.connect(self._scope_radios_toggled)
        _layout.addWidget(self.__full_radio, _scope_row, 1)
        self.__some_radio = QRadioButton(localized_label(L_SOME))
        self.__some_radio.setToolTip(localized_label(T_OPT_RST_RESTORE_SCOPE_SOME))
        self.__some_radio.toggled.connect(self._scope_radios_toggled)
        _layout.addWidget(self.__some_radio, _scope_row+1, 1)
        _select_some_button = QPushButton(localized_label(L_SELECT))
        _select_some_button.clicked.connect(self._scope_button_clicked)
        _layout.addWidget(_select_some_button, _scope_row+1, 2)
        self.__dry_run_option = create_checkbox(_layout, L_DRY_RUN, T_OPT_RST_DRY_RUN, False)

    def fill_snapshot_combo(self, snapshots: list[str]):
        """
        Befüllt die Combo-Box zur Auswahl eines Snapshots mit den übergebenen Daten.
        :param snapshots: Daten aller Snapshots
        """
        self.__snapshot_combo.clear()
        self.__snapshot_combo.addItems(snapshots)
        for _i, _snapshot in enumerate(snapshots):
            _snapshot_id = _snapshot.split(' ')[0]
            self.__snapshot_combo.setItemData(_i, _snapshot_id)

    def some_restore_selected(self) -> bool:
        """
        :returns: True, falls nur ausgewählte Elemente aus der Sicherung zurückgeholt werden sollen
        """
        return self.__some_radio.isChecked()

    def selected_options(self) -> dict:
        """
        :returns: Status der unterstützten Restore-Optionen (snapshot, restore-path, host, jahr und dry-run)
        """
        _snapshot = self.__snapshot_combo.currentData()
        if _snapshot is None or len(_snapshot) == 0:
            raise RestixException(E_GUI_NO_SNAPSHOT_SELECTED)
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
        __restore_path = self.__restore_path_selector.selected_path()
        return os.path.abspath(os.sep) if __restore_path is None else __restore_path

    def _scope_radios_toggled(self):
        """
        Wird aufgerufen, wenn sich der Zustand der Radio-Buttons für den Restore-Umfang ändert.
        """
        if self.__full_radio.isChecked():
            self.__selected_elements = None

    def target_selected(self, target: dict):
        """
        Wird aufgerufen, wenn der Benutzer ein Backup-Ziel auswählt.
        Befüllt die Combo-Box mit den Snapshots des ausgewählten Backup-Ziels.
        """
        if target is None:
            return
        try:
            self.__target_alias = target[CFG_PAR_ALIAS]
            _snapshots = self._determine_snapshots()
            self.fill_snapshot_combo(_snapshots)
        except RestixException as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_RESTIC_CALL_FAILED, ACTION_SNAPSHOTS, str(_e)),
                                 QMessageBox.StandardButton.Ok)

    def _year_selected(self, index: int):
        """
        Wird aufgerufen, wenn der Benutzer das Jahr geändert hat
        :param index: Index der Jahreszahl in der Auswahlliste
        """
        if index < 0:
            return
        try:
            _snapshots = self._determine_snapshots()
            self.fill_snapshot_combo(_snapshots)
        except RestixException as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_RESTIC_CALL_FAILED, ACTION_SNAPSHOTS, str(_e)),
                                 QMessageBox.StandardButton.Ok)

    def _host_edited(self):
        """
        Wird aufgerufen, wenn der Benutzer den Hostnamen geändert hat
        """
        if len(self.__host_text.text()) == 0:
            return
        try:
            _snapshots = self._determine_snapshots()
            self.fill_snapshot_combo(_snapshots)
        except RestixException as _e:
            QMessageBox.critical(self, localized_label(L_MBOX_TITLE_ERROR),
                                 localized_message(E_RESTIC_CALL_FAILED, ACTION_SNAPSHOTS, str(_e)),
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
                                                self.__host_text.text(), self.__year_combo.currentText(), self.__pw)
        if _snapshot_viewer.exec() != QDialog.DialogCode.Accepted:
            return
        self.__selected_elements = _snapshot_viewer.selected_elements()

    def _determine_snapshots(self) -> list[str]:
        """
        Ermittelt die Snapshots in einem restic-Repository.
        :returns: alle Snapshots im Repository für den aktuellen Benutzer, Jahr und Host
        """
        _year = self.__year_combo.currentText()
        _host = self.__host_text.text()
        _options = {OPTION_YEAR: _year, OPTION_HOST: _host}
        _credentials = self.__local_config.credentials_for_target(self.__target_alias)
        if _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_PROMPT:
            # Passwort einlesen
            _pw_dlg = PasswordDialog(self)
            if _pw_dlg.exec() == QDialog.DialogCode.Accepted:
                self.__pw = _pw_dlg.password()
                _options[OPTION_PASSWORD] = self.__pw
        _snapshots_action = RestixAction.for_action_id(ACTION_SNAPSHOTS, self.__target_alias,
                                                       self.__local_config, _options)
        _snapshots = determine_snapshots(_snapshots_action, TaskMonitor(None, True))
        _combo_data = [_s.combo_label() for _s in _snapshots]
        _combo_data.insert(0, RESTIC_SNAPSHOT_LATEST)
        return _combo_data


class RestorePane(ResticActionPane):
    """
    Pane für den Backup.
    """
    def __init__(self, parent: QWidget, local_config: LocalConfig, gui_settings: GuiSettings):
        """
        Konstruktor.
        :param parent: zentrale restix Pane
        :param local_config: lokale restix-Konfiguration
        :param gui_settings: GUI-Einstellungen des Benutzers
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
        _ok, _pw = super().start_button_clicked()
        if not _ok:
            return
        try:
            _options = self.__options_pane.selected_options()
            if _pw is not None:
                _options[OPTION_PASSWORD] = _pw
            _restic_version = self.restix_config.restic_version()
            if _options.get(OPTION_DRY_RUN) and not _restic_version.restore_dry_run_supported():
                raise RestixException(E_RESTORE_DRY_RUN_NOT_SUPPORTED, _restic_version.version())
            _restore_action = RestixAction.for_action_id(ACTION_RESTORE, self.selected_target[CFG_PAR_ALIAS],
                                                         self.restix_config, _options)
            _restore_action.set_option(OPTION_SNAPSHOT, _options.get(OPTION_SNAPSHOT))
            _restore_path = self.__options_pane.selected_restore_path()
            if os.path.isdir(_restore_path):
                _restore_action.set_option(OPTION_RESTORE_PATH, _restore_path)
            else:
                raise RestixException(I_GUI_RESTORE_PATH_IS_NOT_DIR, _restore_path)
            if self.__options_pane.some_restore_selected():
                if not _restic_version.restore_include_file_supported():
                    raise RestixException(E_RESTORE_INCLUDE_NOT_SUPPORTED, _restic_version.version())
                _selected_elements = self.__options_pane.selected_elements()
                if _selected_elements is None or len(_selected_elements) > 0:
                    raise RestixException(E_RESTORE_NOTHING_SELECTED)
                _f = tempfile.NamedTemporaryFile('wt', delete=False)
                for _element in _selected_elements:
                    _f.write(f'{_element}{os.linesep}')
                _restore_action.set_option(OPTION_INCLUDE_FILE, _f.name, True)
            self.__worker = Worker.for_action(_restore_action)
            self.__worker.connect_signals(self.handle_progress, self.handle_finish, self.handle_result, self.handle_error)
        except RestixException as _e:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_ERROR), str(_e), QMessageBox.StandardButton.Ok)
            self.button_pane.action_stopped()
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
