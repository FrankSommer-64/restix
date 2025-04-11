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
Command line interface für arestix.
"""

import datetime
import platform
import sys

from arestix.core import *
from arestix.core.action import ArestixAction
from arestix.core.config import config_root_path, LocalConfig
from arestix.core.messages import *
from arestix.core.arestix_exception import ArestixException
from arestix.core.restic_interface import execute_restic_command
from arestix.core.task import TaskMonitor
from arestix.core.util import current_user

_COMMAND_HELP_IDS = {CLI_COMMAND_BACKUP: T_CLI_HELP_BACKUP, CLI_COMMAND_CLEANUP: T_CLI_HELP_CLEANUP,
                     CLI_COMMAND_FIND: T_CLI_HELP_FIND, CLI_COMMAND_INIT: T_CLI_HELP_INIT,
                     CLI_COMMAND_LS: T_CLI_HELP_LS, CLI_COMMAND_RESTORE: T_CLI_HELP_RESTORE,
                     CLI_COMMAND_SNAPSHOTS: T_CLI_HELP_SHAPSHOTS}


def read_arestix_config_file(action: ArestixAction) -> LocalConfig:
    """
    Liest die arestix-Konfigurationsdatei und ersetzt darin enthaltene Variablen.
    :param action: die auszuführende Aktion
    :returns: arestix-Konfiguration.
    :raises RestixException: falls die Datei nicht verarbeitet werden kann
    """
    _vars = {CFG_VAR_HOST: platform.node(), CFG_VAR_USER: current_user(),
             CFG_VAR_YEAR: str(datetime.datetime.now().year)}
    _host_opt = action.option(OPTION_HOST)
    if _host_opt is not None:
        _vars[CFG_VAR_HOST] = _host_opt
    _year_opt = action.option(OPTION_YEAR)
    if _year_opt is not None:
        _vars[CFG_VAR_YEAR] = _year_opt
    _local_config = LocalConfig.from_file(os.path.join(config_root_path(), ARESTIX_CONFIG_FN))
    return _local_config.for_cli(_vars)


def prompt_confirmation(action: ArestixAction) -> bool:
    """
    Verlangt vom Benutzer eine Bestätigung der Aktion. Falls einer der Optionen --batch oder --dry-run gesetzt sind
    oder die Aktion keine Datenänderung bewirkt, ist keine Bestätigung nötig.
    :param action: die auszuführende Aktion.
    :returns: True, falls die Aktion bestätigt wurde; ansonsten False
    """
    _base_action = action.action_id()
    if (_base_action == ACTION_SNAPSHOTS or _base_action == ACTION_LS or
            _base_action == ACTION_FIND or action.option(OPTION_BATCH) or action.option(OPTION_DRY_RUN)):
        return True
    _target_alias = action.target_alias()
    if _base_action == ACTION_BACKUP:
        print(localized_message(T_CLI_CONFIRM_BACKUP, _target_alias))
    elif _base_action == ACTION_INIT:
        print(localized_message(T_CLI_CONFIRM_INIT, _target_alias))
    elif _base_action == ACTION_FORGET:
        print(localized_message(T_CLI_CONFIRM_CLEANUP, _target_alias))
    elif _base_action == ACTION_RESTORE:
        _snapshot_id = action.option(OPTION_SNAPSHOT)
        if _snapshot_id is None:
            _snapshot_id = RESTIC_SNAPSHOT_LATEST
        _restore_path = action.option(OPTION_RESTORE_PATH)
        if _restore_path is None:
            _restore_path = os.sep
        print(localized_message(T_CLI_CONFIRM_RESTORE, _snapshot_id, _restore_path, _target_alias))
    else:
        # unbekannte Aktion
        return False
    ch = input(localized_label(T_CLI_PROMPT_FOR_CONFIRMATION))
    return ch.lower() == localized_label(T_CLI_YES_CHAR)


def show_help(cmd: str = None):
    """
    Zeigt Hilfe über arestix oder einen speziellen Befehl an.
    :param cmd: optional der Befehl, über den Hilfe angezeigt werden soll
    """
    if cmd is None or cmd not in _COMMAND_HELP_IDS:
        print(localized_message(T_CLI_USAGE_INFO))
        return
    print(localized_message(_COMMAND_HELP_IDS[cmd]))


def show_targets(targets: dict):
    """
    Zeigt die in der arestix-Konfiguration definierten Backup-Ziele an.
    :param targets: die Backup-Ziele aus der arestix-Konfiguration
    """
    print()
    print(localized_message(T_CLI_BACKUP_TARGETS_HEADER))
    for _target in targets.values():
        print(localized_message(T_CLI_BACKUP_TARGET_INFO, _target[CFG_PAR_ALIAS], _target[CFG_PAR_COMMENT]))
    print()


def cli_main():
    """
    Hauptprogramm für die Kommandozeile.
    """
    try:
        # interne Aktion aus den Daten der Kommandozeile erzeugen
        _action = ArestixAction.from_command_line(sys.argv[1:])
        if _action.action_id() == ACTION_HELP:
            show_help(_action.option(OPTION_HELP))
            sys.exit(0)
    except ArestixException as _e:
        print(str(_e))
        show_help()
        sys.exit(1)
    try:
        # arestix-Konfiguration einlesen
        _restix_config = read_arestix_config_file(_action)
        if _action.action_id() == CLI_COMMAND_TARGETS:
            # Sonderfall Backup-Ziele anzeigen (resultiert nicht in einem restic-Befehl)
            show_targets(_restix_config.targets())
            sys.exit(0)
        # Repository und Zugangsdaten in die Aktion eintragen
        _target_alias = _action.target_alias()
        _action.set_basic_options(_restix_config, None)
        if _action.action_id() == ACTION_BACKUP:
            _action.set_scope_options(_restix_config.scope_for_target(_target_alias))
        # Aktion ausführen
        _action.verify_mandatory_options()
        if prompt_confirmation(_action):
            execute_restic_command(_action.to_restic_command(), TaskMonitor())
    except Exception as _e:
        print(localized_message(E_CLI_ARESTIX_COMMAND_FAILED))
        print(f'> {_e}')
        print()


if __name__ == "__main__":
    cli_main()
