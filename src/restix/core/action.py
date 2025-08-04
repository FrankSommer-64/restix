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
import os.path
import platform
import re
import shlex
import tempfile

from restix.core import *
from restix.core import OPTION_AUTO_CREATE, OPTION_PATTERN
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
        :param action_id: ID der Aktion (backup, forget, init, ...)
        :param target_alias: Aliasname des Backup-Ziels
        """
        self.__action_id = action_id
        self.__target_alias = target_alias
        self.__local_config = None
        self.__options = {OPTION_HOST: platform.node(), OPTION_YEAR: str(datetime.date.today().year),
                          OPTION_USER: current_user(), OPTION_DRY_RUN: False, OPTION_BATCH: False}
        self.__temp_files = []

    def action_id(self) -> str:
        """
        :returns: ID der Aktion (backup, forget, init, ...)
        """
        return self.__action_id

    def restic_executable(self) -> str:
        """
        :returns: Pfad zum restic-Programm
        """
        return self.__local_config.restic_executable()

    def set_config(self, config: LocalConfig):
        """
        :param config: lokale restix-Konfiguration
        """
        self.__local_config = config

    def target_alias(self) -> str | None:
        """
        :returns: Aliasname des Backup-Ziels
        """
        return self.__target_alias

    def option(self, option_name: str) -> str | bool | None:
        """
        :param option_name: Name der gewünschten Option
        :returns: Wert der angegebenen Option; None, falls die Option nicht gesetzt wurde
        """
        _value = self.__options.get(option_name)
        return _value

    def set_option(self, option_name: str, option_value: bool | str, value_is_temp_file: bool = False):
        """
        Setzt die angegebene Option.
        Dateinamen müssen mit vollständigem Pfad angegeben werden.
        Bei benutzerdefinierten Angaben für Host und Jahr müssen diese als erste Optionen gesetzt werden.
        :param option_name: Name der Option
        :param option_value: Wert der Option
        :param value_is_temp_file: zeigt an, ob der übergebene Wert eine temporäre Datei ist
        """
        if option_value is None: return
        if value_is_temp_file:
            self.__temp_files.append(option_value)
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
            _repo_path = os.path.join(option_value, self.option(OPTION_USER), self.option(OPTION_HOST),
                                      self.option(OPTION_YEAR))
            self.__options[option_name] = _repo_path
            return
        if option_name == OPTION_BATCH or option_name == OPTION_DRY_RUN:
            if not isinstance(option_value, bool):
                raise RestixException(E_BOOL_OPT_REQUIRED, option_name)
        elif (option_name == OPTION_PASSWORD_FILE or option_name == OPTION_FILES_FROM or
              option_name == OPTION_INCLUDE_FILE or option_name == OPTION_EXCLUDE_FILE):
            if not os.path.isfile(option_value):
                raise RestixException(E_FILE_OPT_REQUIRED, option_value, option_name)
        elif option_name == OPTION_RESTORE_PATH:
            # restore path muss ein existierendes Verzeichnis sein
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
            # grosszügiger Check, aber genug um bösartige Werte zu verhindern
            if not re.match(r'^[a-z0-9\-_.]+$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_HOSTNAME, option_value)
        elif option_name == OPTION_SNAPSHOT:
            # Snapshot-IDs ist entweder 'latest' oder eine Hexadezimalzahl
            if option_value != 'latest' and not re.match(r'^[a-f0-9]+$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_SNAPSHOT_ID, option_value)
        elif option_name == OPTION_YEAR:
            # Jahr muss aus vier Ziffern bestehen
            if not re.match(r'^[0-9]{4}$', option_value, re.IGNORECASE):
                raise RestixException(E_INVALID_YEAR, option_value)
        self.__options[option_name] = option_value

    def remove_option(self, option_name: str):
        """
        Entfernt die angegebene Option.
        :param option_name: Name der Option
        """
        if option_name in self.__options:
            del self.__options[option_name]

    def verify_mandatory_options(self):
        """
        Prüft, ob alle notwendigen Optionen für eine Aktion gesetzt wurden.
        :raises RestixException: wenn mindestens eine notwendige Option nicht gesetzt wurde
        """
        if self.__action_id == ACTION_FIND or self.__action_id == ACTION_LS or self.__action_id == ACTION_RESTORE:
            if OPTION_SNAPSHOT not in self.__options:
                self.set_option(OPTION_SNAPSHOT, RESTIC_SNAPSHOT_LATEST)
        if self.__action_id == ACTION_RESTORE:
            if OPTION_RESTORE_PATH not in self.__options:
                self.set_option(OPTION_RESTORE_PATH, os.sep)
        _mandatory_options = _MANDATORY_OPTIONS.get(self.__action_id)
        if _mandatory_options is None:
            return
        for _option in _mandatory_options:
            if self.option(_option) is None:
                raise RestixException(E_MANDATORY_OPTION_MISSING, _option)

    def is_potential_long_runner(self):
        """
        :returns: True, falls die Ausführung der Action sehr lange dauern kann
        """
        return self.__action_id == ACTION_BACKUP or self.__action_id == ACTION_RESTORE

    def to_restic_command(self) -> list[str]:
        """
        :returns: restic-Kommando für die Daten dieser Aktion.
        """
        _cmd: list[str] = [self.__local_config.restic_executable(), self.__action_id,
                           OPTION_REPO, self.option(OPTION_REPO)]
        _pw_cmd = self.option(OPTION_PASSWORD_COMMAND)
        if _pw_cmd is not None:
            _cmd.extend([OPTION_PASSWORD_COMMAND, _pw_cmd])
        else:
            _cmd.extend([OPTION_PASSWORD_FILE, self.option(OPTION_PASSWORD_FILE)])
        if self.option(OPTION_DRY_RUN):
            _cmd.append(OPTION_DRY_RUN)
        if self.option(OPTION_JSON):
            _cmd.append(OPTION_JSON)
        if self.__action_id == ACTION_BACKUP:
            _cmd.extend((OPTION_FILES_FROM, self.option(OPTION_FILES_FROM)))
            if OPTION_EXCLUDE_FILE in self.__options:
                _cmd.extend((OPTION_EXCLUDE_FILE, self.option(OPTION_EXCLUDE_FILE)))
            return _cmd
        if self.__action_id == ACTION_RESTORE:
            if OPTION_RESTORE_PATH in self.__options:
                _cmd.extend([OPTION_TARGET, self.option(OPTION_RESTORE_PATH)])
            if OPTION_INCLUDE_FILE in self.__options:
                _cmd.extend((OPTION_INCLUDE_FILE, self.option(OPTION_INCLUDE_FILE)))
            _cmd.append(self.option(OPTION_SNAPSHOT))
            return _cmd
        if self.__action_id == ACTION_FORGET:
            if OPTION_KEEP_MONTHLY in self.__options:
                _cmd.extend((OPTION_KEEP_MONTHLY, self.option(OPTION_KEEP_MONTHLY)))
            if OPTION_PRUNE in self.__options:
                _cmd.append(OPTION_PRUNE)
                return _cmd
        if self.__action_id == ACTION_FIND:
            _cmd.extend((OPTION_SNAPSHOT, self.option(OPTION_SNAPSHOT)))
            _cmd.append(self.option(OPTION_PATTERN))
            return _cmd
        if self.__action_id == ACTION_LS:
            _cmd.append(self.option(OPTION_SNAPSHOT))
            return _cmd
        return _cmd

    def init_action(self) -> Self:
        """
        :returns: Init-Aktion aus dieser Aktion.
        """
        _init_action = RestixAction(ACTION_INIT, self.target_alias())
        _init_action.__options[OPTION_REPO] = self.option(OPTION_REPO)
        _init_action.__local_config = self.__local_config
        _pw_cmd = self.option(OPTION_PASSWORD_COMMAND)
        if _pw_cmd is not None:
            _init_action.__options[OPTION_PASSWORD_COMMAND] = _pw_cmd
        else:
            _init_action.__options[OPTION_PASSWORD_FILE] = self.option(OPTION_PASSWORD_FILE)
        return _init_action

    def snapshots_action(self) -> Self:
        """
        :returns: Snapshots-Aktion aus dieser Aktion.
        """
        _snapshots_action = RestixAction(ACTION_SNAPSHOTS, self.target_alias())
        _snapshots_action.__options[OPTION_REPO] = self.option(OPTION_REPO)
        _snapshots_action.__local_config = self.__local_config
        _pw_cmd = self.option(OPTION_PASSWORD_COMMAND)
        if _pw_cmd is not None:
            _snapshots_action.__options[OPTION_PASSWORD_COMMAND] = _pw_cmd
        else:
            _snapshots_action.__options[OPTION_PASSWORD_FILE] = self.option(OPTION_PASSWORD_FILE)
        _snapshots_action.__options[OPTION_JSON] = True
        return _snapshots_action

    def set_basic_options(self, local_config: LocalConfig, options: dict | None):
        """
        Setzt die Optionen, die restic immer benötigt sowie die angegebenen benutzerdefinierten Optionen.
        :param local_config: restix-Konfiguration
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
        elif _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_PGP:
            _file_path = self._full_filename_of(_credentials.get(CFG_PAR_VALUE))
            _cmd = f'""gpg --decrypt {_file_path}""'
            self.set_option(OPTION_PASSWORD_COMMAND, _cmd)
        elif _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_TEXT:
            _f = tempfile.NamedTemporaryFile('wt', delete=False)
            _f.write(_credentials.get(CFG_PAR_VALUE))
            _f.close()
            self.set_option(OPTION_PASSWORD_FILE, _f.name, True)
        elif _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_PROMPT:
            _f = tempfile.NamedTemporaryFile('wt', delete=False)
            _f.write(options.get(OPTION_PASSWORD))
            _f.close()
            self.set_option(OPTION_PASSWORD_FILE, _f.name, True)
        elif _credentials.get(CFG_PAR_TYPE) == CFG_VALUE_CREDENTIALS_TYPE_NONE:
            _restic_version = local_config.restic_version()
            if not _restic_version.empty_password_supported():
                raise RestixException(E_NO_PASSWORD_NOT_SUPPORTED, _restic_version.version())
            self.set_option(OPTION_NO_PASSWORD, True)
        # eventuell die angegebenen Optionen übernehmen
        if options is not None:
            for _k, _v in options.items():
                self.set_option(_k, _v)

    def set_scope_options(self, scope: dict):
        """
        Setzt die Optionen für die zu sichernden und zu ignorierenden Daten.
        :param scope: Backup-Umfang aus der restix-Konfiguration
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
            self.set_option(OPTION_EXCLUDE_FILE, _f.name, True)

    def action_executed(self):
        """
        Wird von der restic-Schnittstelle aufgerufen, nachdem die Aktion ausgeführt wurde.
        Löscht alle temporären Dateien.
        """
        for _f in self.__temp_files:
            try:
                os.remove(_f)
            except (IOError, OSError):
                pass
        self.__temp_files = []

    def _full_filename_of(self, file_name: str) -> str:
        """
        :param file_name: Dateiname aus der Konfigurationsdatei
        :returns: Dateiname mit vollständigem Pfad
        """
        return file_name if os.path.isabs(file_name) else os.path.join(self.__local_config.path(), file_name)

    def __str__(self) -> str:
        """
        :returns: Inhalt der Aktion in lesbarer Form.
        """
        return f'ID:{self.__action_id}/ALIAS:{self.target_alias()}/OPTIONS:{self.__options}'

    @classmethod
    def for_action_id(cls: Self, action_id: str, target_alias: str, local_config: LocalConfig,
                      options: dict = None) -> Self:
        """
        :param action_id: ID der Aktion
        :param target_alias: Aliasname des Backup-Ziels
        :param local_config: restix-Konfiguration
        :param options: ggf. zusätzliche Optionen
        :returns: vollständige Beschreibung der Aktion zur Ausführung mit restic.
        :raises RestixException: falls die Aktion nicht aus den angegebenen Daten erzeugt werden kann
        """
        _action = RestixAction(action_id, target_alias)
        _action.set_config(local_config)
        # Standard-Optionen setzen
        _action.set_basic_options(local_config, options)
        if action_id == ACTION_BACKUP:
            # ein- und auszuschliessende Daten setzen
            _action.set_scope_options(local_config.scope_for_target(target_alias))
        elif action_id == ACTION_SNAPSHOTS:
            _action.set_option(OPTION_JSON, True)
        return _action

    @classmethod
    def from_command_line(cls, cmd_line: list[str]) -> Self:
        """
        :param cmd_line: Kommandozeile
        :returns: vollständige Beschreibung einer Aktion aus den Angaben der Kommandozeile.
        :raises RestixException: falls die Aktion nicht aus den angegebenen Daten erzeugt werden kann
        """
        _option_values = {}
        _action_id = ''
        _target = ''
        _specified_options = set()
        _option_value_expected = None
        _action_processed = False
        _target_processed = False
        _cmd_line = shlex.split(cmd_line[0]) if len(cmd_line) == 1 else cmd_line
        for _arg in _cmd_line:
            _arg = _arg.strip()
            # Optionswerte verarbeiten
            if _option_value_expected is not None:
                _option_values[_option_value_expected] = _arg
                _option_value_expected = None
                continue
            if _arg.startswith('-'):
                # Option
                if _arg == OPTION_BATCH or _arg == OPTION_DRY_RUN or _arg == OPTION_AUTO_CREATE:
                    _option_values[_arg] = True
                    continue
                if _arg == OPTION_HELP:
                    _option_values[OPTION_HELP] = True
                    continue
                if _arg == OPTION_VERSION:
                    return RestixAction(ACTION_VERSION, '')
                if (_arg == OPTION_HOST or _arg == OPTION_PATTERN or _arg == OPTION_RESTORE_PATH or
                        _arg == OPTION_SNAPSHOT or _arg == OPTION_YEAR):
                    if _arg in _specified_options:
                        raise RestixException(E_CLI_DUP_OPTION, _arg)
                    _option_value_expected = _arg
                    _specified_options.add(_arg)
                    continue
                raise RestixException(E_CLI_INVALID_OPTION, _arg)
            if not _action_processed:
                if _option_values.get(OPTION_HELP):
                    # bei help kommt hier der Befehl, zu dem Hilfe angezeigt werden soll
                    _action = RestixAction(ACTION_HELP, '')
                    _action.set_option(OPTION_HELP, _arg)
                    return _action
                if _arg not in ALL_CLI_COMMANDS:
                    raise RestixException(E_CLI_INVALID_COMMAND, _arg)
                if _arg == CLI_COMMAND_CLEANUP:
                    _action_id = ACTION_FORGET
                    _option_values[OPTION_KEEP_MONTHLY] = '1'
                    _option_values[OPTION_PRUNE] = True
                else:
                    _action_id = _arg
                _action_processed = True
                continue
            if not _target_processed:
                _target = _arg
                _target_processed = True
                continue
            raise RestixException(E_CLI_TOO_MANY_ARGS, _arg)
        if not _action_processed:
            raise RestixException(E_CLI_COMMAND_MISSING)
        if _target is None and _action_id != CLI_COMMAND_TARGETS:
            raise RestixException(E_CLI_TARGET_MISSING, _action_id)
        _action = RestixAction(_action_id, _target)
        for _k, _v in _option_values.items():
            _action.set_option(_k, _v)
        return _action


_STD_OPTIONS = {OPTION_REPO, OPTION_PASSWORD, OPTION_PASSWORD_COMMAND, OPTION_PASSWORD_FILE}
_ACTION_OPTIONS = {ACTION_BACKUP: {OPTION_AUTO_CREATE, OPTION_BATCH, OPTION_DRY_RUN,
                                   OPTION_EXCLUDE_FILE, OPTION_FILES_FROM},
                   ACTION_FIND: {OPTION_HOST, OPTION_PATTERN, OPTION_JSON, OPTION_SNAPSHOT, OPTION_YEAR},
                   ACTION_FORGET: {OPTION_BATCH, OPTION_DRY_RUN, OPTION_HOST, OPTION_KEEP_MONTHLY,
                                   OPTION_PRUNE, OPTION_YEAR},
                   ACTION_INIT: {OPTION_BATCH, OPTION_DRY_RUN},
                   ACTION_LS: {OPTION_HOST, OPTION_JSON, OPTION_SNAPSHOT, OPTION_YEAR},
                   ACTION_RESTORE: {OPTION_BATCH, OPTION_DRY_RUN, OPTION_HOST, OPTION_INCLUDE_FILE,
                                    OPTION_SNAPSHOT, OPTION_RESTORE_PATH, OPTION_YEAR},
                   ACTION_SNAPSHOTS: {OPTION_BATCH, OPTION_HOST, OPTION_JSON, OPTION_YEAR},
                   ACTION_UNLOCK: {OPTION_BATCH, OPTION_HOST, OPTION_YEAR},
                   ACTION_HELP: {OPTION_HELP}}

_MANDATORY_OPTIONS = {ACTION_BACKUP: (OPTION_FILES_FROM,),
                      ACTION_FIND: (OPTION_PATTERN, OPTION_SNAPSHOT),
                      ACTION_LS: (OPTION_SNAPSHOT,),
                      ACTION_RESTORE: (OPTION_SNAPSHOT, OPTION_RESTORE_PATH)}
