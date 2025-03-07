# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# restix - Datensicherung auf restic-Basis
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
Localized message support.
"""

import os

from restix.core.util import platform_locale

# General messages
E_BOOL_OPT_REQUIRED = 'e-bool-opt-required'
E_FILE_OPT_REQUIRED = 'e-file-opt-required'
E_INTERNAL_ERROR = 'e-internal-error'
E_INVALID_HOSTNAME = 'e-invalid-hostname'
E_INVALID_OPTION = 'e-invalid-option'
E_INVALID_RESTIX_CFG_FILE = 'e-invalid-restix-cfg-file'
E_INVALID_SNAPSHOT_ID = 'e-invalid-snapshot-id'
E_INVALID_YEAR = 'e-invalid-year'
E_RESTIX_CFG_FILE_NOT_FOUND = 'e-restix-cfg-file-not-found'
E_RESTIX_EXCLUDES_FILE_DOES_NOT_EXIST = 'e-restix-excludes-file-does-not-exist'
E_RESTIX_GUARD_FILE_DOES_NOT_EXIST = 'e-restix-guard-file-does-not-exist'
E_RESTIX_GUARD_FILE_MODIFIED = 'e-restix-guard-file-modified'
E_RESTIX_GUARD_TEXT_NOT_DEFINED = 'e-restix-guard-text-not-defined'
E_RESTIX_INCLUDES_FILE_DOES_NOT_EXIST = 'e-restix-includes-file-does-not-exist'
E_RESTIX_NO_SCOPES_DEFINED = 'e-restix-no-scopes-defined'
E_RESTIX_PW_FILE_DOES_NOT_EXIST = 'e-restix-pw-file-does-not-exist'
E_RESTIX_PW_FILE_NOT_DEFINED = 'e-restix-pw-file-not-defined'
E_RESTIX_READ_GUARD_FILE_FAILED = 'e-restix-read-guard-file-failed'
E_RESTIX_SCOPE_INCLUDES_MISSING = 'e-restix-scope-includes-missing'
E_RESTIX_TARGET_NEEDS_MOUNT_PATH = 'e-restix-target-needs-mount-path'
E_RESTIX_TARGET_NOT_DEFINED = 'e-restix-target-not-defined'
E_RESTIX_TARGET_REPO_MISSING = 'e-restix-target-repo-missing'
E_RESTIX_TARGET_SCOPE_MISSING = 'e-restix-target-scope-missing'
E_RESTIX_TARGET_SCOPE_NOT_DEFINED = 'e-restix-target-scope-not-defined'
E_RESTIX_VAR_NOT_DEFINED = 'e-restix-var-not-defined'

# Fehlermeldungen zur Konfiguration
E_CFG_CUSTOM_CONFIG_ROOT_NOT_FOUND = 'e-cfg-custom-config-root-not-found'
E_CFG_DEFAULT_CONFIG_ROOT_NOT_FOUND = 'e-cfg-default-config-root-not-found'
E_CFG_DUPLICATE_GROUP = 'e-cfg-duplicate-group'
E_CFG_INVALID_CREDENTIALS_REF = 'e-cfg-invalid-credentials-ref'
E_CFG_INVALID_ELEM_TYPE = 'e-cfg-invalid-elem-type'
E_CFG_INVALID_ELEM_VALUE = 'e-cfg-invalid-elem-value'
E_CFG_INVALID_SCOPE_REF = 'e-cfg-invalid-scope-ref'
E_CFG_INVALID_VARIABLE = 'e-cfg-invalid-variable'
E_CFG_MANDATORY_ELEM_MISSING = 'e-cfg-mandatory-elem-missing'
E_CFG_MANDATORY_GRP_MISSING = 'e-cfg-mandatory-grp-missing'
E_CFG_META_DESC_MISSING = 'e-cfg-meta-desc-missing'
E_CFG_READ_FILE_FAILED = 'e-cfg-read-file-failed'
W_CFG_ELEM_IGNORED = 'w-cfg-elem-ignored'

# CLI texts
T_CLI_BACKUP_TARGETS = 't-cli-backup-targets'
T_CLI_CONFIRM_BACKUP = 't-cli-confirm-backup'
T_CLI_CONFIRM_FORGET_SNAPSHOT = 't-cli-confirm-forget-snapshot'
T_CLI_CONFIRM_FORGET_UNTAGGED = 't-cli-confirm-forget-untagged'
T_CLI_CONFIRM_INIT = 't-cli-confirm-init'
T_CLI_CONFIRM_RESTORE = 't-cli-confirm-restore'
T_CLI_CONFIRM_TAG_LATEST = 't-cli-confirm-tag-latest'
T_CLI_CONFIRM_TAG_SNAPSHOT = 't-cli-confirm-tag-snapshot'
T_CLI_PROMPT_FOR_CONFIRMATION = 't-cli-prompt-for-confirmation'
T_CLI_USAGE_INFO = 't-cli-usage-info'
T_CLI_YES_CHAR = 't-cli-yes-char'

# CLI messages
E_CLI_ACTION_MISSING = 'e-cli-action-missing'
E_CLI_DUP_OPTION = 'e-cli-dup-option'
E_CLI_INVALID_ACTION = 'e-cli-invalid-action'
E_CLI_INVALID_OPTION = 'e-cli-invalid-option'
E_CLI_INVALID_PATH_SPEC = 'e-cli-invalid-path-spec'
E_CLI_NON_EXISTING_PATH = 'e-cli-non-existing-path'
E_CLI_PATH_IS_NOT_DIR = 'e-cli-path-is-not-dir'
E_CLI_RESTIC_ACTION_FAILED = 'e-cli-restic-action-failed'
E_CLI_RESTIC_CMD_FAILED = 'e-cli-restic-cmd-failed'
E_CLI_RESTIC_CMD_INTERRUPTED = 'e-cli-restic-cmd-interrupted'
E_CLI_RESTIC_GO_RUNTIME_ERROR = 'e-cli-restic-go-runtime-error'
E_CLI_RESTIC_READ_BACKUP_DATA_FAILED = 'e-cli-restic-read-backup-data-failed'
E_CLI_RESTIC_REPO_DOES_NOT_EXIST = 'e-cli-restic-repo-does-not-exist'
E_CLI_RESTIC_REPO_LOCK_FAILED = 'e-cli-restic-repo-lock-failed'
E_CLI_RESTIC_REPO_WRONG_PASSWORD = 'e-cli-restic-repo-wrong-password'
E_CLI_RESTIX_ACTION_FAILED = 'e-cli-restix-action-failed'
E_CLI_TAG_OPTIONS_MISSING = 'e-cli-tag-options-missing'
E_CLI_TARGET_MISSING = 'e-cli-target-missing'
E_CLI_TOO_MANY_ARGS = 'e-cli-too-many-args'

# GUI Ausgaben
I_GUI_ABOUT_DETAIL_TEXT = 'i-gui-about-detail-text'
I_GUI_ABOUT_INFO_TEXT = 'i-gui-about-info-text'
I_GUI_ABOUT_TEXT = 'i-gui-about-text'
I_GUI_CONFIG_PROBLEM = 'i-gui-config-problem'
I_GUI_CONFIG_WARNING = 'i-gui-config-warning'
I_GUI_CREATE_CONFIG_ROOT = 'i-gui-create-config-root'
I_GUI_NO_TARGET_SELECTED = 'i-gui-no-target-selected'

# GUI widget labels
L_DLG_TITLE_ABOUT = 'l-dlg-title-about'
L_DLG_TITLE_USER_MANUAL = 'l-dlg-title-user-manual'
L_MAIN_WIN_TITLE = 'l-main-win-title'
L_MBOX_TITLE_ERROR = 'l-mbox-title-error'
L_MBOX_TITLE_INFO = 'l-mbox-title-info'
L_MBOX_TITLE_WARNING = 'l-mbox-title-warning'
L_MENU_ABOUT = 'l-menu-about'
L_MENU_USER_MANUAL = 'l-menu-user-manual'

# GUI labels
L_ALIAS = 'l-alias'
L_AUTO_TAG = 'l-auto-tag'
L_BACKUP = 'l-backup'
L_COMMENT = 'l-comment'
L_CONFIGURATION = 'l-configuration'
L_CREDENTIALS = 'l-credentials'
L_DO_BACKUP = 'l-do-backup'
L_DRY_RUN = 'l-dry-run'
L_EXIT = 'l-exit'
L_HELP = 'l-help'
L_LOCATION = 'l-location'
L_MAINTENANCE = 'l-maintenance'
L_OK = 'l-ok'
L_OPTIONS = 'l-options'
L_RESTORE = 'l-restore'
L_SCOPE = 'l-scope'
L_TARGETS = 'l-targets'

# GUI Tooltips
T_OPT_BAK_AUTO_TAG = 't-opt-bak-auto-tag'
T_OPT_BAK_DRY_RUN = 't-opt-bak-dry-run'

# GUI Warnungen
W_GUI_WRITE_GUI_SETTINGS_FAILED = 'w-gui-write-gui-settings-failed'

# internal
_MSG_FILE_NAME_FMT = 'messages_{0}.txt'
_DEFAULT_LOCALE = 'en'
_EMSG_INST_CORRUPT = 'restix installation is corrupt: {0}'
_EMSG_NO_MSG_FILE_FOUND = 'Could not find localized message definition files'
_EMSG_READ_MSG_FILE_FAILED = 'Could not read localized message definition file {0}: {1}'


def localized_message(msg_id, *args):
    """
    Returns the localized message for given message ID and optional arguments.
    The number of optional arguments must match the number of placeholders used in the message's format string.
    Returns the message ID, if this table doesn't contain an appropriate message or there is a mismatch between
    optional arguments and format string.
    :param str msg_id: the message ID
    :param args: the optional additional arguments
    :returns: the localized message
    :rtype: str
    """
    global _MESSAGE_TABLE
    return _MESSAGE_TABLE.message_for(msg_id, *args)


def localized_label(label_id):
    """
    Returns the localized text for given label ID.
    :param str label_id: the label ID
    :rtype: str
    """
    global _MESSAGE_TABLE
    return _MESSAGE_TABLE.label_for(label_id)


class MessageTable(dict):
    def __init__(self, locale, messages):
        """
        Initializes the message table for the specified localized messages.
        Every message must be specified in a line starting with message ID followed by a space character and then
        the format string associated with the message ID. A backslash at the end of a line may be used as
        continuation. Lines starting with a hash mark or not complying with this format are ignored.
        :param str locale: the locale
        :param str messages: the localized messages
        """
        super().__init__()
        self.__locale = locale
        msg_id = None
        msg_text = ''
        msg_list = messages.split(os.linesep)
        for line in msg_list:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                if msg_id is not None:
                    self.update({msg_id: msg_text})
                    msg_id = None
                    msg_text = ''
                continue
            if line.endswith('\\'):
                if msg_id is not None:
                    msg_text = f'{msg_text} {line[:-1]}'
                else:
                    space_pos = line.index(' ')
                    msg_id = line[:space_pos]
                    msg_text = line[space_pos + 1:-1]
                continue
            if msg_id is not None:
                msg_text = f'{msg_text} {line}'
            else:
                space_pos = line.index(' ')
                msg_id = line[:space_pos]
                msg_text = line[space_pos + 1:]
            self.update({msg_id: msg_text})
            msg_id = None
            msg_text = ''

    def message_for(self, msg_id, *args):
        """
        Returns the localized message for given message ID and optional arguments.
        The number of optional arguments must match the number of placeholders used in the message's format string.
        Returns the message ID, if this table doesn't contain an appropriate message or there is a mismatch between
        optional arguments and format string.
        :param str msg_id: the message ID
        :param args: the optional additional arguments
        :returns: the localized message
        :rtype: str
        """
        _fmt_str = self.get(msg_id)
        if _fmt_str is None:
            return msg_id
        _fmt_str = _fmt_str.replace(r'\n', os.linesep)
        try:
            return _fmt_str.format(*args)
        except (KeyError, IndexError, ValueError):
            return msg_id

    def label_for(self, label_id):
        """
        Returns the localized label for given ID.
        Used for GUI widgets.
        :param str label_id: the label ID
        :rtype: str
        """
        _label = self.get(label_id)
        if _label is None:
            return label_id
        return _label

    def locale(self):
        """
        Returns the locale of this message table.
        Used for testing purposes.
        :returns: the locale
        :rtype: str
        """
        return self.__locale

    @staticmethod
    def for_locale(locale):
        """
        Creates a message table for the specified locale.
        Uses default locale, if locale is not supported.
        :param str locale: the locale
        :returns: message table for specified locale
        :rtype: MessageTable
        :raises RuntimeError: if no message definition files exist, i.e. installation is corrupt
        """
        _locale = _DEFAULT_LOCALE if locale is None else locale
        _msgs_file_name = _MSG_FILE_NAME_FMT.format(_locale)
        _current_dir = os.path.dirname(os.path.abspath(__file__))
        _msgs_file_path = os.path.join(_current_dir, _msgs_file_name)
        if not os.path.isfile(_msgs_file_path):
            _locale = _DEFAULT_LOCALE
            _msgs_file_path = os.path.join(_current_dir, _MSG_FILE_NAME_FMT.format(_locale))
        if not os.path.isfile(_msgs_file_path):
            raise RuntimeError(_EMSG_INST_CORRUPT.format(_EMSG_NO_MSG_FILE_FOUND))
        try:
            with open(_msgs_file_path, 'r') as f:
                _msgs = f.read()
            return MessageTable(_locale, _msgs)
        except IOError as e:
            _cause = _EMSG_READ_MSG_FILE_FAILED.format(_msgs_file_path, str(e))
            raise RuntimeError(_EMSG_INST_CORRUPT.format(_cause))


# All localized messages, eventually containing placeholders
_MESSAGE_TABLE = MessageTable.for_locale(platform_locale())
