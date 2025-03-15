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
Worker für die asynchrone Ausführung von restic-Befehlen als Hintergrund-Task.
"""

from collections.abc import Callable
from typing import Any, Self
from PySide6.QtCore import QObject, QRunnable, Signal

from restix.core import *
from restix.core.action import RestixAction
from restix.core.restix_exception import RestixException
from restix.core.messages import E_BACKGROUND_TASK_FAILED, E_INTERNAL_ERROR, E_INVALID_ACTION, localized_message
from restix.core.restic_interface import *
from restix.core.task import TaskExecutor, TaskMonitor, TaskProgress, TaskResult


class WorkerSignals(QObject):
    """
    Signale für die Kommunikation mit einem Worker.
    """

    # Task erfolgreich beendet
    finished = Signal()
    # Task mit Fehler beendet
    error = Signal(RestixException)
    # detailliertes Ergebnis der Task
    result = Signal(TaskResult)
    # Fortschritt der Task
    progress = Signal(TaskProgress)

    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()


class Worker(QRunnable, TaskExecutor):
    """
    Worker zur Ausführung einer Hintergrund-Task.
    """
    def __init__(self, worker_fn: Callable, *args: Any):
        """
        Konstruktor.
        :param worker_fn: die im Hintergrund auszuführende Funktion
        :param args: die Argumente für die Funktion
        """
        super().__init__()
        self.__fn = worker_fn
        self.__args = args
        self.__signals = WorkerSignals()
        self.__task_monitor = TaskMonitor(self)

    def abort(self):
        """
        Bricht die Ausführung der Hintergrund-Task ab.
        """
        self.__task_monitor.request_abort()

    def connect_signals(self, progress_slot: Callable, finished_slot: Callable, result_slot: Callable, error_slot: Callable):
        """
        Bindet die Signale an die übergebenen Slots.
        :param progress_slot: der Handler für Signal 'Progress'
        :param finished_slot: der Handler für Signal 'Finished'
        :param result_slot: der Handler für Signal 'Result'
        :param error_slot: der Handler für Signal 'Error'
        """
        if progress_slot is not None:
            self.__signals.progress.connect(progress_slot)
        if finished_slot is not None:
            self.__signals.finished.connect(finished_slot)
        if result_slot is not None:
            self.__signals.result.connect(result_slot)
        if error_slot is not None:
            self.__signals.error.connect(error_slot)

    def run(self):
        """
        Eintrittsfunktion für den Hintergrund-Thread.
        Führt die im Konstruktor übergebene Funktion aus.
        """
        try:
            _result = self.__fn(*self.__args, self.__task_monitor)
            self.__signals.result.emit(_result)
        except RestixException as _e:
            self.__signals.error.emit(_e)
        except BaseException as _e:
            _ex = RestixException(E_BACKGROUND_TASK_FAILED, str(_e))
            self.__signals.error.emit(_ex)
        self.__signals.finished.emit()

    def emit_progress(self, progress_data: TaskProgress):
        """
        Sendet ein Progress-Signal an den zugeordneten Slot.
        :param progress_data: Informationen über den Fortschritt der Task.
        """
        self.__signals.progress.emit(progress_data)

    @classmethod
    def for_action(cls: Self, action: RestixAction) -> Self:
        """
        Creates a worker for specified action.
        :param action: die vom Worker auszuführende Aktion
        :returns: Worker für die gewünschte Aktion
        """
        _action_id = action.action_id()
        if _action_id == ACTION_BACKUP:
            return Worker(run_backup, action)
        elif _action_id == ACTION_FORGET:
            return Worker(run_forget, action)
        elif _action_id == ACTION_INIT:
            return Worker(run_init, action)
        elif _action_id == ACTION_RESTORE:
            return Worker(run_restore, action)
        elif _action_id == ACTION_SNAPSHOTS:
            return Worker(run_snapshots, action)
        elif _action_id == ACTION_TAG:
            return Worker(run_tag, action)
        _emsg = localized_message(E_INVALID_ACTION, _action_id)
        raise RestixException(E_INTERNAL_ERROR, _emsg)
