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
Classes associated with asynchronous task execution.
"""

import threading

from restix.core import SEVERITY_ERROR, SEVERITY_INFO, TASK_SUCCEEDED
from restix.core.restix_exception import RestixException
from restix.core.messages import localized_message, E_BACKGROUND_TASK_ABORTED


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
    Result of an asynchronous task.
    """
    def __init__(self, code, summary):
        """
        Constructor.
        :param int code: the task result code
        :param str summary: the localized task result summary
        """
        super().__init__()
        self.__code = code
        self.__summary = summary

    def task_succeeded(self):
        """
        :returns: True, if background task finished successfully
        :rtype: bool
        """
        return self.__code == TASK_SUCCEEDED

    def summary(self):
        """
        :returns : localized task result summary
        :rtype: str
        """
        return self.__summary


class TaskMonitor:
    """
    Handles monitoring of asynchronous task progress.
    """
    def __init__(self, progress_receiver=None):
        """
        Constructor.
        :param Slot progress_receiver: the GUI element handling progress; None for command line script
        """
        super().__init__()
        self.__progress_receiver = progress_receiver
        self.__error_count = 0
        self.__operation_count = 1
        self.__operations_processed = 0
        self.__operation_share = 100.0
        self.__abort_requested = False
        self.__dry_run = False
        self.__lock = threading.Lock()

    def errors_detected(self):
        """
        :returns: True, if at least one error message has been issued
        :rtype: bool
        """
        return self.__error_count > 0

    def set_operation_count(self, no_of_operations):
        """
        :param int no_of_operations: the total number of operations to process
        :rtype: None
        """
        self.__operation_count = 1 if no_of_operations <= 0 else no_of_operations
        self.__operations_processed = 0
        self.__operation_share = 100.0 / self.__operation_count

    def operations_processed(self, no_of_operations):
        """
        Increases internal counter of processed operations.
        :param int no_of_operations: the number of operations processed
        :rtype: None
        """
        self.__operations_processed += no_of_operations

    def is_dry_run(self):
        """
        :returns: True, if dry run mode is set; otherwise False
        :rtype: bool
        """
        return self.__dry_run

    def set_dry_run(self, mode):
        """
        Sets dry run mode.
        :param bool mode: True for dry run mode; otherwise False
        """
        self.__dry_run = mode is not None and mode

    def request_abort(self):
        """
        Sets internal flag to abort the task.
        :rtype: None
        """
        self.__lock.acquire()
        self.__abort_requested = True
        self.__lock.release()

    def abort_requested(self):
        """
        :returns: True, if task shall be aborted
        :rtype: bool
        """
        self.__lock.acquire()
        _abort_requested = self.__abort_requested
        self.__lock.release()
        return _abort_requested

    def check_abort(self):
        """
        Raise exception if abort was requested.
        """
        if self.abort_requested():
            raise RestixException(E_BACKGROUND_TASK_ABORTED)

    def log(self, msg_id, *msg_args):
        """
        Issues a localized progress message.
        Messages are shown in progress dialog window in Issai GUI, and on console in scripts.
        :param str msg_id: the message ID
        :param Any msg_args: the message arguments
        :rtype: None
        :raises IssaiException: if the user requested task abortion
        """
        _severity = msg_id[0]
        _msg = localized_message(msg_id, *msg_args)
        self.log_text(_msg, _severity)

    def log_text(self, msg, severity=SEVERITY_INFO):
        """
        Issues an already localized progress message.
        Messages are shown in progress dialog window in Issai GUI, and on console in scripts.
        :param str msg: the localized message
        :param str severity: the optional message severity
        :rtype: None
        :raises IssaiException: if the user requested task abortion
        """
        if severity == SEVERITY_ERROR:
            self.__error_count += 1
        if self.__progress_receiver is None:
            print(msg)
        else:
            _progress_value = int(self.__operations_processed * self.__operation_share)
            self.__progress_receiver.emit_progress(TaskProgress(_progress_value, severity, msg))
        if self.abort_requested():
            raise RestixException(E_BACKGROUND_TASK_ABORTED)


_DRY_RUN_INFIX = 'dry-run-'
