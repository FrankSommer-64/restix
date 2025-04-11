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
Unit tests für gui.settings.
"""
import tempfile
import os.path
import unittest

from PySide6.QtCore import QRect

from arestix.core import ARESTIX_GUI_SETTINGS_FILE_PATH
from arestix.gui.settings import GuiSettings

# Standard arestix-Konfiguration für Unit-Tests
STANDARD_TARGET = 'mytarget'

# Name der Einstellungsdatei für Unit-Tests
TEST_FILE_PATH = os.path.join(tempfile.gettempdir(), ARESTIX_GUI_SETTINGS_FILE_PATH)


class TestSettings(unittest.TestCase):
    def test_default(self):
        """
        Testet die Standard-Einstellungen
        """
        _settings = GuiSettings()
        _settings.set_win_geometry(QRect(100, 100, 800, 600))
        _settings.set_latest_target(STANDARD_TARGET)
        self.assertEqual(QRect(100, 100, 800, 600), _settings.win_geometry())
        self.assertEqual(STANDARD_TARGET, _settings.latest_target())

    def test_roundtrip(self):
        """
        Testet den Zyklus Erzeugen-Speichern-Laden
        """
        _settings = GuiSettings()
        _settings.set_win_geometry(QRect(100, 100, 800, 600))
        _settings.set_latest_target(STANDARD_TARGET)
        if os.path.exists(TEST_FILE_PATH):
            os.remove(TEST_FILE_PATH)
        _settings.save(TEST_FILE_PATH)
        _settings2 = GuiSettings.from_file(TEST_FILE_PATH)
        self.assertEqual(_settings2.win_geometry(), _settings.win_geometry())
        self.assertEqual(_settings.latest_target(), _settings.latest_target())
        self.assertFalse(_settings2._GuiSettings__is_modified)


if __name__ == '__main__':
    unittest.main()
