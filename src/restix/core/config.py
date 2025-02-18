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
Issai runtime configuration.
The framework is configured by files located under Issai configuration directory. This directory
can be specified in environment variable ISSAI_CONFIG_PATH, it defaults to $HOME/.config/issai.
If there is a file named master.toml, it is considered as master configuration for all products.
For each product, there must be a subdirectory with the Issai product name and inside the subdirectory
a file product.toml containing product specific configuration.
During test execution, the configuration may be updated from attachment files contained in test plans
or test cases.
"""

import os.path
import re

import tomli

from restix.core import *
from restix.core.restix_exception import RestixException
from restix.core.messages import *
from restix.core.util import full_path_of


class LocalConfig(dict):
    """
    Lokale restix-Konfiguration.
    """
    def __init__(self, toml_data, file_path, warnings):
        """
        Konstruktor.
        :param dict toml_data: geparste Daten aus der Konfigurationsdatei
        :param str file_path: Name der Konfigurationsdatei mit vollständigem Pfad
        :param list[str] warnings: Warnungen aus Konsistenzprüfung
        """
        super().__init__()
        self.__file_path = file_path
        self.__warnings = warnings
        self.update(toml_data.items())

    def warnings(self):
        """
        :returns: lokalisierte Warnungen vom Parsen der Konfigurationsdatei
        :rtype: list[str]
        """
        return self.__warnings

    @staticmethod
    def from_file(file_path):
        """
        Erzeugt die lokale restix-Konfiguration aus einer TOML-Datei.
        :param str file_path: Name der Konfigurationsdatei mit vollständigem Pfad
        :returns: lokale restix-Konfiguration
        :rtype: LocalConfig
        :raises RestixException: falls die Datei nicht gelesen werden kann
        """
        _file_contents = ''
        _file_path = os.path.abspath(file_path)
        try:
            with open(_file_path, 'r') as _f:
                _file_contents = _f.read()
        except Exception as e:
            raise RestixException(E_CFG_READ_FILE_FAILED, _file_path, e)
        return LocalConfig.from_str(_file_contents, _file_path)

    @staticmethod
    def from_str(data, file_path):
        """
        Erzeugt die lokale restix-Konfiguration aus einem TOML-String.
        :param str data: die TOML-Daten
        :param str file_path: Name der Konfigurationsdatei mit vollständigem Pfad
        :returns: lokale Konfiguration
        :rtype: LocalConfig
        :raises RestixException: falls der String nicht verarbeitet werden kann
        """
        try:
            _toml_data = tomli.loads(data)
            _warnings = validate_config(_toml_data, file_path)
            _cfg = LocalConfig(_toml_data, file_path, _warnings)
            return _cfg
        except Exception as e:
            raise RestixException(E_CFG_READ_FILE_FAILED, file_path, e)


def config_root_path():
    """
    Gibt das Wurzelverzeichnis der restix-Konfiguration zurück.
    Falls die Umgebungsvariable RESTIX_CONFIG_PATH definiert und ein Verzeichnis ist, wird dieses Verzeichnis
    zurückgegeben. Ansonsten wird das Standardverzeichnis '.config/restix' im Home-Verzeichnis des Users zurückgegeben.
    :returns: Wurzelverzeichnis der restix-Konfiguration
    :rtype: str
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


def create_config_root():
    """
    Creates root directory for Issai configuration and a default master configuration file.
    If defined, directory path is taken from environment variable ISSAI_CONFIG_PATH,
    otherwise creates default directory $HOME/.config/issai.
    :returns: full path of configuration root directory
    :rtype: str
    """
    _config_path = os.environ.get(ENVA_RESTIX_CONFIG_PATH)
    if _config_path is None:
        _config_path = os.path.join(os.path.expanduser('~'), RESTIX_CONFIG_SUBDIR)
    _config_path = full_path_of(_config_path)
    os.makedirs(_config_path, 0o755, True)
    return _config_path


