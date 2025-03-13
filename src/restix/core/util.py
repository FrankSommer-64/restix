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
import sys
from typing import NoReturn

import grp
import os
import platform
import pwd
import re
import shutil
import subprocess


# Defaultwerte
DEFAULT_LOCALE = 'de'

# Umgebungsvariablen
ENVA_LANG = 'LANG'
ENVA_LANGUAGE = 'LANGUAGE'

# Betriebssysteme
OS_LINUX = 'linux'
OS_WINDOWS = 'windows'

# Plattform-spezifische Imports
if sys.platform == OS_WINDOWS:
    import win32net
    import win32netcon
    import ctypes
    from ctypes import wintypes


def full_path_of(path_spec: str) -> str:
    """
    :param path_spec: Pfadangabe
    :returns: vervollständigte Pfadangabe
    """
    if path_spec.startswith('~'):
        return os.path.expanduser(path_spec)
    return os.path.abspath(path_spec)


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


def set_node_rights(path: str, owner: str, permissions: str):
    """
    Setzt den Besitzer eines Elements im Dateisystem.
    :param path: Verzeichnis oder Datei
    :param owner: User oder User:Group.
    :param permissions: Zugriffsrechte für Benutzer, Group und alle anderen
    """
    if not is_valid_owner_spec(owner):
        _raise_exception(_E_INV_OWNER_SPEC)
    _permissions_value = permissions_value(permissions)
    if owner.count(':') == 1:
        _user, _group = owner.split(':')
    else:
        _user = owner
        _group = None
    _operating_system = platform.system().lower()
    if _operating_system == OS_LINUX:
        if _group is None:
            shutil.chown(path, user=_user)
        else:
            shutil.chown(path, user=_user, group=_group)
        os.chmod(path, _permissions_value)
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


def is_valid_owner_spec(value: str) -> bool:
    """
    :param value: zu prüfender Wert
    :returns: True, falls der Wert eine gültige Angabe für Benutzer und ggf. Group auf dem lokalen System ist;
              ansonsten False
    """
    if value.count(':') == 0:
        # nur Benutzer
        return value in local_users()
    elif value.count(':') == 1:
        # Benutzer und Group
        _user, _group  = value.split(':')
        return _user in local_users() and _group in local_groups()
    return False


def permissions_value(value: str) -> int:
    """
    :param value: Zugriffsrechte.
    :returns: Zugriffsrechte als Oktalzahl.
    :raises RuntimeError: falls der angegebene Wert ungültig ist
    """
    try:
        return int(value, 8)
    except ValueError:
        _raise_exception(_E_INV_PERMISSIONS)


def local_users() -> list[str]:
    """
    :returns: Name aller Benutzer auf dem lokalen System
    """
    _operating_system = platform.system().lower()
    if _operating_system == OS_LINUX:
        return [_u.pw_name for _u in pwd.getpwall()]
    elif _operating_system == OS_WINDOWS:
        _users = []
        _resume_handle = 0
        while True:
            _result = win32net.NetUserEnum(None, 0, win32netcon.FILTER_NORMAL_ACCOUNT, _resume_handle)
            _users.extend([_u['name'] for _u in _result[0]])
            _resume_handle = _result[2]
            if not _resume_handle:
                break
        return _users
    _raise_exception(_E_OS_NOT_SUPPORTED)


def local_groups() -> list[str]:
    """
    :returns: Name aller Groups auf dem lokalen System
    """
    _operating_system = platform.system().lower()
    if _operating_system == OS_LINUX:
        return [_g.gr_name for _g in grp.getgrall()]
    elif _operating_system == OS_WINDOWS:
        _groups = []
        _resume_handle = 0
        while True:
            _result = win32net.NetGroupEnum(None, 0, win32netcon.FILTER_NORMAL_ACCOUNT, _resume_handle)
            _groups.extend([_g['name'] for _g in _result[0]])
            _resume_handle = _result[2]
            if not _resume_handle:
                break
        return _groups
    _raise_exception(_E_OS_NOT_SUPPORTED)


def installation_path() -> str:
    """
    :returns: Installationspfad für restix.
    :raises RuntimeError: falls das lokale Betriebssystem nicht unterstützt wird.
    """
    _operating_system = platform.system().lower()
    if _operating_system == OS_LINUX:
        return _LINUX_GLOB_INSTALLATION_PATH
    _raise_exception(_E_OS_NOT_SUPPORTED)


def _raise_exception(exception_id: str) -> NoReturn:
    """
    :param exception_id: Exception-ID
    :raises RuntimeError: immer
    """
    _locale = platform_locale()
    _msg = _EMSGS.get(exception_id).get(_locale)
    if _msg is None:
        _msg = _EMSGS.get(exception_id).get(DEFAULT_LOCALE)
    raise RuntimeError(_msg)

"""
FILE PERMISSIONS/OWNER
----------------------
Windows
import os
import ctypes
from ctypes import wintypes

# Define necessary constants and structures
SECURITY_INFORMATION = 1 # OWNER_SECURITY_INFORMATION
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

# Read the file's owner
def get_file_owner(filepath):
pSD = ctypes.c_void_p()
owner_sid = ctypes.c_void_p()
owner_defaulted = ctypes.c_int()

res = advapi32.GetFileSecurityW(
wintypes.LPCWSTR(filepath),
SECURITY_INFORMATION,
pSD,
0,
ctypes.byref(owner_sid)
)
if res == 0:
raise ctypes.WinError(ctypes.get_last_error())

return owner_sid

# Set the new file's owner
def set_file_owner(filepath, owner_sid):
res = advapi32.SetFileSecurityW(
wintypes.LPCWSTR(filepath),
SECURITY_INFORMATION,
owner_sid
)
if res == 0:
raise ctypes.WinError(ctypes.get_last_error())

file_path = 'your_file.txt'
new_file_path = 'new_file.txt'

owner_sid = get_file_owner(file_path)

# Create a new file and apply the same owner
with open(new_file_path, 'w') as new_file:
new_file.write('This is a new file.')
set_file_owner(new_file_path, owner_sid)
"""

_LINUX_GLOB_INSTALLATION_PATH = '/opt/restix'

_E_INV_OWNER_SPEC = 'e-inv-owner-spec'
_E_INV_PERMISSIONS = 'e-inv-permissions'
_E_OS_NOT_SUPPORTED = 'e-os-not-supported'
_EMSGS = {_E_INV_OWNER_SPEC: {'de': 'Ungültige Besitzerangabe',
                              'en': 'Invalid owner specification'},
          _E_INV_PERMISSIONS: {'de': 'Ungültige Zugriffsrechte',
                               'en': 'Invalid permissions'},
          _E_OS_NOT_SUPPORTED: {'de': 'Betriebssystem wird nicht unterstützt',
                                'en': 'Operating system not supported'}}
