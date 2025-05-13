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
Lokalisierte Nachrichten.
"""

import os

from typing import Self

from restix.core.util import platform_locale


# Allgemeine Nachrichten
E_ALIAS_NAME_ALREADY_USED = 'e-alias-name-already-used'
E_ALIAS_NAME_EMPTY = 'e-alias-name-empty'
E_ALIAS_REFERENCED = 'e-alias-referenced'
E_RESTIX_TARGET_NOT_DEFINED = 'e-restix-target-not-defined'
E_RESTIX_VAR_NOT_DEFINED = 'e-restix-var-not-defined'
E_BACKGROUND_TASK_ABORTED = 'e-background-task-aborted'
E_BACKGROUND_TASK_FAILED = 'e-background-task-failed'
E_BACKUP_FAILED = 'e-backup-failed'
E_BOOL_OPT_REQUIRED = 'e-bool-opt-required'
E_COULD_CREATE_REPO = 'e-could-not-create-repo'
E_COULD_NOT_DETERMINE_REPO_STATUS = 'e-could-not-determine-repo-status'
E_FILE_NAME_MISSING = 'e-file-name-missing'
E_FILE_OPT_REQUIRED = 'e-file-opt-required'
E_INTERNAL_ERROR = 'e-internal-error'
E_INVALID_ACTION = 'e-invalid-action'
E_INVALID_HOSTNAME = 'e-invalid-hostname'
E_INVALID_OPTION = 'e-invalid-option'
E_INVALID_SNAPSHOT_ID = 'e-invalid-snapshot-id'
E_INVALID_YEAR = 'e-invalid-year'
E_MANDATORY_OPTION_MISSING = 'e-mandatory-option-missing'
E_NO_SNAPSHOT_DESC_FROM_RESTIC = 'e-no-snapshot-desc-from-restic'
E_REPO_DOES_NOT_EXIST = 'e-repo-does-not-exist'
E_RESTIC_NOT_INSTALLED = 'e-restic-not-installed'
E_WRITE_FILE_FAILED = 'e-write-file-failed'
I_DRY_RUN_CREATE_REPO = 'i-dry-run-create-repo'
I_OVERWRITE_FILE = 'i-overwrite-file'
I_RUNNING_RESTIC_CMD = 'i-running-restic-cmd'
W_CANT_DRY_RUN_BACKUP_WITHOUT_REPO = 'w-cant-dry-run-backup-without-repo'
W_OUTDATED_RESTIC_VERSION = 'w-outdated-restic-version'

# Fehlermeldungen zur Konfiguration
E_CFG_CREATE_CONFIG_ROOT_FAILED = 'e-cfg-create-config-root-failed'
E_CFG_CREATE_PGP_FILE_FAILED = 'e-cfg-create-pgp-file-failed'
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
T_CLI_BACKUP_TARGETS_HEADER = 't-cli-backup-targets-header'
T_CLI_BACKUP_TARGET_INFO = 't-cli-backup-target-info'
T_CLI_CONFIRM_BACKUP = 't-cli-confirm-backup'
T_CLI_CONFIRM_CLEANUP = 't-cli-confirm-cleanup'
T_CLI_CONFIRM_INIT = 't-cli-confirm-init'
T_CLI_CONFIRM_RESTORE = 't-cli-confirm-restore'
T_CLI_ENTER_PASSWORD = 't-cli-enter-password'
T_CLI_PROMPT_FOR_CONFIRMATION = 't-cli-prompt-for-confirmation'
T_CLI_HELP_BACKUP = 't-cli-help-backup'
T_CLI_HELP_CLEANUP = 't-cli-help-cleanup'
T_CLI_HELP_FIND = 't-cli-help-find'
T_CLI_HELP_INIT = 't-cli-help-init'
T_CLI_HELP_LS = 't-cli-help-ls'
T_CLI_HELP_RESTORE = 't-cli-help-restore'
T_CLI_HELP_SHAPSHOTS = 't-cli-help-snapshots'
T_CLI_USAGE_INFO = 't-cli-usage-info'
T_CLI_YES_CHAR = 't-cli-yes-char'

# CLI messages
E_CLI_COMMAND_MISSING = 'e-cli-command-missing'
E_CLI_DUP_OPTION = 'e-cli-dup-option'
E_CLI_INVALID_COMMAND = 'e-cli-invalid-command'
E_CLI_INVALID_OPTION = 'e-cli-invalid-option'
E_CLI_INVALID_PATH_SPEC = 'e-cli-invalid-path-spec'
E_CLI_NON_EXISTING_PATH = 'e-cli-non-existing-path'
E_CLI_PATH_IS_NOT_DIR = 'e-cli-path-is-not-dir'
E_CLI_RESTIX_COMMAND_FAILED = 'e-cli-restix-command-failed'
E_CLI_TARGET_MISSING = 'e-cli-target-missing'
E_CLI_TOO_MANY_ARGS = 'e-cli-too-many-args'

# restic Fehler
E_RESTIC_CMD_FAILED = 'e-restic-cmd-failed'
E_RESTIC_CMD_INTERRUPTED = 'e-restic-cmd-interrupted'
E_RESTIC_GO_RUNTIME_ERROR = 'e-restic-go-runtime-error'
E_RESTIC_READ_BACKUP_DATA_FAILED = 'e-restic-read-backup-data-failed'
E_RESTIC_REPO_DOES_NOT_EXIST = 'e-restic-repo-does-not-exist'
E_RESTIC_REPO_LOCK_FAILED = 'e-restic-repo-lock-failed'
E_RESTIC_REPO_WRONG_PASSWORD = 'e-restic-repo-wrong-password'

# GUI Fehler
E_GUI_NO_SNAPSHOT_SELECTED = 'e-gui-no-snapshot-selected'

# GUI Ausgaben
I_GUI_RESTIX_INFO = 'i-gui-restix-info'
I_GUI_RESTIX_LINK = 'i-gui-restix-link'
I_GUI_RESTIX_COPYRIGHT = 'i-gui-restix-copyright'
I_GUI_CONFIG_PROBLEM = 'i-gui-config-problem'
I_GUI_CONFIG_WARNING = 'i-gui-config-warning'
I_GUI_CONFIRM_REMOVE = 'i-gui-confirm-remove'
I_GUI_CREATE_CONFIG_ROOT = 'i-gui-create-config-root'
I_GUI_CREATING_REPO = 'i-gui-creating-repo'
I_GUI_CREDENTIAL_EXISTS = 'i-gui-credential-exists'
I_GUI_DATA_RESTORED = 'i-gui-data-restored'
I_GUI_ICONS_COPYRIGHT = 'i-gui-icons-copyright'
I_GUI_ICONS_INFO = 'i-gui-icons-info'
I_GUI_ICONS_LINK = 'i-gui-icons-link'
I_GUI_LOCAL_CONFIG_CHANGED = 'i-gui-local-config-changed'
I_GUI_NO_CREDENTIAL_TYPE_SPECIFIED = 'i-gui-no-credential-type-specified'
I_GUI_NO_INCLUDES_SPECIFIED = 'i-gui-no-includes-specified'
I_GUI_NO_NAME_SPECIFIED = 'i-gui-no-name-specified'
I_GUI_NO_SNAPSHOT_SELECTED = 'i-gui-no-snapshot-selected'
I_GUI_NO_TARGET_SELECTED = 'i-gui-no-target-selected'
I_GUI_PYSIDE_INFO = 'i-gui-pyside-info'
I_GUI_PYSIDE_LINK = 'i-gui-pyside-link'
I_GUI_REPO_CREATED = 'i-gui-repo-created'
I_GUI_RESTORE_PATH_IS_NOT_DIR = 'i-gui-restore-path-is-not-dir'
I_GUI_RESTORING_ALL_DATA = 'i-gui-restoring-all-data'
I_GUI_RESTORING_ALL_DATA_TO_PATH = 'i-gui-restoring-all-data-to-path'
I_GUI_RESTORING_SOME_DATA = 'i-gui-restoring-some-data'
I_GUI_RESTORING_SOME_DATA_TO_PATH = 'i-gui-restoring-some-data-to-path'
I_GUI_SCOPE_EXISTS = 'i-gui-scope-exists'
I_GUI_TARGET_EXISTS = 'i-gui-target-exists'
I_GUI_TASK_FINISHED = 'i-gui-task-finished'
I_GUI_TOML_LIB_COPYRIGHT = 'i-gui-toml-lib-copyright'
I_GUI_TOML_LIB_INFO = 'i-gui-toml-lib-info'
I_GUI_TOMLI_LINK = 'i-gui-tomli-link'
I_GUI_TOMLIW_LINK = 'i-gui-tomliw-link'
I_GUI_VERSION = 'i-gui-version'

# GUI widget labels
L_DLG_TITLE_ABOUT = 'l-dlg-title-about'
L_DLG_TITLE_NEW_CREDENTIALS = 'l-dlg-title-new-credentials'
L_DLG_TITLE_NEW_SCOPE = 'l-dlg-title-new-scope'
L_DLG_TITLE_NEW_TARGET = 'l-dlg-title-new-target'
L_DLG_TITLE_PASSWORD = 'l-dlg-title-password'
L_DLG_TITLE_PGP_FILE = 'l-dlg-title-pgp-file'
L_DLG_TITLE_RENAME_ELEMENT = 'l-dlg-title-rename-element'
L_DLG_TITLE_SAVE_LOCAL_CONFIG = 'l-dlg-title-save-local-config'
L_DLG_TITLE_SCOPE_EDITOR = 'l-dlg-title-scope-editor'
L_DLG_TITLE_SELECT_EXCLUDES_FILE = 'l-dlg-title-select-excludes-file'
L_DLG_TITLE_SELECT_FILE = 'l-dlg-title-select-file'
L_DLG_TITLE_SELECT_INCLUDES_FILE = 'l-dlg-title-select-includes-file'
L_DLG_TITLE_SNAPSHOT_VIEWER = 'l-dlg-title-snapshot-viewer'
L_DLG_TITLE_USER_MANUAL = 'l-dlg-title-user-manual'
L_MAIN_WIN_TITLE = 'l-main-win-title'
L_MBOX_TITLE_ERROR = 'l-mbox-title-error'
L_MBOX_TITLE_INFO = 'l-mbox-title-info'
L_MBOX_TITLE_WARNING = 'l-mbox-title-warning'
L_MENU_ABOUT = 'l-menu-about'
L_MENU_REMOVE = 'l-menu-remove'
L_MENU_RENAME = 'l-menu-rename'
L_MENU_USER_MANUAL = 'l-menu-user-manual'

# GUI labels
L_ADD = 'l-add'
L_ADOPT_SELECTION = 'l-adopt-selection'
L_ALIAS = 'l-alias'
L_ASCII_ARMOR = 'l-ascii-armor'
L_RESTIX = 'l-restix'
L_AUTO_CREATE = 'l-auto-create'
L_BACKUP = 'l-backup'
L_CANCEL = 'l-cancel'
L_COMMENT = 'l-comment'
L_CONFIGURATION = 'l-configuration'
L_CREATE_ENCRYPTED_FILE = 'l-create-encrypted-file'
L_CREDENTIALS = 'l-credentials'
L_CURRENT_ALIAS = 'l-current-alias'
L_DISMISS = 'l-dismiss'
L_DO_BACKUP = 'l-do-backup'
L_DO_INIT_REPO = 'l-do-init-repo'
L_DO_RESTORE = 'l-do-restore'
L_DO_YEAR_END = 'l-do-year-end'
L_DRY_RUN = 'l-dry-run'
L_EDIT = 'l-edit'
L_ELEMENT = 'l-element'
L_EMAIL = 'l-email'
L_ENTER_PASSWORD = 'l-enter-password'
L_EXIT = 'l-exit'
L_FILE_NAME = 'l-file-name'
L_FILES_N_DIRS = 'l-files-n-dirs'
L_FULL = 'l-full'
L_HOST = 'l-host'
L_IGNORES = 'l-ignores'
L_INFO = 'l-info'
L_LIBRARIES = 'l-libraries'
L_LICENSE = 'l-license'
L_LOCATION = 'l-location'
L_MAINTENANCE = 'l-maintenance'
L_MANDATORY_SNAPSHOT = 'l-mandatory-snapshot'
L_NEW = 'l-new'
L_NEW_ALIAS = 'l-new-alias'
L_OK = 'l-ok'
L_OPTIONS = 'l-options'
L_PASSWORD = 'l-password'
L_RENAME = 'l-rename'
L_RESTORE = 'l-restore'
L_RESTORE_PATH = 'l-restore-path'
L_RESTORE_SCOPE = 'l-restore-scope'
L_SAVE = 'l-save'
L_SAVE_AS = 'l-save-as'
L_SCOPE = 'l-scope'
L_SCOPES = 'l-scopes'
L_SEARCH = 'l-search'
L_SELECT = 'l-select'
L_SELECT_ELEMENTS = 'l-select-elements'
L_SHOW_ALL_ELEMENTS = 'l-show-all-elements'
L_SOME = 'l-some'
L_TARGET = 'l-target'
L_TARGETS = 'l-targets'
L_TYPE = 'l-type'
L_UPDATE = 'l-update'
L_YEAR = 'l-year'

# GUI Tooltips
T_CANCEL_ACTION = 't-cancel-action'
T_CFG_CREATE_ENCRYPTED_FILE = 't-cfg-create-encrypted-file'
T_CFG_CREDENTIAL_COMMENT = 't-cfg-credential-comment'
T_CFG_CREDENTIAL_ALIAS = 't-cfg-credential-alias'
T_CFG_CREDENTIAL_PASSWORD = 't-cfg-credential-password'
T_CFG_CREDENTIAL_TYPE = 't-cfg-credential-type'
T_CFG_CREDENTIAL_FILE_NAME = 't-cfg-credential-file-name'
T_CFG_PGP_ASCII_ARMOR = 't-cfg-pgp-ascii-armor'
T_CFG_PGP_EMAIL = 't-cfg-pgp-email'
T_CFG_PGP_FILE_NAME = 't-cfg-pgp-file-name'
T_CFG_PGP_PASSWORD = 't-cfg-pgp-password'
T_CFG_SCOPE_ALIAS = 't-cfg-scope-alias'
T_CFG_SCOPE_COMMENT = 't-cfg-scope-comment'
T_CFG_SCOPE_FILES_N_DIRS = 't-cfg-scope-files-n-dirs'
T_CFG_SCOPE_IGNORES = 't-cfg-scope-ignores'
T_CFG_TARGET_ALIAS = 't-cfg-target-alias'
T_CFG_TARGET_COMMENT = 't-cfg-target-comment'
T_CFG_TARGET_CREDENTIALS = 't-cfg-target-credentials'
T_CFG_TARGET_LOCATION = 't-cfg-target-location'
T_CFG_TARGET_SCOPE = 't-cfg-target-scope'
T_DO_BAK_BACKUP = 't-do-bak-backup'
T_DO_MNT_INIT_REPO = 't-do-mnt-init-repo'
T_DO_MNT_YEAR_END = 't-do-mnt-year-end'
T_RST_DO_RESTORE = 't-do-rst-restore'
T_OPT_BAK_AUTO_CREATE = 't-opt-bak-auto-create'
T_OPT_BAK_DRY_RUN = 't-opt-bak-dry-run'
T_OPT_MNT_DRY_RUN = 't-opt-mnt-dry-run'
T_OPT_MNT_HOST = 't-opt-mnt-host'
T_OPT_MNT_YEAR = 't-opt-mnt-year'
T_OPT_RST_DRY_RUN = 't-opt-rst-dry-run'
T_OPT_RST_HOST = 't-opt-rst-host'
T_OPT_RST_RESTORE_PATH = 't-opt-rst-restore-path'
T_OPT_RST_RESTORE_SCOPE = 't-opt-rst-restore-scope'
T_OPT_RST_RESTORE_SCOPE_FULL = 't-opt-rst-restore-scope-full'
T_OPT_RST_RESTORE_SCOPE_SOME = 't-opt-rst-restore-scope-some'
T_OPT_RST_SNAPSHOT = 't-opt-rst-snapshot'
T_OPT_RST_YEAR = 't-opt-rst-year'

# GUI Warnungen
W_GUI_WRITE_GUI_SETTINGS_FAILED = 'w-gui-write-gui-settings-failed'

# intern
_MSG_FILE_NAME_FMT = 'messages_{0}.txt'
_DEFAULT_LOCALE = 'en'
_EMSG_INST_CORRUPT = 'restix installation is corrupt: {0}'
_EMSG_NO_MSG_FILE_FOUND = 'Could not find localized message definition files'
_EMSG_READ_MSG_FILE_FAILED = 'Could not read localized message definition file {0}: {1}'


def localized_message(msg_id: str, *args) -> str:
    """
    Gibt die lokalisierte Nachricht für angegebene Message-ID und Argumente zurück.
    Die Anzahl der Argumente muss zur Anzahl der Platzhalter im Format-String der Nachricht passen.
    Gibt die Message-ID zurück, falls die interne Tabelle keine passende Nachricht enthält oder die Argumente nicht
    zum Format-String passen.
    :param msg_id: Resource-ID der Nachricht
    :param args: Argumente für die Nachricht
    :returns: lokalisierte Nachricht für angegebene Message-ID und Argumente
    """
    global _MESSAGE_TABLE
    return _MESSAGE_TABLE.message_for(msg_id, *args)


def localized_label(label_id: str) -> str:
    """
    :param label_id: Resource-ID des Labels
    :returns: lokalisierter Label für ein GUI-Element
    """
    global _MESSAGE_TABLE
    return _MESSAGE_TABLE.label_for(label_id)


class MessageTable(dict):
    """
    Tabelle mit allen lokalisierten Nachrichten für eine Sprache.
    Jede Nachricht muss in einer eigenen Zeile definiert werden, beginnend mit der Message ID, gefolgt von einem
    Leerzeichen und dem Format-String der Nachricht. Durch Backslash am Zeilenende kann sich der Format-String
    über mehrere Zeilen erstrecken. Zeilen, die mit einem #-Zeichen beginnen werden ignoriert.
    """
    def __init__(self, messages: str):
        """
        Konstruktor.
        :param messages: lokalisierte Nachrichten
        """
        super().__init__()
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

    def message_for(self, msg_id: str, *args) -> str:
        """
        Gibt die lokalisierte Nachricht für angegebene Message-ID und Argumente zurück.
        Die Anzahl der Argumente muss zur Anzahl der Platzhalter im Format-String der Nachricht passen.
        Gibt die Message-ID zurück, falls die interne Tabelle keine passende Nachricht enthält oder die Argumente nicht
        zum Format-String passen.
        :param msg_id: Resource-ID der Nachricht
        :param args: Argumente für die Nachricht
        :returns: lokalisierte Nachricht für angegebene Message-ID und Argumente
        """
        _fmt_str = self.get(msg_id)
        if _fmt_str is None:
            return msg_id
        _fmt_str = _fmt_str.replace(r'\n', os.linesep)
        try:
            return _fmt_str.format(*args)
        except (KeyError, IndexError, ValueError):
            return msg_id

    def label_for(self, label_id: str) -> str:
        """
        :param label_id: Resource-ID des Labels
        :returns: lokalisierter Label für ein GUI-Element
        """
        _label = self.get(label_id)
        return label_id if _label is None else _label

    @classmethod
    def for_locale(cls, locale: str | None) -> Self:
        """
        :param locale: locale-Code der Sprache (z.B. 'en')
        :returns: Tabelle mit den lokalisierten Nachrichten der angegebenen Sprache.
        :raises RuntimeError: falls die restix-Konfiguration korrupt ist
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
            return MessageTable(_msgs)
        except IOError as e:
            _cause = _EMSG_READ_MSG_FILE_FAILED.format(_msgs_file_path, str(e))
            raise RuntimeError(_EMSG_INST_CORRUPT.format(_cause))


# Tabelle mit allen lokalisierten Nachrichten für die lokale Plattform
_MESSAGE_TABLE = MessageTable.for_locale(platform_locale())
