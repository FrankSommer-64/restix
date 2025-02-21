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
Unit tests für core.config.
"""

from pathlib import Path
import os.path
import unittest

from restix.core.config import *

UNSUPPORTED_ELEMENTS = ['credentials.[0].user', 'credentials.[0].password', 'scope.[0].type',
                        'target.[0].url', 'user']


class TestConfig(unittest.TestCase):
    def test_config_root_path(self):
        """
        Testet die Ermittlung des restix-Konfigurationsverzeichnisses.
        """
        # existierendes Default-Verzeichnis
        self.assertEqual(os.path.join(Path.home(), *RESTIX_CONFIG_SUBDIR), config_root_path())
        # existierendes benutzerdefiniertes Verzeichnis
        _custom_root = TestConfig.unit_test_home()
        os.environ[ENVA_RESTIX_CONFIG_PATH] = _custom_root
        self.assertEqual(_custom_root, config_root_path())
        # nicht existierendes benutzerdefiniertes Verzeichnis
        os.environ[ENVA_RESTIX_CONFIG_PATH] = os.path.join(Path.home(), 'nonexistent')
        self.assertRaises(RestixException, config_root_path)
        # nicht existierendes Default-Verzeichnis
        _orig_home_dir = os.environ['HOME']
        try:
            os.environ['HOME'] = os.path.join(Path.home(), 'nonexistent')
            self.assertRaises(RestixException, config_root_path)
        finally:
            os.environ['HOME'] = _orig_home_dir
            del os.environ[ENVA_RESTIX_CONFIG_PATH]

    def test_unsupported_elements(self):
        """
        Prüft, ob nicht unterstützte Elemente korrekt erkannt werden.
        """
        _file_name = 'unsupported_elements.toml'
        _toml_data = TestConfig.unittest_toml_data(_file_name)
        _warnings = validate_config(_toml_data, _file_name)
        self.assertEqual(len(UNSUPPORTED_ELEMENTS), len(_warnings))
        for _warning in _warnings:
            self.assertTrue([any(_warning.find(_t) >= 0 for _t in UNSUPPORTED_ELEMENTS)], _warning)

    def test_missing_mandatory_elements(self):
        """
        Prüft, ob fehlende notwendige Elemente korrekt erkannt werden.
        """
        self._dataset_test('missing*.toml')

    def test_invalid_typed_elements(self):
        """
        Prüft, ob Elemente mit falschem Typ korrekt erkannt werden.
        """
        self._dataset_test('invalid_typed*.toml')

    def test_invalid_target_references(self):
        """
        Prüft, ob Target-Referenzen auf nicht existierenden Scope oder Credentials erkannt werden.
        """
        self._dataset_test('invalid_target*.toml')

    def test_duplicate_group_names(self):
        """
        Prüft, ob mehrfach definierte Groups korrekt erkannt werden.
        """
        self._dataset_test('duplicate*.toml')

    def _dataset_test(self, file_name_pattern):
        """
        Test mit mehreren Testdaten-Dateien durchführen.
        :param str file_name_pattern: Pattern für die Namen der Testdateien
        :raises: falls beim Validieren der Dateien keine Exception auftritt
        """
        _toml_dataset = TestConfig.unittest_toml_dataset(file_name_pattern)
        for _file_name, _toml_data in _toml_dataset.items():
            with self.assertRaises(RestixException, msg=_file_name) as _e:
                validate_config(_toml_data, _file_name)
            print(_e.exception)

    @staticmethod
    def unittest_toml_data(file_name = 'unittest.toml'):
        """
        :returns: TOML-Daten für Unit-Test
        :rtype: dict
        """
        _file_path = os.path.join(TestConfig.unit_test_home(), file_name)
        with open(_file_path, 'r') as _f:
            _file_contents = _f.read()
            return tomli.loads(_file_contents)

    @staticmethod
    def unittest_toml_dataset(pattern):
        """
        :returns: TOML-Daten für Unit-Test
        :rtype: dict
        """
        _dataset = {}
        for _file_path in Path(TestConfig.unit_test_home()).glob(pattern):
            with open(_file_path, 'r') as _f:
                _file_contents = _f.read()
                _toml_data = tomli.loads(_file_contents)
                _dataset[os.path.basename(_file_path)] = _toml_data
        return _dataset

    @staticmethod
    def unittest_configuration(file_name = 'unittest.toml'):
        """
        :returns: restix-Konfiguration für Unit-Tests
        :rtype: LocalConfig
        """
        _config_file_path = os.path.join(TestConfig.unit_test_home(), file_name)
        _restix_config = LocalConfig.from_file(_config_file_path)
        return _restix_config

    @staticmethod
    def unit_test_home():
        """
        :returns: Wurzelverzeichnis für Testdaten der Unit-Tests
        :rtype: str
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'testdata', 'config'))


if __name__ == '__main__':
    unittest.main()
