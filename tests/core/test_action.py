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
Unit tests für core.action.
Testdateien liegen im Projektverzeichnis tests/testdata/config.
"""

from pathlib import Path
import os.path
import unittest

from restix.core.action import *

# Standard restix-Konfiguration für Unit-Tests
STANDARD_CONFIG_FN = 'unittest.toml'


class TestAction(unittest.TestCase):
    def test_backup_action(self):
        """
        Testet die Backup-Aktion.
        """
        _config = TestAction.unittest_configuration()
        # Test mit Includes und Excludes-Datei
        _backup_action = RestixAction.for_backup('target-usbstick', _config, None)
        print(_backup_action.to_restic_command())

    @staticmethod
    def unittest_configuration() -> LocalConfig:
        """
        :returns: Standard restix-Konfiguration für Unit-Tests
        """
        _config_file_path = os.path.join(TestAction.unit_test_home(), STANDARD_CONFIG_FN)
        _restix_config = LocalConfig.from_file(_config_file_path)
        return _restix_config

    @staticmethod
    def unit_test_home() -> str:
        """
        :returns: Wurzelverzeichnis für Testdateien der Unit-Tests
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'testdata', 'core', 'action'))


if __name__ == '__main__':
    unittest.main()
