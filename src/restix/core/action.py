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
Daten für alle restix-Aktionen.
"""

import datetime
import platform
import re
import shlex
import subprocess
import tempfile

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.util import current_user


class RestixAction:
    """
    Datenklasse mit allen Informationen, die zum Ausführen einer restix-Aktion benötigt werden.
    """
    def __init__(self, action_id: str, target_alias: str):
        """
        Konstruktor.
        :param action_id: die ID der Aktion (backup, forget, init, ...)
        :param target_alias: der Aliasname des Backup-Ziels
        """
        self.__action_id = action_id
        self.__target_alias = target_alias
        self.__options = {OPTION_HOST: platform.node(), OPTION_YEAR: str(datetime.date.today().year),
                          OPTION_USER: current_user()}

    def action_id(self) -> str:
        """
        :returns: die ID der Aktion (backup, forget, init, ...)
        """
        return self.__action_id

    def target_alias(self) -> str | None:
        """
        :returns: Aliasname des Backup-Ziels
        """
        return self.__target_alias

    def option(self, option_name: str) -> str | None:
        """
        :param option_name: der Name der gewünschten Option
        :returns: Wert der angegebenen Option; None, falls die Option nicht gesetzt wurde
        """
        return self.__options.get(option_name)

    def set_option(self, option_name: str, option_value: bool | str):
        """
        Setzt die angegebene Option.
