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

from typing import Self
import datetime
import os.path
import platform
import re
import shlex
import tempfile

from restix.core import *
from restix.core import OPTION_AUTO_CREATE
from restix.core.config import LocalConfig, config_root_path
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
        self.__config_path = config_root_path()
        self.__options = {OPTION_HOST: platform.node(), OPTION_YEAR: str(datetime.date.today().year),
                          OPTION_USER: current_user(), OPTION_DRY_RUN: False, OPTION_BATCH: False}

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

    def option(self, option_name: str) -> str | bool | None:
        """
        :param option_name: der Name der gewünschten Option
        :returns: Wert der angegebenen Option; None, falls die Option nicht gesetzt wurde
        """
        _value = self.__options.get(option_name)
        return _value

    def set_option(self, option_name: str, option_value: bool | str):
        """
        Setzt die angegebene Option.
        Dateinamen müssen mit vollständigem Pfad angegeben werden.
        Bei benutzerdefinierten Angaben für Host und Jahr müssen diese als erste Optionen gesetzt werden.
        :param option_name: der Name der Option
        :param option_value: der Wert der Option
        """
        if option_value is None: return
        if option_name not in _STD_OPTIONS and option_name not in _ACTION_OPTIONS.get(self.__action_id):
            raise RestixException(E_INVALID_OPTION, option_name)
        if isinstance(option_value, str):
            # ggf. Variablen ersetzen
            for _var_name in CFG_VARS:
                _var_value = self.option(f'--{_var_name.lower()}')
                if _var_value is None:
                    raise RestixException(E_RESTIX_VAR_NOT_DEFINED, _var_name)
                option_value = option_value.replace(f'${{{_var_name}}}', str(_var_value))
        if option_name == OPTION_REPO:
            _repo_path = os.path.join(option_value, self.option(OPTION_YEAR),
                                      self.option(OPTION_HOST), self.option(OPTION_USER))
            self.__options[option_name] = _repo_path
            return
        if option_name == OPTION_BATCH or option_name == OPTION_DRY_RUN:
            if not isinstance(option_value, bool):
                raise RestixException(E_BOOL_OPT_REQUIRED, option_name)
        elif (option_name == OPTION_PASSWORD_FILE or option_name == OPTION_FILES_FROM or
              option_name == OPTION_INCLUDE_FILE or option_name == OPTION_EXCLUDE_FILE):
            if not os.path.isfile(option_value):
                raise RestixException(E_FILE_OPT_REQUIRED, option_value, option_name)
        elif option_name == OPTION_TARGET:
            # restore path must refer to an existing directory
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
        elif option_name == OPTION_HOST:
            # generous hostname check, but enough to prevent malicious values, as hostname is
            # part of the restic repository path
            if not re.match(r'^[a-z0-9\-_.]+$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_HOSTNAME, option_value)
        elif option_name == OPTION_SNAPSHOT:
            # restic snapshot IDs must be hex numbers
            if not re.match(r'^[a-f0-9]+$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_SNAPSHOT_ID, option_value)
        elif option_name == OPTION_YEAR:
            # year must be 4 digits
            if not re.match(r'^[0-9]{4}$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_YEAR, option_value)
        self.__options[option_name] = option_value

    def to_restic_command(self) -> list[str]:
        """
        :returns: restic-Kommando für die Daten dieser Aktion.
        """
        _cmd = ['restic', self.__action_id, OPTION_REPO, self.option(OPTION_REPO), OPTION_PASSWORD_FILE, self.option(OPTION_PASSWORD_FILE)]
        if self.option(OPTION_DRY_RUN):
            _cmd.append(OPTION_DRY_RUN)
        if self.__action_id == ACTION_BACKUP:
            _cmd.extend((OPTION_FILES_FROM, self.option(OPTION_FILES_FROM)))
            if OPTION_EXCLUDE_FILE in self.__options:
                _cmd.extend((OPTION_EXCLUDE_FILE, self.option(OPTION_EXCLUDE_FILE)))
            if OPTION_TAG in self.__options:
                _cmd.extend((OPTION_TAG, self.option(OPTION_TAG)))
            return _cmd
        if self.__action_id == ACTION_INIT or self.__action_id == ACTION_SNAPSHOTS:
            return _cmd
        return _cmd

    def _set_basic_options(self, local_config: LocalConfig, options: dict | None):
        """
        Setzt die Optionen, die restic immer benötigt sowie die angegebenen benutzerdefinierten Optionen.
        :param local_config: die restix-Konfiguration
        :param options: ggf. zusätzliche Optionen
        """
        # restic-Repository setzen
        _target = local_config.targets().get(self.target_alias())
        if _target is None:
            raise RestixException(E_RESTIX_TARGET_NOT_DEFINED, self.target_alias())
        self.set_option(OPTION_REPO, _target.get(CFG_PAR_LOCATION))
        # Zugangsdaten setzen
        _credentials = local_config.credentials_for_target(self.target_alias())
        if _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_FILE:
            self.set_option(OPTION_PASSWORD_FILE, self._full_filename_of(_credentials.get(CFG_PAR_VALUE)))
        # eventuell die angegebenen Optionen übernehmen
        if options is not None:
            for _k, _v in options.items():
                self.set_option(_k, _v)

    def _set_scope_options(self, scope: dict):
        """
        Setzt die Optionen für die zu sichernden und zu ignorierenden Daten.
        :param scope: der Backup-Umfang aus der restix-Konfiguration
        """
        _includes_file_path = self._full_filename_of(scope.get(CFG_PAR_INCLUDES))
        self.set_option(OPTION_FILES_FROM, _includes_file_path)
        _excludes_file_name = scope.get(CFG_PAR_EXCLUDES)
        _ignores = scope.get(CFG_PAR_IGNORES)
        if _ignores is None or len(_ignores) == 0:
            # keine Patterns für zu ignorierende Daten, Excludes-Datei 1:1 übernehmen, falls eine definiert ist
            if _excludes_file_name is not None:
                self.set_option(OPTION_EXCLUDE_FILE, self._full_filename_of(_excludes_file_name))
        else:
            # Patterns für zu ignorierende Daten in die Excludes-Datei eintragen, falls eine definiert ist
            _f = tempfile.NamedTemporaryFile('wt', delete=False)
            for _item in _ignores:
                _f.write(f'{_item}{os.linesep}')
            if _excludes_file_name is not None:
                with open(self._full_filename_of(_excludes_file_name), 'r') as _exclude_file:
                    _excludes = _exclude_file.readlines()
                _f.writelines(_excludes)
            self.set_option(OPTION_EXCLUDE_FILE, _f.name)

    def _full_filename_of(self, file_name: str) -> str:
        """
        :param file_name: Dateiname aus der Konfigurationsdatei
        :returns: Dateiname mit vollständigem Pfad
        """
        return file_name if os.path.isabs(file_name) else os.path.join(self.__config_path, file_name)

    def __str__(self) -> str:
        """
        :returns: Inhalt der Aktion in lesbarer Form.
        """
        return f'ID:{self.__action_id}/ALIAS:{self.target_alias()}/OPTIONS:{self.__options}'

    @classmethod
    def for_backup(cls: Self, target_alias: str, local_config: LocalConfig, options: dict = None) -> Self:
        """
        :param target_alias: der Aliasname des Backup-Ziels
        :param local_config: die restix-Konfiguration
        :param options: ggf. zusätzliche Optionen
        :returns: vollständige Beschreibung einer Backup-Aktion.
        :raises RestixException: falls die Aktion nicht aus den angegebenen Daten erzeugt werden kann
        """
        _action = RestixAction(ACTION_BACKUP, target_alias)
        # Standard-Optionen setzen
        _action._set_basic_options(local_config, options)
        # ein- und auszuschliessende Daten setzen
        _action._set_scope_options(local_config.scope_for_target(target_alias))
        return _action

    @classmethod
    def for_init(cls: Self, target_alias: str, local_config: LocalConfig, options: dict = None) -> Self:
        """
        :param target_alias: der Aliasname des Backup-Ziels
        :param local_config: die restix-Konfiguration
        :param options: ggf. zusätzliche Optionen
        :returns: vollständige Beschreibung einer Init-Aktion.
        :raises RestixException: falls die Aktion nicht aus den angegebenen Daten erzeugt werden kann
        """
        _action = RestixAction(ACTION_INIT, target_alias)
        # Standard-Optionen setzen
        _action._set_basic_options(local_config, options)
        return _action

    @classmethod
    def from_command_line(cls, cmd_line: list[str]) -> Self:
        """
        :param list[str] cmd_line: die Kommandozeile
        :returns: vollständige Beschreibung einer Aktion aus den Angaben der Kommandozeile.
        :raises RestixException: falls die Aktion nicht aus den angegebenen Daten erzeugt werden kann
        """
        _option_values = {}
        _action_id = ''
        _target = ''
        _host_value_expected = 0
        _restore_path_value_expected = 0
        _snapshot_value_expected = 0
        _tag_value_expected = 0
        _year_value_expected = 0
        _action_processed = False
        _target_processed = False
        _cmd_line = shlex.split(cmd_line[0]) if len(cmd_line) == 1 else cmd_line
        for _arg in _cmd_line:
            _arg = _arg.strip()
            # Optionswerte verarbeiten
            if _host_value_expected == 1:
                # vorangegangenes Argument war --host
                _option_values[OPTION_HOST] = _arg
                _host_value_expected = 2
                continue
            if _restore_path_value_expected == 1:
                # vorangegangenes Argument war --restore-path
                _option_values[OPTION_TARGET] = _arg
                _restore_path_value_expected = 2
                continue
            if _snapshot_value_expected == 1:
                # vorangegangenes Argument verlangt die Angabe einer Snapshot-ID
                _option_values[OPTION_SNAPSHOT] = _arg
                _snapshot_value_expected = 2
                continue
            if _tag_value_expected == 1:
                # vorangegangenes Argument verlangt die Angabe eines Tag-Namens
                _option_values[OPTION_TAG] = _arg
                _tags_value_expected = 2
                continue
            if _year_value_expected == 1:
                # vorangegangenes Argument war --year
                _option_values[OPTION_YEAR] = _arg
                _year_value_expected = 2
                continue
            if _arg.startswith('-'):
                # Option
                if _arg == OPTION_BATCH:
                    _option_values[OPTION_BATCH] = True
                    continue
                if _arg == OPTION_DRY_RUN:
                    _option_values[OPTION_DRY_RUN] = True
                    continue
                if _arg == OPTION_HELP:
                    _option_values[OPTION_HELP] = True
                    continue
                if _arg == OPTION_HOST:
                    if _host_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, _arg)
                    _host_value_expected = 1
                    continue
                if _arg == OPTION_RESTORE_PATH:
                    if _restore_path_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, _arg)
                    _restore_path_value_expected = 1
                    continue
                if _arg == OPTION_SNAPSHOT:
                    if _snapshot_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, _arg)
                    _snapshot_value_expected = 1
                    continue
                if _arg == OPTION_TAG:
                    if _tag_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, _arg)
                    _tag_value_expected = 1
                    continue
                if _arg == OPTION_YEAR:
                    if _year_value_expected > 0:
                        raise RestixException(E_CLI_DUP_OPTION, _arg)
                    _year_value_expected = 1
                    continue
                raise RestixException(E_CLI_INVALID_OPTION, _arg)
            if not _action_processed:
                if _option_values.get(OPTION_HELP):
                    # bei help kommt hier der Befehl, zu dem Hilfe angezeigt werden soll
                    _action = RestixAction(ACTION_HELP, '')
                    _action.set_option(OPTION_HELP, _arg)
                    return _action
                if _arg not in ALL_CLI_COMMANDS:
                    raise RestixException(E_CLI_INVALID_ACTION, _arg)
                _action_id = _arg
                _action_processed = True
                continue
            if not _target_processed:
                _target = _arg
                _target_processed = True
                continue
            raise RestixException(E_CLI_TOO_MANY_ARGS, _arg)
        if not _action_processed:
            raise RestixException(E_CLI_ACTION_MISSING)
        if _target is None and _action_id != CLI_COMMAND_TARGETS:
            raise RestixException(E_CLI_TARGET_MISSING, _action_id)
        if _action_id == CLI_COMMAND_TAG and (_option_values[OPTION_TAG] is None or
                                              _option_values[OPTION_SNAPSHOT] is None):
            raise RestixException(E_CLI_TAG_OPTIONS_MISSING)
        _action = RestixAction(_action_id, _target)
        for _k, _v in _option_values.items():
            _action.set_option(_k, _v)
        return _action


