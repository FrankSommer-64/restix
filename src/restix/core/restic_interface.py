# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# issai - Framework to run tests specified in Kiwi Test Case Management System
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
Functions to export entities from TCMS to files.
"""
from datetime import datetime
import json
import re
import subprocess

from restix.core import *
from restix.core.action import RestixAction
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.snapshot import Snapshot, SnapshotElement
from restix.core.task import TaskMonitor, TaskResult


def run_backup(action: RestixAction, task_monitor: TaskMonitor):
    """
    Sichert lokale Daten in einem restic-Repository.
    :param action: die Daten des auszuführenden Backups.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls das Backup fehlschlägt
    """
    _auto_create = action.option(OPTION_AUTO_CREATE) is True
    _dry_run = action.option(OPTION_DRY_RUN) is True
    _repo = action.option(OPTION_REPO)
    _status = _repo_status(action)
    if _status == 1:
        # Repository existiert
        pass
    elif _status == 0:
        # Repository existiert nicht
        if not _auto_create:
            # ohne auto create-Flag geht es nicht weiter
            task_monitor.log(E_REPO_DOES_NOT_EXIST, _repo)
            return TaskResult(TASK_FAILED, '')
        if _dry_run:
            # dry-run Flag gesetzt
            task_monitor.log(I_DRY_RUN_CREATE_REPO, _repo)
            task_monitor.log(W_CANT_DRY_RUN_BACKUP_WITHOUT_REPO, _repo)
            return TaskResult(TASK_SUCCEEDED, '')
        # Repository anlegen
        _init_action = action.init_action()
        _restic_cmd = _init_action.to_restic_command()
        task_monitor.log(I_RUNNING_RESTIC_CMD, ' '.join(_restic_cmd))
        _rc, _, _ = _execute_restic_command(_restic_cmd, task_monitor)
        if _rc != RESTIC_RC_OK:
            _detail_msg = localized_message(E_COULD_CREATE_REPO, _repo, _rc)
            task_monitor.log(E_BACKGROUND_TASK_FAILED, _detail_msg)
            return TaskResult(TASK_FAILED, '')
    else:
        # Fehler bei restic-Befehl
        _detail_msg = localized_message(E_COULD_NOT_DETERMINE_REPO_STATUS, _repo, _status)
        task_monitor.log(E_BACKGROUND_TASK_FAILED, _detail_msg)
        return TaskResult(TASK_FAILED, '')
    # Backup ausführen
    _restic_cmd = action.to_restic_command()
    task_monitor.log(I_RUNNING_RESTIC_CMD, ' '.join(_restic_cmd))
    _rc, _, _ = _execute_restic_command(action.to_restic_command(), task_monitor, True)
    if _rc == RESTIC_RC_OK:
        return TaskResult(TASK_SUCCEEDED, '')
    _detail_msg = localized_message(E_BACKUP_FAILED, _repo, _rc)
    task_monitor.log(E_BACKGROUND_TASK_FAILED, _detail_msg)
    return TaskResult(TASK_FAILED, '')


def run_forget(action: RestixAction, task_monitor: TaskMonitor) -> TaskResult:
    """
    Löscht Snapshots aus einem Repository.
    :param action: die Daten des auszuführenden Forget-Befehls.
    :param task_monitor: der Fortschritt-Handler.
    :returns: Ergebnis der Ausführung
    """
    try:
        _restic_cmd = action.to_restic_command()
        task_monitor.log(I_RUNNING_RESTIC_CMD, ' '.join(_restic_cmd))
        _repo = action.option(OPTION_REPO)
        execute_restic_command(_restic_cmd, task_monitor)
        return TaskResult(TASK_SUCCEEDED, '')
    except Exception as _e:
        return TaskResult(TASK_FAILED, str(_e))


def run_init(action: RestixAction, task_monitor: TaskMonitor):
    """
    Legt ein neues restic-Repository an.
    :param action: die Daten für die Initialisierung.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls das Erzeugen des Repositories fehlschlägt
    """
    _repo = action.option(OPTION_REPO)
    task_monitor.log(I_GUI_CREATING_REPO, _repo)
    try:
        execute_restic_command(action.to_restic_command(), task_monitor)
        return TaskResult(TASK_SUCCEEDED, localized_message(I_GUI_REPO_CREATED, _repo))
    except Exception as _e:
        task_monitor.log(E_BACKGROUND_TASK_FAILED, str(_e))
        return TaskResult(TASK_FAILED, str(_e))


def run_restore(action: RestixAction, task_monitor: TaskMonitor):
    """
    Stellt lokale Daten aus einem restic-Repository wieder her.
    :param action: die Daten des auszuführenden Restores.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls die Ausführung fehlschlägt
    """
    _repo = action.option(OPTION_REPO)
    _snapshot_id = action.option(OPTION_SNAPSHOT)
    _restore_path = action.option(OPTION_RESTORE_PATH)
    _included_files = action.option(OPTION_INCLUDE_FILE)
    if _restore_path is None and _included_files is None:
        _msg = localized_message(I_GUI_RESTORING_ALL_DATA, _repo)
    elif _restore_path is None:
        _msg = localized_message(I_GUI_RESTORING_SOME_DATA, _repo)
    elif _included_files is None:
        _msg = localized_message(I_GUI_RESTORING_ALL_DATA_TO_PATH, _repo, _restore_path)
    else:
        _msg = localized_message(I_GUI_RESTORING_SOME_DATA_TO_PATH, _repo, _restore_path)
    task_monitor.log_text(_msg)
    try:
        execute_restic_command(action.to_restic_command(), task_monitor)
        return TaskResult(TASK_SUCCEEDED, localized_message(I_GUI_DATA_RESTORED, _repo))
    except Exception as _e:
        task_monitor.log(E_BACKGROUND_TASK_FAILED, str(_e))
        return TaskResult(TASK_FAILED, str(_e))


def run_snapshots(action: RestixAction, task_monitor: TaskMonitor):
    """
    Gibt alle Snapshots in einem Repository zurück.
    :param action: die Daten des auszuführenden Snapshot-Befehls.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls die Ausführung fehlschlägt
    """
    try:
        execute_restic_command(action.to_restic_command(), task_monitor)
        return TaskResult(TASK_SUCCEEDED, '')
    except Exception as _e:
        task_monitor.log(E_BACKGROUND_TASK_FAILED, str(_e))
        return TaskResult(TASK_FAILED, str(_e))


def execute_restic_command(cmd: list[str], task_monitor: TaskMonitor, potential_long_runner: bool = False) -> str:
    """
    Führt einen restic-Befehl aus.
    Bei potenziell lang laufenden Befehlen werden die Fortschritt-Nachrichten sofort an den TaskMonitor weitergeleitet,
    ansonsten erst nach der Befehlsausführung.
    :param cmd: auszuführender restic-Befehl
    :param task_monitor: der Fortschritt-Handler.
    :param potential_long_runner: zeigt an, ob die Ausführung sehr lange dauern kann.
    :returns: die Standard-Ausgabe.
    :raises RestixException: falls die Ausführung fehlschlägt
    """
    _stdout = []
    if potential_long_runner:
        # potenziell lang laufender restic-Befehl, Ausgaben gleich an den TaskMonitor weiterreichen
        _p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        for _line in iter(_p.stdout.readline, ""):
            _stdout.append(_line.strip())
            task_monitor.log_text(_line.strip(), SEVERITY_INFO)
        for _line in iter(_p.stderr.readline, ""):
            task_monitor.log_text(_line.strip(), SEVERITY_ERROR)
        _rc = _p.wait()
        _stdout = os.linesep.join(_stdout)
    else:
        # kurz laufender restic-Befehl, Ausgaben erst am Ende aufsammeln
        res = subprocess.run(cmd, capture_output=True, encoding='utf-8')
        if len(res.stderr) > 0: task_monitor.log_text(res.stderr, SEVERITY_ERROR)
        _stdout = res.stdout
        if len(res.stdout) > 0: task_monitor.log_text(res.stdout, SEVERITY_INFO)
        _rc = res.returncode
    if _rc == 0:
        return _stdout
    _restic_cmd = ' '.join(cmd)
    if _rc == 2:
        _exception_id = E_RESTIC_GO_RUNTIME_ERROR
    elif _rc == 3:
        _exception_id = E_RESTIC_READ_BACKUP_DATA_FAILED
    elif _rc == 10:
        _exception_id = E_RESTIC_REPO_DOES_NOT_EXIST
    elif _rc == 11:
        _exception_id = E_RESTIC_REPO_LOCK_FAILED
    elif _rc == 12:
        _exception_id = E_RESTIC_REPO_WRONG_PASSWORD
    elif _rc == 130:
        _exception_id = E_RESTIC_CMD_INTERRUPTED
    else:
        raise RestixException(E_RESTIC_CMD_FAILED, _restic_cmd, _stdout)
    raise RestixException(_exception_id, _restic_cmd)


def determine_snapshots(action: RestixAction, task_monitor: TaskMonitor) -> list[Snapshot]:
    """
    Ermittelt alle Snapshots in einem Repository für die GUI.
    :param action: Snapshot-Aktion
    :param task_monitor: der Fortschritt-Handler.
    :returns: alle Snapshots im Repository.
    :raises RestixException: falls das Lesen der Snapshots fehlschlägt
    """
    _silent_monitor = TaskMonitor(None, True)
    _rc, _stdout, _stderr = _execute_restic_command(action.to_restic_command(), _silent_monitor)
    if _rc != RESTIC_RC_OK:
        task_monitor.log_text(_stdout, SEVERITY_INFO)
        task_monitor.log_text(_stderr, SEVERITY_ERROR)
        _result = f'{_stderr}{os.linesep}{_stdout}'
        raise RestixException(E_RESTIC_CMD_FAILED, action.action_id(), _result)
    _snapshots = []
    _result = json.loads(_stdout)
    for _element in _result:
        _snapshot_id = _element.get(JSON_ATTR_SHORT_ID)
        _time = _element.get(JSON_ATTR_TIME)
        _snapshot = Snapshot(_snapshot_id, datetime.fromisoformat(_time), '')
        _tags = _element.get(JSON_ATTR_TAGS)
        for _tag in _tags:
            _snapshot.add_tag(_tag)
        _snapshots.append(_snapshot)
    return _snapshots


def find_snapshot_elements(action: RestixAction) -> list[SnapshotElement]:
    """
    :param action: find-Aktion
    :returns: gefundene Elemente im Snapshot.
    :raises RestixException: falls das Lesen des Snapshots fehlschlägt
    """
    _silent_monitor = TaskMonitor(None, True)
    _rc, _stdout, _stderr = _execute_restic_command(action.to_restic_command(), _silent_monitor)
    if _rc != RESTIC_RC_OK:
        _result = f'{_stderr}{os.linesep}{_stdout}'
        raise RestixException(E_RESTIC_CMD_FAILED, action.action_id(), _result)
    _elements = []
    _result = json.loads(_stdout)
    for _match in _result:
        _match_elements = _match.get(JSON_ATTR_MATCHES)
        for _match_element in _match_elements:
            _elements.append(SnapshotElement(_match_element[JSON_ATTR_PATH], _match_element[JSON_ATTR_TYPE]))
    return _elements


def list_snapshot_elements(action: RestixAction) -> Snapshot:
    """
    :param action: ls-Aktion
    :returns: Snapshot mit allen Elementen.
    :raises RestixException: falls das Lesen des Snapshots fehlschlägt
    """
    _silent_monitor = TaskMonitor(None, True)
    _rc, _stdout, _stderr = _execute_restic_command(action.to_restic_command(), _silent_monitor)
    if _rc != RESTIC_RC_OK:
        _result = f'{_stderr}{os.linesep}{_stdout}'
        raise RestixException(E_RESTIC_CMD_FAILED, action.action_id(), _result)
    _elements = []
    _snapshot = None
    for _line in _stdout.split(os.linesep):
        _line = _line.strip()
        if len(_line) == 0:
            continue
        _element = json.loads(_line)
        if _element.get(JSON_ATTR_STRUCT_TYPE) == JSON_STRUCT_TYPE_SNAPSHOT:
            _snapshot = Snapshot(_element[JSON_ATTR_SHORT_ID], datetime.fromisoformat(_element[JSON_ATTR_TIME]), '')
            _tags = _element.get(JSON_ATTR_TAGS)
            if _tags is not None:
                for _tag in _tags:
                    _snapshot.add_tag(_tag)
        elif _element.get(JSON_ATTR_STRUCT_TYPE) == JSON_STRUCT_TYPE_NODE:
            if _snapshot is None:
                _reason = localized_message(E_NO_SNAPSHOT_DESC_FROM_RESTIC)
                raise RestixException(E_RESTIC_CMD_FAILED, ACTION_SNAPSHOTS, _reason)
            _snapshot.add_element(SnapshotElement(_element[JSON_ATTR_PATH], _element[JSON_ATTR_TYPE]))
        else:
            continue
    return _snapshot


def _repo_status(action: RestixAction) -> int:
    """
    :param action: Backup-Aktion
    :returns: 1: repo existiert, 0: repo existiert nicht, andere Werte: Fehler bei restic-Befehl
    """
    _snapshots_action = action.snapshots_action()
    _silent_monitor = TaskMonitor(None, True)
    _rc, _, _ = _execute_restic_command(_snapshots_action.to_restic_command(), _silent_monitor)
    if _rc == RESTIC_RC_OK: return 1
    if _rc == RESTIC_RC_REPO_DOES_NOT_EXIST: return 0
    return _rc


def _execute_restic_command(cmd: list[str], task_monitor: TaskMonitor,
                            potential_long_runner: bool = False) -> tuple[int, str, str]:
    """
    Führt einen restic-Befehl aus.
    Bei potenziell lang laufenden Befehlen werden die Fortschritt-Nachrichten sofort an den TaskMonitor weitergeleitet,
    ansonsten erst nach der Befehlsausführung.
    :param cmd: auszuführender restic-Befehl
    :param task_monitor: der Fortschritt-Handler.
    :param potential_long_runner: zeigt an, ob die Ausführung sehr lange dauern kann.
    :returns: Tupel mit restic-Return code, Inhalt Standard-Ausgabe, Inhalt Standard-Error.
    """
    _stdout = []
    _stderr = []
    if potential_long_runner:
        # potenziell lang laufender restic-Befehl, Ausgaben gleich an den TaskMonitor weiterreichen
        _p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        for _line in iter(_p.stdout.readline, ""):
            _stdout.append(_line.strip())
            task_monitor.log_text(_line.strip(), SEVERITY_INFO)
        for _line in iter(_p.stderr.readline, ""):
            _stderr.append(_line.strip())
            task_monitor.log_text(_line.strip(), SEVERITY_ERROR)
        _rc = _p.wait()
        _stdout = os.linesep.join(_stdout)
        _stderr = os.linesep.join(_stderr)
    else:
        # kurz laufender restic-Befehl, Ausgaben erst am Ende aufsammeln
        res = subprocess.run(cmd, capture_output=True, encoding='utf-8')
        if len(res.stderr) > 0: task_monitor.log_text(res.stderr, SEVERITY_ERROR)
        _stdout = res.stdout
        if len(res.stdout) > 0: task_monitor.log_text(res.stdout, SEVERITY_INFO)
        _stderr = res.stderr
        _rc = res.returncode
    return _rc, _stdout, _stderr


_SNAPSHOT_COLUMN_HOST = 'Host'
_SNAPSHOT_COLUMN_ID = 'ID'
_SNAPSHOT_COLUMN_SIZE = 'Size'
_SNAPSHOT_COLUMN_TAGS = 'Tags'
_SNAPSHOT_COLUMN_TIME = 'Time'
_SNAPSHOTS_HEADER_PATTERN = re.compile(r'ID\s+Time\s+Host\s+Tags\s+Size')
_SNAPSHOT_SEP_LINE_CHAR = '-'
_SNAPSHOT_CONTINUATION_LINE_CHAR = ' '
