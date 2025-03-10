# Script für Backup und Restore mit restic.
#
# Die Einstellungen sind in der Konfigurationsdatei config.toml hinterlegt,
# in $HOME/.config/restic auf Linux, in %LOCALAPPDATA%/restic auf Windows.
# In der Konfigurationsdatei werden Umfänge (Scopes) definiert, die die
# zu sichernden Verzeichnisse und Dateien enthalten.
# Dort werden auch die Ziele (Targets) fürs Backup definiert, wie z.B.
# externe Festplatte oder Remote-Server.
#
# Bei Remote-Servern erfolgt die Übertragung per sftp, hier muss ein passender
# Alias in die ssh-Client-Konfigurationsdatei eingetragen werden.
#
# Aufruf: restix.py [options] action [target]
#           Options: -b | --batch
#                    -d Verzeichnis | --dest Verzeichnis (nur Restore)
#                    --host Hostname (nur Restore)
#                    -s Snapshot-Nummer | --snapshot Snapshot-Nummer (nur Restore)
#                    -y Jahr | --year Jahr
#
#           Actions: backup | init | restore | snapshots | targets
#           Target: Alias aus der Konfigurationsdatei

import datetime
import platform
import re
import shlex
import subprocess
import sys

from restix.core import *
from restix.core.action import RestixAction
from restix.core.config import config_root_path, LocalConfig
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.util import current_user


def read_restix_config_file(action: RestixAction) -> LocalConfig:
    """
    Liest die restix-Konfigurationsdatei und ersetzt darin enthaltene Variablen.
    :param action: die auszuführende Aktion
    :return: restix-Konfiguration.
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
    _local_config = LocalConfig.from_file(os.path.join(config_root_path(), RESTIX_CONFIG_FN))
    return _local_config.for_cli(_vars)


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
    pass
    '''
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
    '''


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
    raise RestixException(E_CLI_RESTIC_CMD_FAILED, ' '.join(cmd), localized_label(_reason))


def build_restic_cmd(restix_action, restic_info):
    """
    Creates restic command for specified restix action.
    :param DetailAction restix_action: restix action including options
    :param dict restic_info: additional information
    :return: restic command
    :rtype: list[str]
    :raises RestixException: if desired action is not implemented
    """
    return []
    '''
    _restic_cmd = ['restic', '-r', restic_info[RESTIX_TOML_KEY_REPO], '-p', restic_info[RESTIX_TOML_KEY_PW_FILE]]
    if restix_action.option(CLI_OPTION_DRY_RUN):
        _restic_cmd.append('--dry-run')
    _base_action = restix_action.base_action()
    if _base_action == RESTIC_COMMAND_BACKUP:
        _restic_cmd.append('--files-from')
        _restic_cmd.append(restic_info[RESTIX_TOML_KEY_INCLUDES])
        excl_fn = restic_info[RESTIX_TOML_KEY_EXCLUDES]
        if excl_fn:
            _restic_cmd.append('--exclude-file')
            _restic_cmd.append(excl_fn)
        _restic_cmd.append(_base_action)
        return _restic_cmd
    if _base_action == RESTIC_COMMAND_INIT or _base_action == RESTIC_COMMAND_SNAPSHOTS:
        _restic_cmd.append(_base_action)
        return _restic_cmd
    if _base_action == RESTIC_COMMAND_RESTORE:
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
    if _base_action == RESTIC_COMMAND_FORGET:
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
    if _base_action == RESTIC_COMMAND_TAG:
        _restic_cmd.append(_base_action)
        _restic_cmd.append('--set')
        _restic_cmd.append(restix_action.option(CLI_OPTION_TAGS))
        _restic_cmd.append(restix_action.option(CLI_OPTION_SNAPSHOT))
        return _restic_cmd
    raise RestixException(E_CLI_INVALID_ACTION, _base_action)
    '''


def prompt_confirmation(action: RestixAction) -> bool:
    """
    Verlangt vom Benutzer eine Bestätigung der Aktion. Falls einer der Optionen --batch oder --dry-run gesetzt sind
    oder die Aktion keine Datenänderung bewirkt, ist keine Bestätigung nötig.
    :param action: die auszuführende Aktion.
    :returns: True, falls die Aktion bestätigt wurde; ansonsten False
    """
    _base_action = action.action_id()
    if _base_action == RESTIC_COMMAND_SNAPSHOTS or action.option(OPTION_BATCH) or action.option(OPTION_DRY_RUN):
        return True
    _target_alias = action.target_alias()
    if _base_action == RESTIC_COMMAND_BACKUP:
        print(localized_message(T_CLI_CONFIRM_BACKUP, _target_alias))
    elif _base_action == RESTIC_COMMAND_INIT:
        print(localized_message(T_CLI_CONFIRM_INIT, _target_alias))
    elif _base_action == RESTIC_COMMAND_TAG:
        _tag = action.option(OPTION_TAG)
        _snapshot_id = action.option(OPTION_SNAPSHOT)
        print(localized_message(T_CLI_CONFIRM_TAG_SNAPSHOT, _snapshot_id, _target_alias, _tag))
    elif _base_action == RESTIC_COMMAND_FORGET:
        _snapshot_id = action.option(OPTION_SNAPSHOT)
        if _snapshot_id is None:
            print(localized_message(T_CLI_CONFIRM_FORGET_UNTAGGED, _target_alias))
        else:
            print(localized_message(T_CLI_CONFIRM_FORGET_SNAPSHOT, _snapshot_id, _target_alias))
    elif _base_action == RESTIC_COMMAND_RESTORE:
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
    Zeigt Hilfe über restix oder einen speziellen Befehl an.
    :param cmd: optional der Befehl, über den Hilfe angezeigt werden soll
    """
    if cmd is None or cmd not in ALL_CLI_COMMANDS:
        print(localized_message(T_CLI_USAGE_INFO))
        return


def show_targets(targets: dict):
    """
    Zeigt die in der restix-Konfiguration definierten Backup-Ziele an.
    :param targets: die Backup-Ziele aus der restix-Konfiguration
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
        _action = RestixAction.from_command_line(sys.argv[1:])
        if _action.action_id() == ACTION_HELP:
            show_help(_action.option(OPTION_HELP))
            print(localized_message(T_CLI_USAGE_INFO))
            sys.exit(0)
    except RestixException as _e:
        print(str(_e))
        show_help()
        sys.exit(1)
    try:
        # restix-Konfiguration einlesen
        _restix_config = read_restix_config_file(_action)
        if _action.action_id() == CLI_COMMAND_TARGETS:
            # Sonderfall Backup-Ziele anzeigen (resultiert nicht in einem restic-Befehl)
            show_targets(_restix_config.targets())
            sys.exit(0)
        # Aktion ausführen
        if prompt_confirmation(_action):
            execute_restic_command(_action.to_restic_command())
    except Exception as _e:
        print(localized_message(E_CLI_RESTIX_ACTION_FAILED))
        print(f'> {_e}')
        print()


if __name__ == "__main__":
    cli_main()
