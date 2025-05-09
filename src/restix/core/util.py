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
Hilfsfunktionen für restix.
"""

import os
import platform
import pwd
import re
import subprocess

from typing import NoReturn


# Defaultwerte
DEFAULT_LOCALE = 'de'

# Umgebungsvariablen
ENVA_LANG = 'LANG'
ENVA_LANGUAGE = 'LANGUAGE'

# Betriebssysteme
OS_LINUX = 'linux'
OS_WINDOWS = 'windows'


def full_path_of(path_spec: str) -> str:
    """
    :param path_spec: Pfadangabe
    :returns: vervollständigte Pfadangabe
    """
    if path_spec.startswith('~'):
        return os.path.expanduser(path_spec)
    return os.path.abspath(path_spec)


def relative_config_path_of(file_path: str, config_dir_path: str) -> str | None:
    """
    :param file_path: Dateiname
    :param config_dir_path: restix Konfigurationsverzeichnis
    :returns: Dateiname mit Pfad relativ zum Konfigurationsverzeichnis, falls möglich
    """
    if file_path is None:
        return None
    if os.path.isabs(file_path):
        # bei absolutem Pfad prüfen, ob die Datei im gegebenen Verzeichnis liegt
        _common_path = os.path.commonpath([file_path, config_dir_path])
        if len(_common_path) > 0:
            return file_path[len(_common_path) + len(os.sep):]
    # Dateiname hat schon relativen Pfad oder liegt nicht unterhalb des angegebenen Verzeichnisses
    return file_path


def full_config_path_of(file_path: str, config_dir_path: str) -> str | None:
    """
    :param file_path: Dateiname
    :param config_dir_path: restix Konfigurationsverzeichnis
    :returns: Dateiname mit absolutem Pfad
    """
    if file_path is None:
        return None
    if os.path.isabs(file_path):
        return file_path
    return os.path.join(config_dir_path, file_path)


def shell_cmd(cmd: list[str], runtime_env: dict = None) -> tuple[int, str, str]:
    """
    Führt den übergebenen Befehl in der Shell aus.
    :param cmd: auszuführender Befehl
    :param runtime_env: optional Umgebungsvariablen
    :returns: return code, stdout, stderr.
    :raises subprocess.TimeoutException: falls bei der Kommunikation zum gestarteten Prozess ein Timeout auftritt
    """
    if runtime_env is None:
        _res = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    else:
        _res = subprocess.run(cmd, env=runtime_env, capture_output=True, encoding='utf-8')
    return _res.returncode, _res.stdout, _res.stderr


def platform_locale() -> str:
    """
    :returns: Sprache des lokalen Hosts, zwei Kleinbuchstaben (z.B. 'de'); 'de', falls die Sprache nicht ermittelt
              werden kann
    """
    # noinspection PyBroadException
    try:
        _operating_system = platform.system().lower()
        if _operating_system == OS_LINUX:
            _rc, _stdout, _stderr = shell_cmd(['locale'])
            if _rc == 0:
                _m = re.search(r'.*LANG=(\w+).*', _stdout, re.DOTALL)
                if _m is not None:
                    _v = _m.group(1)
                    if len(_v) >= 2:
                        return _v[:2].lower()
                _m = re.search(r'.*LANGUAGE=(\w+).*', _stdout, re.DOTALL)
                if _m is not None:
                    _v = _m.group(1)
                    if len(_v) >= 2:
                        return _v[:2].lower()
        elif _operating_system == OS_WINDOWS:
            _rc, _stdout, _stderr = shell_cmd(['systeminfo'])
            if _rc == 0:
                _m = re.search(r'.*System\s+Locale:\s+(\w+).*', _stdout, re.DOTALL)
                if _m is not None:
                    _v = _m.group(1)
                    if len(_v) >= 2:
                        return _v[:2].lower()
        else:
            _v = os.environ.get(ENVA_LANG)
            if _v is not None and len(_v) >= 2:
                return _v[:2].lower()
            _v = os.environ.get(ENVA_LANGUAGE)
            if _v is not None and len(_v) >= 2:
                return _v[:2].lower()
    except Exception:
        pass
    return DEFAULT_LOCALE


def current_user() -> str:
    """
    :returns: Name des aktuell angemeldeten Benutzers.
    :raises RuntimeError: falls das lokale Betriebssystem nicht unterstützt wird.
    """
    _operating_system = platform.system().lower()
    if _operating_system == OS_LINUX:
        return pwd.getpwuid(os.getuid()).pw_name
    _raise_exception(_E_OS_NOT_SUPPORTED)


def is_valid_hostname(value: str) -> bool:
    """
    :param value: zu prüfender Wert
    :returns: True, falls der Wert ein gültiger Hostname ist; ansonsten False
    """
    if value[-1] == '.':
        # Punkt am Ende entfernen
        value = value[:-1]
    if len(value) > 253:
        return False
    labels = value.split('.')
    allowed = re.compile(r'(?!-)[A-Za-z0-9-_]{1,63}(?<!-)$')
    return all(allowed.match(label) for label in labels)


def _raise_exception(exception_id: str) -> NoReturn:
    """
    :param exception_id: Exception-ID
    :raises RuntimeError: immer
    """
    _locale = platform_locale()
    _msg = _ERROR_MSGS.get(exception_id).get(_locale)
    if _msg is None:
        _msg = _ERROR_MSGS.get(exception_id).get(DEFAULT_LOCALE)
    raise RuntimeError(_msg)


_E_OS_NOT_SUPPORTED = 'e-os-not-supported'
_ERROR_MSGS = {_E_OS_NOT_SUPPORTED: {'de': 'Betriebssystem wird nicht unterstützt',
                                     'en': 'Operating system not supported'}}