OPTION_DRY_RUN = '--dry-run'
OPTION_EXCLUDE_FILE = '--exclude-file'
OPTION_HOST= 'host'
OPTION_INCLUDE_FILE = '--files-from-file'
OPTION_PASSWORD_FILE = '--password-file'
OPTION_REPO = '--repo'
OPTION_TAG = '--tag'
OPTION_YEAR = 'year'
        :param option_name: der Name der Option
        :param option_value: der Wert der Option
        """
        if option_value is None: return
        if option_name == CLI_OPTION_BATCH:
            # batch option has no parameter
            self.__options[option_name] = True
            return
        if option_name == CLI_OPTION_RESTORE_PATH or option_name == CLI_OPTION_TARGET_MOUNT_PATH:
            # restore or target mount path must refer to an existing directory
            try:
                _path = os.path.abspath(option_value)
                if not os.path.exists(_path):
                    raise RestixException(E_CLI_NON_EXISTING_PATH, option_value, option_name)
                if not os.path.isdir(_path):
                    raise RestixException(E_CLI_PATH_IS_NOT_DIR, option_value, option_name)
                self.__options[option_name] = _path
                return
            except Exception as _e:
                raise RestixException(E_CLI_INVALID_PATH_SPEC, option_name, _e)
        if option_name == CLI_OPTION_HOST:
            # generous hostname check, but enough to prevent malicious values, as hostname is
            # part of the restic repository path
            if not re.match(r'^[a-z0-9\-_.]+$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_HOSTNAME, option_value)
        elif option_name == CLI_OPTION_SNAPSHOT:
            # restic snapshot IDs must be hex numbers
            if not re.match(r'^[a-f0-9]+$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_SNAPSHOT_ID, option_value)
        elif option_name == CLI_OPTION_YEAR:
            # year must be 4 digits
            if not re.match(r'^[0-9]{4}$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_YEAR, option_value)
        self.__options[option_name] = option_value

    def set_scope_options(self, scope: dict):
        """
        Setzt die Optionen für die zu sichernden und zu ignorierenden Daten.
        :param scope: der Backup-Umfang aus der restix-Konfiguration
        """
        self.set_option(OPTION_INCLUDE_FILE, scope.get(CFG_PAR_INCLUDES))
        _ignores = scope.get(CFG_PAR_IGNORES)
        if _ignores is None or len(_ignores) == 0:
            # keine Patterns für zu ignorierende Daten, Excludes-Datei 1:1 übernehmen
            self.set_option(OPTION_EXCLUDE_FILE, scope.get(CFG_PAR_EXCLUDES))
        else:
            # Patterns für zu ignorierende Daten in die Excludes-Datei eintragen
            with open(scope.get(CFG_PAR_EXCLUDES), 'r') as _exclude_file:
                _excludes = _exclude_file.readlines()
            _f = tempfile.NamedTemporaryFile()
            _f.writelines(_ignores)
            _f.writelines(_excludes)
            self.set_option(OPTION_EXCLUDE_FILE, _f.name)

    @classmethod
    def for_backup(cls, target_alias: str, local_config: LocalConfig, options:dict = None):
        """
        Setzt die Optionen für die zu sichernden und zu ignorierenden Daten.
        :param target_alias: der Aliasname des Backup-Ziels
        :param local_config: die restix-Konfiguration
        :param options: ggf. zusätzliche Optionen
        :returns: vollständige Beschreibung einer Backup-Aktion
        """
        _action = RestixAction(ACTION_BACKUP, target_alias)
        # restic-Repository setzen
        _action.set_option(OPTION_REPO, local_config.targets().get(target_alias).get(CFG_PAR_LOCATION))
        # ein- und auszuschliessende Daten setzen
        _action.set_scope_options(local_config.scope_for_target(target_alias))
        # eventuell die angegebenen Optionen übernehmen
        if options is not None:
            for _k, _v in options.items():
                _action.set_option(_k, _v)
        return _action

    @staticmethod
    def from_command_line(cmd_line):
        """
        Creates DetailAction objects from command line.
        :param list[str] cmd_line: the command line
        :returns: detail action
        :rtype: DetailAction
        :raises RestixException: if detail action cannot be created from command line
        """
        _option_values = {CLI_OPTION_BATCH: None, CLI_OPTION_HOST: None, CLI_OPTION_RESTORE_PATH: None,
                          CLI_OPTION_SNAPSHOT: None, CLI_OPTION_TAGS: None, CLI_OPTION_TARGET_MOUNT_PATH: None,
                          CLI_OPTION_YEAR: None}
        _base_action = ''
        _target = ''
        _host_value_expected = 0
        _restore_path_value_expected = 0
        _snapshot_value_expected = 0
        _target_mount_path_value_expected = 0
        _tags_value_expected = 0
        _year_value_expected = 0
        _action_processed = False
        _target_processed = False
        _cmd_line = shlex.split(cmd_line[0]) if len(cmd_line) == 1 else cmd_line
        for p in _cmd_line:
            p = p.strip()
            # option values
            if _host_value_expected == 1:
                _option_values[CLI_OPTION_HOST] = p
                _host_value_expected = 2
                continue
            if _restore_path_value_expected == 1:
                _option_values[CLI_OPTION_RESTORE_PATH] = p
                _restore_path_value_expected = 2
                continue
            if _snapshot_value_expected == 1:
                _option_values[CLI_OPTION_SNAPSHOT] = p
                _snapshot_value_expected = 2
                continue
            if _tags_value_expected == 1:
                _option_values[CLI_OPTION_TAGS] = p
                _tags_value_expected = 2
                continue
            if _target_mount_path_value_expected == 1:
                _option_values[CLI_OPTION_TARGET_MOUNT_PATH] = p
                _target_mount_path_value_expected = 2
                continue
            if _year_value_expected == 1:
                _option_values[CLI_OPTION_YEAR] = p
                _year_value_expected = 2
                continue
            if p.startswith('-'):
                # options
                if p == '-b' or p == '--batch':
                    _option_values[CLI_OPTION_BATCH] = True
                    continue
                if p == '--dry-run':
                    _option_values[CLI_OPTION_DRY_RUN] = True
                    continue
                if p == '--help':
                    return RestixAction(CLI_ACTION_HELP)
                if p == '--host':
                    if _host_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, p)
                    _host_value_expected = 1
                    continue
                if p == '-r' or p == '--restore-path':
                    if _restore_path_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, p)
                    _restore_path_value_expected = 1
                    continue
                if p == '-s' or p == '--snapshot':
                    if _snapshot_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, p)
                    _snapshot_value_expected = 1
                    continue
                if p == '--tags':
                    if _tags_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, p)
                    _tags_value_expected = 1
                    continue
                if p == '--target-mount-path':
                    if _target_mount_path_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, p)
                    _target_mount_path_value_expected = 1
                    continue
                if p == '-y' or p == '--year':
                    if _year_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, p)
                    _year_value_expected = 1
                    continue
                raise RestixException(E_CLI_INVALID_OPTION, p)
            if not _action_processed:
                if p not in ALL_CLI_ACTIONS:
                    raise RestixException(E_CLI_INVALID_ACTION, p)
                _base_action = p
                _action_processed = True
                continue
            if not _target_processed:
                _target = p
                _target_processed = True
                continue
            raise RestixException(E_CLI_TOO_MANY_ARGS, p)
        if not _action_processed:
            raise RestixException(E_CLI_ACTION_MISSING)
        if _target is None and _base_action != CLI_ACTION_TARGETS:
            raise RestixException(E_CLI_TARGET_MISSING, _base_action)
        if _base_action == CLI_ACTION_TAG and (_option_values[CLI_OPTION_TAGS] is None or
                                               _option_values[CLI_OPTION_SNAPSHOT] is None):
            raise RestixException(E_CLI_TAG_OPTIONS_MISSING)
        _action = RestixAction(_base_action, _target)
        for _k, _v in _option_values.items():
            if _v is not None:
                _action.set_option(_k, _v)
        return _action


def resolve_restix_vars_in_str(str_value, restix_vars):
    """
    Replaces all references to restix variables (${variable}) with actual values.
    :param str str_value: the string where variable references shall be replaced
    :param dict restix_vars: dictionary containing restix variable names and values
    :return: string with all variable references replaced by actual values
    :rtype: str
    :raises RestixException: if a referenced variable doesn't have an actual value (internal error)
    """
    _plain_value = str_value
    for _var_name in RESTIX_CFG_VARS:
        _var_value = restix_vars.get(_var_name)
        if _var_value is None:
            raise RestixException(E_RESTIX_VAR_NOT_DEFINED, _var_name)
        _plain_value = _plain_value.replace(f'${{{_var_name}}}', str(_var_value))
    return _plain_value


def resolve_restix_vars_in_value(value, restix_vars):
    """
    Replaces all references to restix variables (${variable}) with actual values.
    :param value: the Python value where variable references shall be replaced
    :param dict restix_vars: dictionary containing restix variable names and values
    :return: python value with all variable references replaced by actual values
    :raises RestixException: if a referenced variable doesn't have an actual value (internal error)
    """
    if isinstance(value, str):
        return resolve_restix_vars_in_str(value, restix_vars)
    if isinstance(value, list or tuple):
        return [resolve_restix_vars_in_value(_v, restix_vars) for _v in value]
    if isinstance(value, dict):
        for _k, _v in value.items():
            value[_k] = resolve_restix_vars_in_value(_v, restix_vars)
    return value


def restic_info_for(repo_alias, restix_settings):
    """
    Creates all information needed to execute restic command for desired restix action.
    :param str repo_alias: restix repository alias name
    :param dict restix_settings: local restix settings
    :return: all data needed to execute restic command
    :rtype: dict
    :raise RestixException: if repository alias is not defined or mandatory options are missing
    """
    # restic password file must be defined and exist
    _password_fn = restix_settings.get(RESTIX_TOML_KEY_PW_FILE)
    if _password_fn is None:
        raise RestixException(E_RESTIX_PW_FILE_NOT_DEFINED)
    if not os.path.isfile(_password_fn):
        raise RestixException(E_RESTIX_PW_FILE_DOES_NOT_EXIST, _password_fn)
    _restic_info = {RESTIX_TOML_KEY_PW_FILE: _password_fn, RESTIX_TOML_KEY_GUARD_FILE: None,
                    RESTIX_TOML_KEY_GUARD_TEXT: None}
    _guard_fn = restix_settings.get(RESTIX_TOML_KEY_GUARD_FILE)
    if _guard_fn is not None:
        # guard file name is defined, then the file must exist and an expected value for the contents must be defined
        if not os.path.isfile(_guard_fn):
            raise RestixException(E_RESTIX_GUARD_FILE_DOES_NOT_EXIST, _guard_fn)
        _guard_text = restix_settings.get(RESTIX_TOML_KEY_GUARD_TEXT)
        if _guard_text is None:
            raise RestixException(E_RESTIX_GUARD_TEXT_NOT_DEFINED, _guard_fn)
        _restic_info[RESTIX_TOML_KEY_GUARD_FILE] = _guard_fn
        _restic_info[RESTIX_TOML_KEY_GUARD_TEXT] = _guard_text
    for _target in restix_settings[RESTIX_TOML_KEY_TARGET]:
        if _target[RESTIX_TOML_KEY_ALIAS] != repo_alias:
            continue
        _restic_info[RESTIX_TOML_KEY_ALIAS] = repo_alias
        # make sure restic repository can be resolved from repository alias
        _repo = _target.get(RESTIX_TOML_KEY_REPO)
        if _repo is None:
            raise RestixException(E_RESTIX_TARGET_REPO_MISSING, repo_alias)
        _restic_info[RESTIX_TOML_KEY_REPO] = _repo
        # make sure backup scope is defined and referenced by repository alias
        _scope_name = _target.get(RESTIX_TOML_KEY_SCOPE)
        if _scope_name is None:
            raise RestixException(E_RESTIX_TARGET_SCOPE_MISSING, repo_alias)
        _scopes = restix_settings.get(RESTIX_TOML_KEY_SCOPE)
        if _scopes is None:
            raise RestixException(E_RESTIX_NO_SCOPES_DEFINED)
        for _scope in _scopes:
            if _scope_name != _scope[RESTIX_TOML_KEY_NAME]:
                continue
            _includes_fn = _scope.get(RESTIX_TOML_KEY_INCLUDES)
            if _includes_fn is None:
                raise RestixException(E_RESTIX_SCOPE_INCLUDES_MISSING, _scope_name)
            if not os.path.isfile(_includes_fn):
                raise RestixException(E_RESTIX_INCLUDES_FILE_DOES_NOT_EXIST, _includes_fn)
            _restic_info[RESTIX_TOML_KEY_INCLUDES] = _includes_fn
            _excludes_fn = _scope.get(RESTIX_TOML_KEY_EXCLUDES)
            if _excludes_fn is not None:
                if not os.path.isfile(_excludes_fn):
                    raise RestixException(E_RESTIX_EXCLUDES_FILE_DOES_NOT_EXIST, _excludes_fn)
            _restic_info[RESTIX_TOML_KEY_EXCLUDES] = _excludes_fn
            return _restic_info
        raise RestixException(E_RESTIX_TARGET_SCOPE_NOT_DEFINED, _scope_name, repo_alias)
    raise RestixException(E_RESTIX_TARGET_NOT_DEFINED, repo_alias)


def execute_restic_command(cmd):
    """
    Executes a restic command.
    Standard output and error are written to console.
    :param list[str] cmd: the restic command to execute
    :raises RestixException: if command execution returns an error
    """
    res = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    if len(res.stderr) > 0: print(res.stderr)
    if len(res.stdout) > 0: print(res.stdout)
    if res.returncode == 0:
        return
    _reason = E_CLI_RESTIC_CMD_FAILED
    if res.returncode == 2:
        _reason = E_CLI_RESTIC_GO_RUNTIME_ERROR
    elif res.returncode == 3:
        _reason = E_CLI_RESTIC_READ_BACKUP_DATA_FAILED
    elif res.returncode == 10:
        _reason = E_CLI_RESTIC_REPO_DOES_NOT_EXIST
    elif res.returncode == 11:
        _reason = E_CLI_RESTIC_REPO_LOCK_FAILED
    elif res.returncode == 12:
        _reason = E_CLI_RESTIC_REPO_WRONG_PASSWORD
    elif res.returncode == 130:
        _reason = E_CLI_RESTIC_CMD_INTERRUPTED
    raise RestixException(E_CLI_RESTIC_ACTION_FAILED, ' '.join(cmd), localized_label(_reason))


def build_restic_cmd(restix_action, restic_info):
    """
    Creates restic command for specified restix action.
    :param DetailAction restix_action: restix action including options
    :param dict restic_info: additional information
    :return: restic command
    :rtype: list[str]
    :raises RestixException: if desired action is not implemented
    """
    _restic_cmd = ['restic', '-r', restic_info[RESTIX_TOML_KEY_REPO], '-p', restic_info[RESTIX_TOML_KEY_PW_FILE]]
    if restix_action.option(CLI_OPTION_DRY_RUN):
        _restic_cmd.append('--dry-run')
    _base_action = restix_action.base_action()
    if _base_action == RESTIC_ACTION_BACKUP:
        _restic_cmd.append('--files-from')
        _restic_cmd.append(restic_info[RESTIX_TOML_KEY_INCLUDES])
        excl_fn = restic_info[RESTIX_TOML_KEY_EXCLUDES]
        if excl_fn:
            _restic_cmd.append('--exclude-file')
            _restic_cmd.append(excl_fn)
        _restic_cmd.append(_base_action)
        return _restic_cmd
    if _base_action == RESTIC_ACTION_INIT or _base_action == RESTIC_ACTION_SNAPSHOTS:
        _restic_cmd.append(_base_action)
        return _restic_cmd
    if _base_action == RESTIC_ACTION_RESTORE:
        _restic_cmd.append(_base_action)
        _snapshot_id = restix_action.option(CLI_OPTION_SNAPSHOT)
        if _snapshot_id is None:
            _restic_cmd.append('latest')
        else:
            _restic_cmd.append(_snapshot_id)
        _restore_path = restix_action.option(CLI_OPTION_RESTORE_PATH)
        if _restore_path is not None:
            _restic_cmd.append('--target')
            _restic_cmd.append(_restore_path)
        return _restic_cmd
    if _base_action == RESTIC_ACTION_FORGET:
        _restic_cmd.append(_base_action)
        _snapshot_id = restix_action.option(CLI_OPTION_SNAPSHOT)
        if _snapshot_id is None:
            _restic_cmd.append('--tag')
            _restic_cmd.append("''")
            _restic_cmd.append('--keep-last')
            _restic_cmd.append('1')
        else:
            _restic_cmd.append(_snapshot_id)
        _restic_cmd.append('--prune')
        return _restic_cmd
    if _base_action == RESTIC_ACTION_TAG:
        _restic_cmd.append(_base_action)
        _restic_cmd.append('--set')
        _restic_cmd.append(restix_action.option(CLI_OPTION_TAGS))
        _restic_cmd.append(restix_action.option(CLI_OPTION_SNAPSHOT))
        return _restic_cmd
    raise RestixException(E_CLI_INVALID_ACTION, _base_action)


def do_action(restix_action, restic_info):
    """
    Executes an action.
    :param DetailAction restix_action: restix action including options
    :param dict restic_info: additional information
    :raises RestixException: if command execution results in an error
    """
    # eventually check guard file first
    _base_action = restix_action.base_action()
    _guard_fn = restic_info.get(RESTIX_TOML_KEY_GUARD_FILE)
    if _guard_fn is not None and _base_action == RESTIC_ACTION_BACKUP:
        _expected_text = restic_info.get(RESTIX_TOML_KEY_GUARD_TEXT)
        try:
            with open(_guard_fn, 'r') as _f:
                _actual_text = _f.read().strip()
                _f.close()
                if _expected_text != _actual_text:
                    raise RestixException(E_RESTIX_GUARD_FILE_MODIFIED, _guard_fn)
        except RestixException as _e:
            raise _e
        except Exception as _e:
            raise RestixException(E_RESTIX_READ_GUARD_FILE_FAILED, _guard_fn, str(_e))
    # create and execute restic command from restix action
    _restic_cmd = build_restic_cmd(restix_action, restic_info)
    execute_restic_command(_restic_cmd)


def prompt_confirmation(restix_action, repo_alias):
    """
    Prompts user to confirm desired action. Confirmation is skipped if --batch option was specified or the action will
    not change data.
    :param DetailAction restix_action: restix action including options
    :param str repo_alias: the repository alias
    :return: True if the command may be executed; otherwise False
    :rtype: bool
    """
    _base_action = restix_action.base_action()
    if _base_action == RESTIC_ACTION_SNAPSHOTS or restix_action.option(CLI_OPTION_BATCH): return True
    if _base_action == RESTIC_ACTION_BACKUP:
        print(localized_message(T_CLI_CONFIRM_BACKUP, repo_alias))
    elif _base_action == RESTIC_ACTION_INIT:
        print(localized_message(T_CLI_CONFIRM_INIT, repo_alias))
    elif _base_action == RESTIC_ACTION_TAG:
        _tags = restix_action.option(CLI_OPTION_TAGS)
        _snapshot_id = restix_action.option(CLI_OPTION_SNAPSHOT)
        print(localized_message(T_CLI_CONFIRM_TAG_SNAPSHOT, _snapshot_id, repo_alias, _tags))
    elif _base_action == RESTIC_ACTION_FORGET:
        _snapshot_id = restix_action.option(CLI_OPTION_SNAPSHOT)
        if _snapshot_id is None:
            print(localized_message(T_CLI_CONFIRM_FORGET_UNTAGGED, repo_alias))
        else:
            print(localized_message(T_CLI_CONFIRM_FORGET_SNAPSHOT, _snapshot_id, repo_alias))
    else:
        # RESTORE
        _snapshot_id = restix_action.option(CLI_OPTION_SNAPSHOT)
        if _snapshot_id is None:
            _snapshot_id = 'latest'
        _restore_path = restix_action.option(CLI_OPTION_RESTORE_PATH)
        if _restore_path is None:
            _restore_path = os.sep
        print(localized_message(T_CLI_CONFIRM_RESTORE, _snapshot_id, _restore_path, repo_alias))
    ch = input(localized_label(T_CLI_PROMPT_FOR_CONFIRMATION))
    return ch.lower() == localized_label(T_CLI_YES_CHAR)
