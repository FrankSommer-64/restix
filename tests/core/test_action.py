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
Testdateien liegen im Projektverzeichnis tests/testdata/action.
"""

import os.path
import unittest

from restix.core.action import *

# Standard restix-Konfiguration für Unit-Tests
STANDARD_CONFIG_FN = 'unittest.toml'

# Backup-Ziele
TARGET_SRV = 'target-srv'
TARGET_EXTHDD = 'target-exthdd'
TARGET_USBSTICK = 'target-usbstick'
TARGET_DIR = 'target-dir'

EXPECTED_BACKUP_CMD_SRV = ['restic', 'backup', '--repo', 'sftp:myserver:data*', '--password-file', '*/pw.txt', '--files-from', '*/minimal.list']
EXPECTED_BACKUP_CMD_EXTHDD = ['restic', 'backup', '--repo', '/media/${USER}/58af5a30-36b5-4f0b-bb8f-a70683ae3e7e/restix/*', '--password-file', '*/pw.txt', '--files-from', '*/full.list', '--exclude-file', '/tmp/*']
EXPECTED_BACKUP_CMD_USBSTICK = ['restic', 'backup', '--repo', '/media/${USER}/USBSAVE/restix/*', '--password-file', '*/pw.txt', '--files-from', '*/full.list', '--exclude-file', '*/full_excludes.list']
EXPECTED_BACKUP_CMD_DIR = ['restic', 'backup', '--repo', '/var/restix/*', '--password-file', '*/pw.txt', '--files-from', '*/full.list', '--exclude-file', '/tmp/*']

EXPECTED_INIT_CMD_DIR = ['restic', 'init', '--repo', '/var/restix/*', '--password-file', '*/pw.txt']

class TestAction(unittest.TestCase):

    original_config_path = ''

    @classmethod
    def setUpClass(cls):
        cls.original_config_path = os.environ.get(ENVA_RESTIX_CONFIG_PATH)
        os.environ[ENVA_RESTIX_CONFIG_PATH] = cls.unit_test_home()

    @classmethod
    def tearDownClass(cls):
        if cls.original_config_path is not None:
            os.environ[ENVA_RESTIX_CONFIG_PATH] = cls.original_config_path

    def test_backup_action(self):
        """
        Testet die Backup-Aktion.
        """
        _config = TestAction.unittest_configuration()
        # Test keine Excludes und keine Ignores
        _backup_action = RestixAction.for_action_id(ACTION_BACKUP, TARGET_SRV, _config, None)
        self.verify_restic_command(EXPECTED_BACKUP_CMD_SRV, _backup_action.to_restic_command())
        # Test nur Ignores
        _backup_action = RestixAction.for_action_id(ACTION_BACKUP, TARGET_EXTHDD, _config, None)
        self.verify_restic_command(EXPECTED_BACKUP_CMD_EXTHDD, _backup_action.to_restic_command())
        # Test nur Excludes
        _backup_action = RestixAction.for_action_id(ACTION_BACKUP, TARGET_USBSTICK, _config, None)
        self.verify_restic_command(EXPECTED_BACKUP_CMD_USBSTICK, _backup_action.to_restic_command())
        # Test Ignores und Excludes
        _backup_action = RestixAction.for_action_id(ACTION_BACKUP, TARGET_DIR, _config, None)
        self.verify_restic_command(EXPECTED_BACKUP_CMD_DIR, _backup_action.to_restic_command())

    def test_init_action(self):
        """
        Testet die Init-Aktion.
        """
        _config = TestAction.unittest_configuration()
        # Test keine Excludes und keine Ignores
        _init_action = RestixAction.for_action_id(ACTION_INIT, TARGET_DIR, _config, None)
        self.verify_restic_command(EXPECTED_INIT_CMD_DIR, _init_action.to_restic_command())

    def verify_restic_command(self, expected_command: list[str], actual_command: list[str]):
        """
        Prüft, ob ein restic-Befehl der Erwartung entspricht.
        :param expected_command:
        :param actual_command:
        :raises AssertionError: falls der Befehl nicht der Erwartung entspricht.
        """
        self.assertEqual(len(expected_command), len(actual_command))
        for _i, _elem in enumerate(expected_command):
            _elem = _elem.replace('${USER}', current_user())
            if _elem.startswith('*'):
                self.assertTrue(actual_command[_i].endswith(_elem[1:]))
            elif _elem.endswith('*'):
                self.assertTrue(actual_command[_i].startswith(_elem[:-1]))
            else:
                self.assertEqual(_elem, actual_command[_i])

    @staticmethod
    def unittest_configuration() -> LocalConfig:
        """
        :returns: Standard restix-Konfiguration für Unit-Tests
        """
        _config_file_path = os.path.join(TestAction.unit_test_home(), RESTIX_CONFIG_FN)
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
