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
Lokale restix-Konfiguration.
Die Konfiguration erfolgt durch Dateien im Konfigurationsverzeichnis $HOME/.config/restix.
Alternativ kann das Verzeichnis durch Umgebungsvariable RESTIX_CONFIG_PATH festgelegt werden.
"""

import copy
import os.path
import pathlib
import re
import shutil

import tomli
import tomli_w

from restix.core import *
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.util import current_user, full_path_of


class LocalConfig(dict):
    """
    Lokale restix-Konfiguration.
    """
    def __init__(self, toml_data: dict, file_path: str, warnings: list[str]):
        """
        Konstruktor.
        :param toml_data: geparste Daten aus der Konfigurationsdatei
        :param file_path: Name der Konfigurationsdatei mit vollständigem Pfad
        :param warnings: Warnungen aus Konsistenzprüfung
        """
        super().__init__()
        self.__file_path = file_path
        self.__warnings = warnings
        self.update(toml_data.items())

    def path(self) -> str:
        """
        :returns: Verzeichnis der restix-Konfiguration inklusive Pfad
        """
        return os.path.dirname(self.__file_path)

    def warnings(self) -> list[str]:
        """
        :returns: lokalisierte Warnungen vom Auswerten der Konfigurationsdatei
        """
        return self.__warnings

    def credentials(self) -> dict:
        """
        :returns: alle definierten Zugangsdaten, sortiert nach Name
        """
        return self._group(CFG_GROUP_CREDENTIALS)

    def scopes(self) -> dict:
        """
        :returns: alle definierten Backup-Umfänge, sortiert nach Name
        """
        return self._group(CFG_GROUP_SCOPE)

    def repo_for_target(self, alias: str) -> str:
        """
        :param alias: Aliasname des Backup-Ziels
        :returns: Repository-Location für das angegebene Backup-Ziel
        """
        return self.targets().get(alias).get(CFG_PAR_LOCATION)

    def credentials_for_target(self, alias: str) -> dict:
        """
        :param alias: Aliasname des Backup-Ziels
        :returns: Zugangsdaten für das angegebene Backup-Ziel
        """
        _target = self.targets().get(alias)
        return self.credentials().get(_target.get(CFG_PAR_CREDENTIALS))

    def scope_for_target(self, alias: str) -> dict:
        """
        :param alias: Aliasname des Backup-Ziels
        :returns: Backup-Umfang für das angegebene Backup-Ziel
        """
        _target = self.targets().get(alias)
        return self.scopes().get(_target.get(CFG_PAR_SCOPE))

    def targets(self) -> dict:
        """
        :returns: alle definierten Backup-Ziele, sortiert nach Name
        """
        return self._group(CFG_GROUP_TARGET)

    def pre_check_remove(self, group: str, alias: str):
        """
        Prüft, ob ein Element gelöscht werden kann.
        :param group: Group des Elements
        :param alias: Aliasname des Elements.
        :raises RestixException: falls das Element nicht gelöscht werden darf
        """
        if group == CFG_GROUP_TARGET:
            # Backup-Ziele haben keine Abhängigkeiten
            return
        # Backup-Umfang oder Zugriffsdaten
        # hier muss geprüft werden, ob sie in einem Backup-Ziel referenziert werden
        for _target in self[CFG_GROUP_TARGET]:
            if _target.get(group) == alias:
                raise RestixException(E_ALIAS_REFERENCED, alias)

    def pre_check_rename(self, group: str, old_alias: str, new_alias: str):
        """
        Prüft, ob ein Element umbenannt werden kann.
        :param group: Group des Elements
        :param old_alias: alter Aliasname des Elements
        :param new_alias: neuer Aliasname des Elements.
        :raises RestixException: falls das Element nicht umbenannt werden darf
        """
        if len(new_alias) == 0:
            # Leerstring als neuer Aliasname ist nie erlaubt
            raise RestixException(E_ALIAS_NAME_EMPTY)
        if old_alias == new_alias:
            # gleicher Name hat keinen Effekt, muss vom Aufrufer abgefangen werden
            return
        if new_alias in self._group(group).keys():
            # neuer Name wird schon verwendet
            raise RestixException(E_ALIAS_NAME_ALREADY_USED, new_alias)

    def element_renamed(self, group: str, old_alias: str, new_alias: str):
        """
        Passt die in Backup-Zielen referenzierten Elemente aufgrund einer Umbenennung an.
        :param group: Group, in dem sich das umbenannte Element befindet
        :param old_alias: alter Aliasname der Zugriffsdaten
        :param new_alias: neuer Aliasname der Zugriffsdaten
        """
        for _target in self[CFG_GROUP_TARGET].values():
            if _target.get(group) == old_alias:
                _target[group] = new_alias

    def for_cli(self, variables: dict):
        """
        :param variables: Namen und Werte der zu ersetzenden Variablen
        :returns: Kopie der Konfiguration mit ersetzten Variablen
        """
        _config = copy.deepcopy(self)
        LocalConfig.replace_variables(_config, variables)
        return _config

    def has_warnings(self) -> bool:
        """
        Zeigt an, ob beim Parsen der Konfiguration aus den TOML-Daten Warnungen aufgetreten sind.
        :returns: True, falls Warnungen vorliegen
        """
        return len(self.__warnings) > 0

    def to_file(self, file_path: str = None):
        """
        Speichert die Konfiguration in Datei.
        Überschreibt den Inhalt, falls die Datei bereits existiert.
        :param file_path: Dateiname; bei None wird der Dateiname vom öffnen benutzt.
        :raises RestixException: falls das Speichern fehlschlägt
        """
        _output_file_path = self.__file_path if file_path is None else file_path
        if _output_file_path is None:
            raise RestixException(E_FILE_NAME_MISSING)
        try:
            with open(_output_file_path, 'wb') as _f:
                tomli_w.dump(self, _f)
        except IOError | OSError as _e:
            raise RestixException(E_WRITE_FILE_FAILED, _output_file_path, str(_e))

    def _group(self, group_name: str) -> dict:
        """
        :param group_name: gewünschte Group
        :returns: alle definierten Elemente der übergebenen Group, sortiert nach Aliasname
        """
        _elements = {}
        for _element in self[group_name]:
            _elements[_element[CFG_PAR_ALIAS]] = _element
        return dict(sorted(_elements.items()))

    @classmethod
    def from_file(cls: Self, file_path: str) -> Self:
        """
        Erzeugt die lokale restix-Konfiguration aus einer TOML-Datei.
        :param file_path: Name der Konfigurationsdatei mit vollständigem Pfad
        :returns: lokale restix-Konfiguration.
        :raises RestixException: falls die Datei nicht gelesen oder verarbeitet werden kann
        """
        _file_contents = ''
        _file_path = os.path.abspath(file_path)
        try:
            with open(_file_path, 'r') as _f:
                _file_contents = _f.read()
        except Exception as e:
            raise RestixException(E_CFG_READ_FILE_FAILED, _file_path, e)
        return LocalConfig.from_str(_file_contents, _file_path)

    @classmethod
    def from_str(cls: Self, data: str, file_path: str) -> Self:
        """
        Erzeugt die lokale restix-Konfiguration aus einem TOML-String.
        :param data: TOML-Daten
        :param file_path: Name der Konfigurationsdatei mit vollständigem Pfad
        :returns: lokale restix-Konfiguration.
        :raises RestixException: falls der String nicht verarbeitet werden kann
        """
        try:
            _toml_data = tomli.loads(data)
            _warnings = validate_config(_toml_data, file_path)
            _cfg = LocalConfig(_toml_data, file_path, _warnings)
            return _cfg
        except Exception as e:
            raise RestixException(E_CFG_READ_FILE_FAILED, file_path, e)

    @classmethod
    def replace_variables(cls: Self, element: dict|list|str, variables: dict) -> dict|list|str:
        """
        Ersetzt Variablen in String-Werten des Elements
        :param element: Element
        :param variables: zu ersetzende Variablen
        :returns: Element, in dem alle Vorkommen der Variablen durch ihre Werte ersetzt wurden
        """
        if type(element) is str:
            for _var_name, _var_value in variables.items():
                _search_str = f'${{{_var_name}}}'
                element = element.replace(_search_str, _var_value)
        elif issubclass(element.__class__, dict):
            for _item_name, _item_value in element.items():
                element[_item_name] = LocalConfig.replace_variables(_item_value, variables)
        elif type(element) is list:
            for _i, _item in enumerate(element):
                element[_i] = LocalConfig.replace_variables(_item, variables)
        return element


def config_root_path() -> str:
    """
    Gibt das Wurzelverzeichnis der restix-Konfiguration zurück.
    Falls die Umgebungsvariable RESTIX_CONFIG_PATH definiert und ein Verzeichnis ist, wird dieses Verzeichnis
    zurückgegeben. Ansonsten wird das Standardverzeichnis '.config/restix' im Home-Verzeichnis des Users zurückgegeben.
    :returns: Wurzelverzeichnis der restix-Konfiguration
    :raises RestixException: Umgebungsvariable RESTIX_CONFIG_PATH ist definiert, aber kein Verzeichnis,
                             oder Umgebungsvariable RESTIX_CONFIG_PATH ist **nicht** definiert und das
                             Standardverzeichnis existiert nicht
    """
    _config_path = os.environ.get(ENVA_RESTIX_CONFIG_PATH)
    if _config_path is not None:
        _config_path = full_path_of(_config_path)
        if not os.path.isdir(_config_path):
            raise RestixException(E_CFG_CUSTOM_CONFIG_ROOT_NOT_FOUND, _config_path, ENVA_RESTIX_CONFIG_PATH)
        return _config_path
    _home_dir = os.path.expanduser('~')
    _config_path = os.path.join(_home_dir, *RESTIX_CONFIG_SUBDIR)
    if not os.path.isdir(_config_path):
        raise RestixException(E_CFG_DEFAULT_CONFIG_ROOT_NOT_FOUND, _config_path)
    return _config_path


def create_config_root() -> str:
    """
    Erzeugt das restix-Konfigurationsverzeichnis.
    Falls Umgebungsvariable RESTIX_CONFIG_PATH gesetzt ist, wird dieses als Verzeichnisname benutzt, ansonsten wird
    das Verzeichnis $HOME/.config/restix erzeugt.
    :returns: restix-Konfigurationsverzeichnis mit vollständigem Pfad.
    :raises RestixException: falls das Erstellen fehlschlägt
    """
    _config_path = os.environ.get(ENVA_RESTIX_CONFIG_PATH)
    if _config_path is None:
        _config_path = os.path.join(os.path.expanduser('~'), *RESTIX_CONFIG_SUBDIR)
    _config_path = full_path_of(_config_path)
    try:
        os.makedirs(_config_path, 0o755, True)
        _source_path = pathlib.Path(__file__).parent.resolve()
        _templates_path = os.path.abspath(os.path.join(_source_path, '..', RESTIX_TEMPLATES_DIR))
        shutil.copy(os.path.join(_templates_path, RESTIX_CONFIG_FN), _config_path)
        with open(os.path.join(_templates_path, RESTIX_DEFAULT_INCLUDES_FN), 'r') as _includes_template:
            _contents = _includes_template.read()
            _contents = _contents.replace(f'${{{CFG_VAR_USER}}}', current_user())
            with open(os.path.join(_config_path, RESTIX_DEFAULT_INCLUDES_FN), 'w') as _default_includes_file:
                _default_includes_file.write(_contents)
    except OSError as _e:
        raise RestixException(E_CFG_CREATE_CONFIG_ROOT_FAILED, _config_path, str(_e))
    return _config_path


def validate_config(data: dict, file_path: str) -> list[str]:
    """
    Prüft, ob eine restix-Konfiguration gültig ist.
    :param data: TOML-Daten der Konfiguration
    :param file_path: Name der Konfigurationsdatei mit vollständigem Pfad
    :returns: lokalisierte Warnungen.
    :raises RestixException: falls in der Konfiguration ein Element mit falschem Typ definiert ist, ein notwendiges
     Element fehlt oder in einem String-Wert eine nicht unterstützte Variable verwendet wird
    """
    _unsupported_items = []
    _file_name = os.path.basename(file_path)
    # Name und Typ aller Elemente der Konfigurationsdatei prüfen
    for _grp_name, _grp_value in data.items():
        _grp_desc = _META_ROOT.get(_grp_name)
        if _grp_desc is None:
            _unsupported_items.append(_grp_name)
            continue
        check_element_type(_grp_name, 'at', _grp_value, _file_name)
        for _i, _elem_value in enumerate(_grp_value):
            _elem_name = f'{_grp_name}.[{_i}]'
            _unsupported_items.extend(check_element(_elem_name, _elem_value, _grp_desc, _file_name))
    # Prüfen, ob alle notwendigen Elemente definiert wurden
    for _mandatory_grp in _META_ROOT.keys():
        if _mandatory_grp not in data.keys():
            raise RestixException(E_CFG_MANDATORY_GRP_MISSING, _mandatory_grp, _file_name)
    _warnings = [localized_message(W_CFG_ELEM_IGNORED, _elem) for _elem in _unsupported_items]
    # Prüfen, ob es mehrfach definierte Groups oder ungültige Referenzen gibt
    _groups = extract_groups(data, file_path)
    for _target_alias, _target_data in _groups.get(CFG_GROUP_TARGET).items():
        if _target_data[CFG_PAR_SCOPE] not in _groups.get(CFG_GROUP_SCOPE).keys():
            raise RestixException(E_CFG_INVALID_SCOPE_REF, _target_alias, _target_data[CFG_PAR_SCOPE], _file_name)
        if _target_data[CFG_PAR_CREDENTIALS] not in _groups.get(CFG_GROUP_CREDENTIALS).keys():
            raise RestixException(E_CFG_INVALID_CREDENTIALS_REF, _target_alias,
                                  _target_data[CFG_PAR_CREDENTIALS], _file_name)
    # nicht unterstützte Elemente aus der Konfiguration entfernen
    for _item in _unsupported_items:
        _dot_pos = _item.rfind('.')
        if _dot_pos < 0:
            del data[_item]
        else:
            _parent_name = _item[:_dot_pos].split('.')
            _parent = data
            for _e in _parent_name:
                if _e.startswith('['):
                    _index = int(_e[1:-1])
                    _parent = _parent[_index]
                else:
                    _parent = _parent.get(_e)
            _element = _item[_dot_pos+1:]
            del _parent[_element]
    return _warnings


def check_element(qualified_element_name: str, element_value: dict|list|str, element_desc: tuple,
                  file_name: str) -> list[str]:
    """
    Prüft ein Element der Konfigurationsdatei.
    :param qualified_element_name: Qualifizierter Name des Elements
    :param element_value: Wert des Elements
    :param element_desc: Beschreibung für alle Unter-Elemente
    :param file_name: Name der Konfigurationsdatei ohne Pfadangabe
    :returns: nicht unterstützte Elemente.
    :raises RestixException: falls das Element nicht verarbeitet werden kann
    """
    _expected_element_type = element_desc[0]
    check_element_type(qualified_element_name, _expected_element_type, element_value, file_name)
    _unsupported_elements = []
    if _expected_element_type == 's':
        _vars = re.findall(r'\$\{([A-Z_])}', element_value.upper())
        for _var in _vars:
            if _var not in CFG_VARS:
                raise RestixException(E_CFG_INVALID_VARIABLE, _var)
    elif _expected_element_type == 't':
        # dict
        for _sub_element_name, _sub_element_value in element_value.items():
            _qualified_sub_element_name = f'{qualified_element_name}.{_sub_element_name}'
            _sub_element_desc = element_desc[1].get(_sub_element_name)
            if _sub_element_desc is None:
                # nicht unterstütztes Element
                _unsupported_elements.append(_qualified_sub_element_name)
                continue
            _unsupported_elements.extend(check_element(_qualified_sub_element_name, _sub_element_value,
                                                       _sub_element_desc, file_name))
        # prüfen, ob alle notwendigen Unter-Elemente definiert wurden
        _mandatory_sub_elements = [_k for _k, _v in element_desc[1].items() if _v[3]]
        for _k in _mandatory_sub_elements:
            if _k not in element_value.keys():
                # auf bedingte Notwendigkeit prüfen
                _condition_desc = element_desc[1][_k][4]
                if _condition_desc is not None:
                    _ref_par_name = _condition_desc[0]
                    _ref_par_values = _condition_desc[1]
                    _actual_value = element_value.get(_ref_par_name)
                    if _actual_value not in _ref_par_values:
                        continue
                raise RestixException(E_CFG_MANDATORY_ELEM_MISSING, qualified_element_name, _k)
    return _unsupported_elements


def check_element_type(element_name: str, expected_type: str, par_value: dict|list|str,
                       file_name: str):
    """
    Prüft den Typ eines Elements (Group oder Parameter) der Konfigurationsdatei.
    :param element_name: Qualifizierter Name des Elements
    :param expected_type: erwarteter TOML-Typ (a für Array, s für String, t für Table)
    :param par_value: Wert des Elements
    :param file_name: Name der Konfigurationsdatei ohne Pfad.
    :raises RestixException: falls das Element nicht den erwarteten Typ oder Wert hat
    """
    if expected_type.startswith('s'):
        # string
        if type(par_value) is not str:
            raise RestixException(E_CFG_INVALID_ELEM_TYPE, element_name, 'string', file_name)
        if expected_type.find(':') > 0:
            _allowed_values = expected_type[2:].split(',')
            if par_value.lower() not in _allowed_values:
                raise RestixException(E_CFG_INVALID_ELEM_VALUE, element_name, expected_type[2:], file_name)
        return
    if expected_type == 't':
        # table
        if type(par_value) is not dict:
            raise RestixException(E_CFG_INVALID_ELEM_TYPE, element_name, 'table', file_name)
        return
    if expected_type.startswith('a'):
        # array
        if type(par_value) is not list:
            raise RestixException(E_CFG_INVALID_ELEM_TYPE, element_name, 'array', file_name)
        for _i, _item_value in enumerate(par_value):
            _item_name = f'{element_name}.[{_i}]'
            check_element_type(_item_name, expected_type[1:], _item_value, file_name)
        return
    _reason = localized_message(E_CFG_META_DESC_MISSING, expected_type)
    raise RestixException(E_INTERNAL_ERROR, _reason)


def extract_groups(data: dict, file_path: str) -> dict:
    """
    Liest die Groups aus den übergebenen TOML-Daten.
    :param data: TOML-Daten der Konfiguration
    :param file_path: Name der Konfigurationsdatei mit vollständigem Pfad
    :returns: Name und Daten aller Groups.
    :raises RestixException: falls es Groups mit gleichem Namen gibt
    """
    _file_name = os.path.basename(file_path)
    _groups = {}
    for _grp_name, _grp_value in data.items():
        _grp_desc = _META_ROOT.get(_grp_name)
        if _grp_desc is None:
            continue
        _element_names = set()
        _groups[_grp_name] = {}
        for _grp_item in _grp_value:
            for _element_attr, _element_value in _grp_item.items():
                _attr_desc = _grp_desc[1].get(_element_attr)
                if _attr_desc is None:
                    continue
                if _attr_desc[2]:
                    if _element_value in _element_names:
                        raise RestixException(E_CFG_DUPLICATE_GROUP, _grp_name, _element_value, _file_name)
                    _element_names.add(_element_value)
                    _groups[_grp_name][_element_value] = _grp_item
    return _groups


# Pattern für Variablen im String-Wert von Parametern
TOML_VAR_PATTERN = re.compile(r'\$\{(.*?)}')

# Erlaubte Werte für den Credentials-Typ
_ALLOWED_CREDENTIAL_TYPES = (CFG_VALUE_CREDENTIALS_TYPE_FILE, CFG_VALUE_CREDENTIALS_TYPE_PROMPT,
                             CFG_VALUE_CREDENTIALS_TYPE_TEXT, CFG_VALUE_CREDENTIALS_TYPE_PGP)

# Credentials-Typen, die einen Wert benötigen
_VALUED_CREDENTIAL_TYPES = (CFG_VALUE_CREDENTIALS_TYPE_FILE, CFG_VALUE_CREDENTIALS_TYPE_TEXT)

# Beschreibung der Parameter in der TOML-Datei:
# ([0] Typ, [1] Beschreibung der Elemente, [2] unique, [3] mandatory, [4] Bedingung für Mandatory)
_META_CREDENTIALS = {CFG_PAR_COMMENT: ('s', None, False, False, None),
                     CFG_PAR_ALIAS: ('s', None, True, True, None),
                     CFG_PAR_TYPE: (f's:{",".join(_ALLOWED_CREDENTIAL_TYPES)}', None, False, True, None),
                     CFG_PAR_VALUE: ('s', None, False, True, (CFG_PAR_TYPE, _VALUED_CREDENTIAL_TYPES))}
_META_SCOPE = {CFG_PAR_COMMENT: ('s', None, False, False, None),
               CFG_PAR_EXCLUDES: ('s', None, False, False, None),
               CFG_PAR_IGNORES: ('as', None, False, False, None),
               CFG_PAR_INCLUDES: ('s', None, False, True, None),
               CFG_PAR_ALIAS: ('s', None, True, True, None)}
_META_TARGET = {CFG_PAR_ALIAS: ('s', None, True, True, None),
                CFG_PAR_COMMENT: ('s', None, False, None),
                CFG_PAR_CREDENTIALS: ('s', None, False, True, None),
                CFG_PAR_LOCATION: ('s', None, False, True, None),
                CFG_PAR_SCOPE: ('s', None, False, True, None)}
_META_ROOT = {CFG_GROUP_CREDENTIALS: ('t', _META_CREDENTIALS, False, True, None),
              CFG_GROUP_SCOPE: ('t', _META_SCOPE, False, True, None),
              CFG_GROUP_TARGET: ('t', _META_TARGET, False, True, None)}
