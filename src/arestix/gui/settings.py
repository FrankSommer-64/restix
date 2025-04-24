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
Persönliche Einstellungen der arestix GUI.
"""

import os
import tomli
import tomli_w

from typing import Self

from PySide6 import QtGui
from PySide6.QtCore import QRect

from arestix.core import ARESTIX_GUI_SETTINGS_FILE_PATH
from arestix.core.arestix_exception import ArestixException
from arestix.core.messages import W_GUI_WRITE_GUI_SETTINGS_FAILED


class GuiSettings(dict):
    """
    Speichert die benutzerspezifischen Einstellungen der arestix-GUI.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.__is_modified = False

    def latest_target(self) -> str | None:
        """
        :returns: Alias-Name des zuletzt verwendeten Backup-Ziels
        """
        return self.get(_KEY_LATEST_TARGET)

    # noinspection PyArgumentList
    def win_geometry(self) -> QRect:
        """
        :returns: letzte Position und Größe des GUI-Fensters
        """
        _value = self.get(_KEY_WIN_GEOMETRY)
        return _default_win_geometry() if _value is None else QRect(*_value)

    def set_latest_target(self, target_alias: str):
        """
        Setzt den Alias-Namen des zuletzt verwendeten Backup-Ziels.
        :param target_alias: Alias-Name des Backup-Ziels
        """
        self[_KEY_LATEST_TARGET] = target_alias
        self.__is_modified = True

    def set_win_geometry(self, geometry: QRect):
        """
        Setzt letzte Position und Größe des GUI-Fensters.
        :param geometry: Position und Größe des GUI-Fensters
        """
        self[_KEY_WIN_GEOMETRY] = (geometry.x(), geometry.y(), geometry.width(), geometry.height())
        self.__is_modified = True

    def save(self, file_path: str = os.path.expanduser(ARESTIX_GUI_SETTINGS_FILE_PATH)):
        """
        Speichert die Einstellungen in einer Datei.
        :param file_path: Dateiname inklusive Pfad.
        :raises ArestixException: falls die Einstellungen nicht gespeichert werden konnten
        """
        if not self.__is_modified:
            return
        try:
            with open(file_path, 'wb') as _f:
                tomli_w.dump(self, _f)
        except (IOError, OSError, TypeError, ValueError) as e:
            raise ArestixException(W_GUI_WRITE_GUI_SETTINGS_FAILED, file_path, str(e))

    @classmethod
    def default(cls: Self) -> Self:
        """
        :returns: Standard-Einstellungen der arestix-GUI.
        """
        _settings = GuiSettings()
        _settings.set_win_geometry(_default_win_geometry())
        return _settings

    @classmethod
    def from_file(cls: Self, file_path: str = os.path.expanduser(ARESTIX_GUI_SETTINGS_FILE_PATH)) -> Self:
        """
        Liest die Einstellungen aus Datei.
        Gibt die Standard-Einstellungen zurück, falls die Datei nicht gelesen werden kann.
        :param file_path: Dateiname inklusive Pfad.
        :returns: Einstellungen der arestix-GUI.
        """
        try:
            with open(file_path, 'rb') as _f:
                _persistent_settings = tomli.load(_f)
            _settings = GuiSettings()
            _settings.update(_persistent_settings.items())
            return _settings
        except (IOError, OSError, TypeError, ValueError):
            return GuiSettings.default()


def _default_win_geometry() -> QRect:
    """
    :returns: Standard-Position und -Größe des GUI-Fensters
    """
    _screen_geometry = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    _width = min(_DEFAULT_WIN_WIDTH, _screen_geometry.width())
    _height = min(_DEFAULT_WIN_HEIGHT, _screen_geometry.height())
    return QRect(0, 0, _width, _height)

# Standard-Position und -Größe des GUI-Fensters
_DEFAULT_WIN_WIDTH = 800
_DEFAULT_WIN_HEIGHT = 720
_DEFAULT_WIN_GEOMETRY = [0, 0, _DEFAULT_WIN_WIDTH, _DEFAULT_WIN_HEIGHT]

# TOML-Keys der Datei mit den Einstellungen
_KEY_LATEST_TARGET = 'latest_target'
_KEY_WIN_GEOMETRY = 'win_geometry'
