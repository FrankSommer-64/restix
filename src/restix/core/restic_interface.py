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
    _repo = action.option(OPTION_REPO)
    task_monitor.log(I_GUI_BACKING_UP_DATA, _repo)
    _rc, _, _ = _execute_restic_command(action.to_restic_command(), task_monitor, True)
    if _rc == RESTIC_RC_OK:
        _auto_tag(action, task_monitor)
        return TaskResult(TASK_SUCCEEDED, localized_message(I_GUI_DATA_BACKED_UP, _repo))
    if _rc != RESTIC_RC_REPO_DOES_NOT_EXIST or not action.option(OPTION_AUTO_CREATE) or action.option(OPTION_DRY_RUN):
        task_monitor.log(E_BACKGROUND_TASK_FAILED, '')
        return TaskResult(TASK_FAILED, '')
    # restic-Repository existiert nicht, Option auto-create wurde angegeben: Repository anlegen
    task_monitor.log(I_GUI_CREATING_REPO, _repo)
    _init_action = action.init_action()
    _rc, _, _ = _execute_restic_command(_init_action.to_restic_command(), task_monitor)
    if _rc == RESTIC_RC_OK:
        task_monitor.log(I_GUI_REPO_CREATED, _repo)
    else:
        task_monitor.log(E_BACKGROUND_TASK_FAILED, '')
        return TaskResult(TASK_FAILED, '')
    # Backup, zweiter Versuch
    _rc, _, _ = _execute_restic_command(action.to_restic_command(), task_monitor, True)
    if _rc == RESTIC_RC_OK:
        _auto_tag(action, task_monitor)
        return TaskResult(TASK_SUCCEEDED, localized_message(I_GUI_DATA_BACKED_UP, _repo))
    task_monitor.log(E_BACKGROUND_TASK_FAILED, '')
    return TaskResult(TASK_FAILED, '')


def run_forget(action: RestixAction, task_monitor: TaskMonitor):
    """
    Löscht einen Snapshot aus einem Repository.
    :param action: die Daten des auszuführenden Forget-Befehls.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls die Ausführung fehlschlägt
    """
    return TaskResult(TASK_FAILED, 'Noch nicht implementiert')


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


def run_tag(action: RestixAction, task_monitor: TaskMonitor):
    """
    Markiert einen Snapshot in einem Repository mit einem Tag.
    :param action: die Daten des auszuführenden Tags.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls die Ausführung fehlschlägt
    """
    try:
        _repo = action.option(OPTION_REPO)
        _snapshot_id = action.option(OPTION_SNAPSHOT)
        _tag = action.option(OPTION_TAG)
        if action.option(OPTION_DRY_RUN):
            task_monitor.log(I_DRY_RUN_TAGGING_SNAPSHOT, _snapshot_id, _repo, _tag)
            return TaskResult(TASK_SUCCEEDED, '')
        else:
            execute_restic_command(action.to_restic_command(), task_monitor)
        return TaskResult(TASK_SUCCEEDED, localized_message(I_GUI_SNAPSHOT_TAGGED, _snapshot_id, _repo, _tag))
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
    _exception_id = E_RESTIC_CMD_FAILED
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
    raise RestixException(_exception_id, ' '.join(cmd))


def _auto_tag(action: RestixAction, task_monitor: TaskMonitor):
    """
    Versieht Snapshots mit Tags, falls die Option auto-tag gesetzt wurde.
    :param action: die Daten des auszuführenden Backups.
    :param task_monitor: der Fortschritt-Handler.
    """
    if not action.option(OPTION_AUTO_TAG):
        return
    # Snapshots des Repositories holen
    _snapshots = determine_snapshots(action.snapshots_action(), task_monitor)
    _current_year = datetime.now().year
    _current_month = datetime.now().month
    _first_tag = f'{_current_year}_FIRST'
    if len(_snapshots) == 0:
        # Bei dry-run wurde kein Snapshot angelegt, d.h. Backup war der erste des Jahres, dann würde mit
        # Jahresanfangskennung getaggt. Ohne dry-run ist was schiefgegangen, dann tun wir hier nichts.
        if action.option(OPTION_DRY_RUN):
            task_monitor.log(I_DRY_RUN_TAGGING_FIRST_SNAPSHOT, _first_tag)
        return
    # ersten Snapshot des Jahres ggf. mit Jahresanfangskennung taggen
    _first_snapshot = _snapshots[0]
    if not _first_snapshot.is_tagged_with(_first_tag):
        # erster Snapshot hat noch keine Jahresanfangskennung
        if _tag_snapshot(action, _first_snapshot.snapshot_id(), _first_tag, task_monitor) != RESTIC_RC_OK:
            # Taggen hat nicht funktioniert, dann sparen wir uns auch die möglichen weiteren
            return
    if len(_snapshots) == 1:
        # bei nur einem Snapshot sind wir fertig
        return
    _last_snapshot = _first_snapshot
    for _snapshot in _snapshots[1:]:
        if _last_snapshot.month() < _snapshot.month():
            # letzter Snapshot eines Monats bekommt Tag 'YYYY_MM'
            _tag = f'{_current_year}_{_last_snapshot.month():02}'
            _tag_snapshot(action, _last_snapshot.snapshot_id(), _tag, task_monitor)


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
        raise RestixException(E_RESTIC_CMD_FAILED, action.action_id())
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
                raise RestixException(E_RESTIC_CMD_FAILED, 'keine Snapshot-Beschreibung')
            _snapshot.add_element(SnapshotElement(_element[JSON_ATTR_PATH], _element[JSON_ATTR_TYPE]))
        else:
            continue
    return _snapshot


def _tag_snapshot(action: RestixAction, snapshot_id: str, tag: str, task_monitor: TaskMonitor) -> int:
    """
    Markiert einen Snapshot mit dem angegebenen Tag.
    :param action: Backup-Aktion
    :param snapshot_id: ID des zu markierenden Snapshots
    :param tag: zu setzender Tag
    :param task_monitor: Fortschritt-Handler
    :return: Return code von restic
    """
    if action.option(OPTION_DRY_RUN):
        # bei dry-run nur Meldung ausgeben, was getaggt würde
        task_monitor.log(I_DRY_RUN_TAGGING_SNAPSHOT, snapshot_id, action.option(OPTION_REPO), tag)
        return RESTIC_RC_OK
    _tag_action = action.tag_action(snapshot_id, tag)
    _rc, _stdout, _stderr = _execute_restic_command(_tag_action.to_restic_command(), task_monitor)
    if _rc == RESTIC_RC_OK:
        # restic-Befehl war erfolgreich, Meldung ausgeben
        task_monitor.log(I_TAGGED_SNAPSHOT, snapshot_id, tag)
    else:
        # restic-Befehl ist fehlgeschlagen, Warnung und restic-Ausgaben an den Fortschritt-Handler weiterreichen
        task_monitor.log(W_TAG_SNAPSHOT_FAILED, snapshot_id, tag)
        task_monitor.log(_stdout, SEVERITY_WARNING)
        task_monitor.log(_stderr, SEVERITY_WARNING)
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
