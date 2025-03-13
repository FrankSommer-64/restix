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
import re
from datetime import datetime
import subprocess

from restix.core import *
from restix.core.action import RestixAction
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.task import TaskMonitor, TaskResult


class Snapshot:
    """
    Daten eines restic Snapshots.
    """
    def __init__(self, snapshot_id: str, time_stamp: datetime, tags: str):
        """
        Konstruktor.
        :param snapshot_id: Snapshot-ID
        :param time_stamp: Zeitstempel des Snapshots
        :param tags: Tags des Snapshots
        """
        self.__snapshot_id = snapshot_id
        self.__time_stamp = time_stamp
        self.__tags = tags

    def snapshot_id(self) -> str:
        """
        :returns: Snapshot-ID
        """
        return self.__snapshot_id

    def time_stamp(self) -> datetime:
        """
        :returns: Zeitstempel des Snapshots
        """
        return self.__time_stamp

    def tags(self) -> str:
        """
        :returns: Tags des Snapshots
        """
        return self.__tags

    def month(self) -> int:
        """
        :returns: Monat des Snapshot-Zeitstempels
        """
        return self.__time_stamp.month

    def is_tagged(self) -> bool:
        """
        :returns: True, falls der Snapshot mindestens einen Tag besitzt
        """
        return len(self.__tags) > 0

    def __str__(self) -> str:
        """
        :returns: Inhalt des Snapshots in lesbarer Form.
        """
        return f'ID:{self.__snapshot_id}/TIME:{self.__time_stamp}/TAGS:{self.__tags}'


def backup(action: RestixAction, task_monitor: TaskMonitor):
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


def init(action: RestixAction, task_monitor: TaskMonitor):
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
    Tagged einen Snapshot, falls die Option auto-tag gesetzt wurde.
    :param action: die Daten des auszuführenden Backups.
    :param task_monitor: der Fortschritt-Handler.
    """
    if not action.option(OPTION_AUTO_TAG):
        return
    # Snapshots des Repositories holen
    _snapshots = determine_snapshots(action.snapshots_action(), task_monitor)
    if len(_snapshots) == 0:
        # ohne Snapshots gibt's auch nichts zu taggen
        return
    _current_year = datetime.now().year
    _current_month = datetime.now().month
    if len(_snapshots) == 0 and action.option(OPTION_DRY_RUN):
        # Bei dry-run wird kein Snapshot angelegt, d.h. Backup war der erste des Jahres
        _tag = f'{_current_year}_FIRST'
        task_monitor.log(I_DRY_RUN_TAGGING_FIRST_SNAPSHOT, _tag)
        return
    if len(_snapshots) == 1:
        _tag = f'{_current_year}_FIRST'
        if not _snapshots[0].is_tagged():
            # einziger Snapshot hat noch keinen Tag für den ersten des Jahres
            if action.option(OPTION_DRY_RUN):
                task_monitor.log(I_DRY_RUN_TAGGING_SNAPSHOT, _snapshots[0].snapshot_id(), _tag)
                return
            _tag_action = action.tag_action(_snapshots[0].snapshot_id(), _tag)
            _rc, _stdout, _stderr = _execute_restic_command(_tag_action.to_restic_command(), task_monitor)
            if _rc == RESTIC_RC_OK:
                task_monitor.log(I_TAGGED_SNAPSHOT, _snapshots[0].snapshot_id(), _tag)
                return
            task_monitor.log(W_TAG_SNAPSHOT_FAILED, _snapshots[0].snapshot_id(), _tag)
            task_monitor.log(_stdout, SEVERITY_WARNING)
            task_monitor.log(_stderr, SEVERITY_WARNING)
        return
    _last_snapshot = _snapshots[-1] if action.option(OPTION_DRY_RUN) else _snapshots[-2]
    if _last_snapshot.month() < _current_month and not _last_snapshot.is_tagged():
        # letzter Snapshot eines Monats bekommt Tag 'YYYY_MM'
        _tag = f'{_current_year}_{_current_month:02}'
        _tag_action = action.tag_action(_last_snapshot.snapshot_id(), _tag)
        print(_tag_action)


def determine_snapshots(action: RestixAction, task_monitor: TaskMonitor) -> list[Snapshot]:
    """
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
        raise RestixException(E_RESTIC_CMD_FAILED, 'snapshots')
    _snapshots = []
    _stdout_lines = _stdout.split(os.linesep)
    _snapshot_expected = False
    _header_processed = False
    _id_index = -1
    _time_index = -1
    _host_index = -1
    _tags_index = -1
    _size_index = -1
    for _line in _stdout_lines:
        if _SNAPSHOTS_HEADER_PATTERN.match(_line):
            _id_index = _line.find('ID')
            _time_index = _line.find('Time')
            _host_index = _line.find('Host')
            _tags_index = _line.find('Tags')
            _size_index = _line.find('Size')
            _header_processed = True
            continue
        if _line.startswith('-'):
            if _snapshot_expected:
                break
            _snapshot_expected = True
            continue
        if _snapshot_expected and _header_processed:
            _id = _line[_id_index:_time_index].strip()
            _time = _line[_time_index:_host_index].strip()
            _tags = _line[_tags_index:_size_index].strip()
            _snapshots.append(Snapshot(_id, datetime.fromisoformat(_time), _tags))
    return _snapshots


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


_SNAPSHOTS_HEADER_PATTERN = re.compile(r'ID\s+Time\s+Host\s+Tags\s+Size')