def validate_config(data, file_path):
    """
    Prüft, ob eine restix-Konfiguration gültig ist.
    :param dict data: die TOML-Daten der Konfiguration
    :param str file_path: Name der Konfigurationsdatei mit vollständigem Pfad
    :returns: lokalisierte Warnungen
    :rtype: list[str]
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
        check_element_type(_grp_name, 'a', _grp_value, _file_name)
        for _i, _elem_value in enumerate(_grp_value):
            _elem_name = f'{_grp_name}.[{_i}]'
            _unsupported_items.extend(check_element(_elem_name, _elem_value, _grp_desc, _file_name))
    for _mandatory_grp in _META_ROOT.keys():
        if _mandatory_grp not in data.keys():
            raise RestixException(E_CFG_MANDATORY_GRP_MISSING, _mandatory_grp)
    _warnings = [localized_message(W_CFG_ELEM_IGNORED, _elem) for _elem in _unsupported_items]
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


def mandatory_groups():
    """
    :returns: Namen aller in einer restix-Konfiguration notwendigen Groups
    :rtype: list[str]
    """
    return [_k for _k, _v in _META_ROOT.items() if _v[1]]


def mandatory_parameter(group_name):
    """
    :returns: Namen aller in einer Group notwendigen Parameter
    :rtype: list[str]
    """
    _group_meta = _META_ROOT[group_name][2]
    return [_k for _k, _v in _group_meta.items() if _v[1]]


def check_element(qualified_element_name, element_value, element_desc, file_name):
    """
    Prüft ein Element der Konfigurationsdatei.
    :param qualified_element_name: Qualifizierter Name des Elements
    :param element_value: Wert des Elements
    :param element_desc: Beschreibung für alle Unter-Elemente
    :param file_name: Name der Konfigurationsdatei
    :return: nicht unterstützte Elemente
    :rtype: list[str]
    :raises RestixException: wenn das Element nicht verarbeitet werden kann
    """
    _expected_element_type = element_desc[0]
    check_element_type(qualified_element_name, _expected_element_type, element_value, file_name)
    _unsupported_elements = []
    if _expected_element_type == 's':
        _vars = re.findall(r'\$\{([A-Z_])}', element_value.upper())
        for _var in _vars:
            if _var not in CONFIG_VARIABLES:
                raise RestixException(E_CFG_INVALID_VARIABLE, _var)
    elif _expected_element_type == 't':
        # dict
        for _k, _v in element_value.items():
            _sub_element_name = f'{qualified_element_name}.{_k}'
            _sub_element_desc = element_desc[2].get(_k)
            if _sub_element_desc is None:
                # nicht unterstütztes Element
                _unsupported_elements.append(_sub_element_name)
                continue
            _unsupported_elements.extend(check_element(_sub_element_name, _v, _sub_element_desc, file_name))
            # prüfen, ob alle notwendigen Unter-Elemente definiert wurden
            _mandatory_sub_elements = [_k for _k, _v in element_desc[2].items() if _v[1]]
            for _k in _mandatory_sub_elements:
                if _k not in element_value.keys():
                    raise RestixException(E_CFG_MANDATORY_ELEM_MISSING, qualified_element_name, _k)
    return _unsupported_elements


def check_element_type(element_name, expected_type, par_value, file_name):
    """
    Prüft den Typ eines Elements (Group oder Parameter) der Konfigurationsdatei.
    :param element_name: Qualifizierter Name des Elements
    :param expected_type: erwarteter TOML-Typ (a für Array, s für String, t für Table)
    :param par_value: Wert des Elements
    :param file_name: Name der Konfigurationsdatei
    :raises RestixException: falls das Element nicht den erwarteten Typ hat
    """
    if expected_type == 's':
        # string
        if type(par_value) is not str:
            raise RestixException(E_CFG_INVALID_ELEM_TYPE, element_name, 'string', file_name)
        return
    if expected_type == 't':
        # table
        if type(par_value) is not dict:
            raise RestixException(E_CFG_INVALID_ELEM_TYPE, element_name, 'table', file_name)
        return
    if expected_type == 'a':
        # array
        if type(par_value) is not list:
            raise RestixException(E_CFG_INVALID_ELEM_TYPE, element_name, 'array', file_name)
        return
    _reason = localized_message(E_CFG_META_DESC_MISSING, expected_type)
    raise RestixException(E_INTERNAL_ERROR, _reason)


# Pattern für Variablen im String-Wert von Parametern
TOML_VAR_PATTERN = re.compile(r'\$\{(.*?)}')

# Beschreibung der Parameter in der TOML-Datei: (Python-Typ, Mandatory, ggf. Beschreibung der Elemente)
_META_ACCESS_RIGHTS = {CFG_PAR_HOST: ('s', True, None),
                       CFG_PAR_USER: ('s', True, None),
                       CFG_PAR_YEAR: ('s', True, None)}
_META_CREDENTIALS = {CFG_PAR_COMMENT: ('s', False, None),
                     CFG_PAR_NAME: ('s', True, None),
                     CFG_PAR_TYPE: ('s', True, None),
                     CFG_PAR_VALUE: ('s', False, None)}
_META_SCOPE = {CFG_PAR_COMMENT: ('s', False, None),
               CFG_PAR_EXCLUDES: ('s', False, None),
               CFG_PAR_IGNORES: ('s', False, None),
               CFG_PAR_INCLUDES: ('s', True, None),
               CFG_PAR_NAME: ('s', True, None)}
_META_TARGET = {CFG_PAR_ALIAS: ('s', True, None),
                CFG_PAR_COMMENT: ('s', False, None),
                CFG_PAR_CREDENTIALS: ('s', True, None),
                CFG_PAR_LOCATION: ('s', True, None),
                CFG_PAR_SCOPE: ('s', True, None),
                CFG_PAR_ACCESS_RIGHTS: ('t', False, _META_ACCESS_RIGHTS)}
_META_ROOT = {CFG_GROUP_CREDENTIALS: ('t', True, _META_CREDENTIALS),
              CFG_GROUP_SCOPE: ('t', True, _META_SCOPE),
              CFG_GROUP_TARGET: ('t', True, _META_TARGET)}

# Erlaubte Werte für den Credentials-Typ
_META_CREDENTIAL_TYPES = {CFG_VALUE_CREDENTIALS_TYPE_FILE, CFG_VALUE_CREDENTIALS_TYPE_PROMPT,
                          CFG_VALUE_CREDENTIALS_TYPE_TEXT, CFG_VALUE_CREDENTIALS_TYPE_TOKEN}

# Erlaubte Variablen in der Konfigurationsdatei
CONFIG_VARIABLES = {'HOST', 'USER', 'YEAR'}
