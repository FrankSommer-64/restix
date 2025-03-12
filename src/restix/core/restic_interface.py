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

import subprocess

from restix.core import SEVERITY_INFO, SEVERITY_ERROR, OPTION_REPO, TASK_FAILED, TASK_SUCCEEDED
from restix.core.action import RestixAction
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.task import TaskMonitor, TaskResult


def backup(action: RestixAction, task_monitor: TaskMonitor):
    """
    Sichert lokale Daten in einem restic-Repository.
    :param action: die Daten des auszuführenden Backups.
    :param task_monitor: der Fortschritt-Handler.
    :raises RestixException: falls das Backup fehlschlägt
    """
    _repo = action.option(OPTION_REPO)
    task_monitor.log(I_GUI_BACKING_UP_DATA, _repo)
    try:
        execute_restic_command(action.to_restic_command(), task_monitor)
        return TaskResult(TASK_SUCCEEDED, localized_message(I_GUI_DATA_BACKED_UP, _repo))
    except Exception as _e:
        task_monitor.log(E_BACKGROUND_TASK_FAILED, str(_e))
        return TaskResult(TASK_FAILED, str(_e))


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
    _reason = E_CLI_RESTIC_CMD_FAILED
    if _rc == 2:
        _reason = E_CLI_RESTIC_GO_RUNTIME_ERROR
    elif _rc == 3:
        _reason = E_CLI_RESTIC_READ_BACKUP_DATA_FAILED
    elif _rc == 10:
        _reason = E_CLI_RESTIC_REPO_DOES_NOT_EXIST
    elif _rc == 11:
        _reason = E_CLI_RESTIC_REPO_LOCK_FAILED
    elif _rc == 12:
        _reason = E_CLI_RESTIC_REPO_WRONG_PASSWORD
    elif _rc == 130:
        _reason = E_CLI_RESTIC_CMD_INTERRUPTED
    raise RestixException(E_CLI_RESTIC_ACTION_FAILED, ' '.join(cmd), localized_label(_reason))