def build_restic_cmd(restix_action, restic_info):
    """
    Creates restic command for specified restix action.
    :param DetailAction restix_action: restix action including options
    :param dict restic_info: additional information
    :return: restic command
    :rtype: list[str]
    :raises RestixException: if desired action is not implemented
    """
    pass
    '''
    _restic_cmd = ['restic', '-r', restic_info[RESTIX_TOML_KEY_REPO], '-p', restic_info[RESTIX_TOML_KEY_PW_FILE]]
    if restix_action.option(CLI_OPTION_DRY_RUN):
        _restic_cmd.append('--dry-run')
    _base_action = restix_action.base_action()
    if _base_action == RESTIC_ACTION_SNAPSHOTS:
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
    '''


_STD_OPTIONS = {OPTION_REPO, OPTION_PASSWORD_FILE}
_ACTION_OPTIONS = {ACTION_BACKUP: {OPTION_AUTO_CREATE, OPTION_AUTO_TAG, OPTION_BATCH, OPTION_DRY_RUN,
                                   OPTION_EXCLUDE_FILE, OPTION_HOST, OPTION_FILES_FROM, OPTION_YEAR},
                   ACTION_FORGET: {OPTION_BATCH, OPTION_DRY_RUN, OPTION_SNAPSHOT, OPTION_UNTAGGED},
                   ACTION_INIT: {OPTION_BATCH},
                   ACTION_RESTORE: {OPTION_BATCH, OPTION_DRY_RUN, OPTION_HOST, OPTION_RESTORE_PATH, OPTION_SNAPSHOT,
                                    OPTION_YEAR},
                   ACTION_SNAPSHOTS: {OPTION_HOST, OPTION_YEAR},
                   ACTION_TAG: {OPTION_BATCH, OPTION_DRY_RUN, OPTION_SNAPSHOT, OPTION_TAG},
                   ACTION_HELP: {OPTION_HELP}}
