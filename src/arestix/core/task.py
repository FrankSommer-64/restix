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
Informationen und Ergebnis einer asynchron ausgeführten Task.
"""

from abc import abstractmethod
from typing import Any
import threading

from arestix.core import SEVERITY_INFO, TASK_SUCCEEDED
from arestix.core.arestix_exception import ArestixException
from arestix.core.messages import localized_message, E_BACKGROUND_TASK_ABORTED


class TaskProgress:
    """
    Informationen über den Fortschritt einer asynchronen Task.
    """
    def __init__(self, completion_status: int, message_severity: str, message_text: str):
        """
        Konstruktor.
        :param completion_status: Fortschritt-Status in Prozent.
        :param message_severity: Schweregrad der Nachricht ('e' für Fehler, 'i' für Information, 'w' für Warnung).
        :param message_text: Text der Nachricht.
        """
        super().__init__()
        self.__completion_status = completion_status
        self.__message_severity = message_severity
        self.__message_text = message_text

    def completion_status(self) -> int:
        """
        :returns: Fortschritt-Status in Prozent.
        """
        return self.__completion_status

    def message_severity(self) -> str:
        """
        :returns: Schweregrad der Fortschritt-Nachricht ('e' für Fehler, 'i' für Information, 'w' für Warnung).
        """
        return self.__message_severity

    def message_text(self) -> str:
        """
        :returns: Text der Fortschritt-Nachricht.
        """
        return self.__message_text


class TaskResult:
    """
    Ergebnis einer asynchronen Task.
    """
    def __init__(self, code: int, summary: str):
        """
        Konstruktor.
        :param code: Ergebnis-Code (0 für ok, 1 für fehlgeschlagen)
        :param summary: Zusammenfassung des Ergebnisses
        """
        super().__init__()
        self.__code = code
        self.__summary = summary

    def task_succeeded(self) -> bool:
        """
        :returns: True, falls die Task erfolgreich ausgeführt wurde.
        """
        return self.__code == TASK_SUCCEEDED

    def summary(self) -> str:
        """
        :returns : lokalisierte Zusammenfassung des Ergebnisses
        """
        return self.__summary


class TaskExecutor:
    """
    Abstrakte Basisklasse für asynchrone Worker, die per TasḱMonitor überwacht werden können.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()

    @abstractmethod
    def emit_progress(self, progress_data: TaskProgress):
        """
        Sendet ein Progress-Signal an den zugeordneten Slot.
        :param progress_data: Informationen über den Fortschritt der Task.
        """
        pass


class TaskMonitor:
    """
    Überwacht die Ausführung einer asynchronen Task.
    """
    def __init__(self, progress_handler: TaskExecutor = None, silent: bool = False):
        """
        Konstruktor.
        :param progress_handler: Slot, der Fortschritts-Events entgegennimmt.
        """
        super().__init__()
        self.__progress_handler = progress_handler
        self.__silent = silent
        self.__abort_requested = False
        self.__lock = threading.Lock()

    def request_abort(self):
        """
        Setzt das interne Flag zum Abbrechen der Task.
        """
        self.__lock.acquire()
        self.__abort_requested = True
        self.__lock.release()

    def abort_requested(self) -> bool:
        """
        :returns: True, falls die Task abgebrochen werden soll.
        """
        self.__lock.acquire()
        _abort_requested = self.__abort_requested
        self.__lock.release()
        return _abort_requested

    def check_abort(self):
        """
        :raises RestixException: falls die Task abgebrochen werden soll.
        """
        if self.abort_requested():
            raise ArestixException(E_BACKGROUND_TASK_ABORTED)

    def log(self, msg_id: str, *msg_args: Any):
        """
        Sendet eine Fortschritt-Nachricht an den registrierten Handler. Falls kein Handler registriert
        wurde, wird die Nachricht auf der Konsole ausgegeben.
        :param msg_id: die ID der Nachricht
        :param msg_args: die Argumente für die Nachricht.
        :raises RestixException: falls die Task abgebrochen werden soll.
        """
        _severity = msg_id[0]
        _msg = localized_message(msg_id, *msg_args)
        self.log_text(_msg, _severity)

    def log_text(self, msg: str, severity: str = SEVERITY_INFO):
        """
        Sendet eine lokalisierte Fortschritt-Nachricht an den registrierten Handler. Falls kein Handler registriert
        wurde, wird die Nachricht auf der Konsole ausgegeben.
        :param msg: lokalisierte Nachricht
        :param severity: Schweregrad der Nachricht.
        :raises RestixException: falls die Task abgebrochen werden soll.
        """
        if not self.__silent:
            if self.__progress_handler is None:
                print(msg)
            else:
                self.__progress_handler.emit_progress(TaskProgress(50, severity, msg))
        if self.abort_requested():
            raise ArestixException(E_BACKGROUND_TASK_ABORTED)
