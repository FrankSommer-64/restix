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
Unit tests für core.config.
Testdateien liegen im Projektverzeichnis tests/testdata/config.
"""

from pathlib import Path
import os.path
import unittest

from arestix.core.config import *

# Namen der nicht unterstützten Elemente in Testdatei unsupported_elements.toml
UNSUPPORTED_ELEMENTS = ['credentials.[0].user', 'credentials.[0].password', 'scope.[0].type',
                        'target.[0].url', 'user']
# Namen der Elemente in der Standard-arestix-Konfiguration, deren Wert eine Variable enthält
VAR_CREDENTIALS = {'shared': ['value']}
VAR_TARGETS = {'usbstick': ['location'],
               'nvme': ['location']}


class TestConfig(unittest.TestCase):
    def test_config_root_path(self):
        """
        Testet die Ermittlung des arestix-Konfigurationsverzeichnisses.
        """
        # existierendes Default-Verzeichnis
        self.assertEqual(os.path.join(Path.home(), *ARESTIX_CONFIG_SUBDIR), config_root_path())
        # existierendes benutzerdefiniertes Verzeichnis
        _custom_root = TestConfig.unit_test_home()
        os.environ[ENVA_ARESTIX_CONFIG_PATH] = _custom_root
        self.assertEqual(_custom_root, config_root_path())
        # nicht existierendes benutzerdefiniertes Verzeichnis
        os.environ[ENVA_ARESTIX_CONFIG_PATH] = os.path.join(Path.home(), 'nonexistent')
        self.assertRaises(ArestixException, config_root_path)
        # nicht existierendes Default-Verzeichnis
        _orig_home_dir = os.environ['HOME']
        try:
            os.environ['HOME'] = os.path.join(Path.home(), 'nonexistent')
            self.assertRaises(ArestixException, config_root_path)
        finally:
            os.environ['HOME'] = _orig_home_dir
            del os.environ[ENVA_ARESTIX_CONFIG_PATH]

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

    def test_variable_replacement(self):
        """
        Prüft, ob Variablen in der Konfiguration korrekt ersetzt werden.
        """
        _config = TestConfig.unittest_configuration()
        _clone = _config.for_cli({'USER': 'unittest'})
        self._replacement_test(_clone.credentials(), VAR_CREDENTIALS)
        self._replacement_test(_clone.targets(), VAR_TARGETS)

    def _dataset_test(self, file_name_pattern: str):
        """
        Test mit mehreren Testdaten-Dateien durchführen.
        :param file_name_pattern: Pattern für die Namen der Testdateien.
        :raises RestixException: falls beim Validieren der Dateien **keine** Exception auftritt
        """
        _toml_dataset = TestConfig.unittest_toml_dataset(file_name_pattern)
        for _file_name, _toml_data in _toml_dataset.items():
            with self.assertRaises(ArestixException, msg=_file_name) as _e:
                validate_config(_toml_data, _file_name)
            print(_e.exception)

    def _replacement_test(self, group: dict, element_desc: dict):
        """
        Testet Variablen-Ersetzung für eine Group der Unittest-Konfigurationsdatei.
        :param group: zu testende Group
        :param element_desc: Beschreibung der zu prüfenden Elemente.
        :raises AssertionError: falls nicht alle Variablen ersetzt wurden
        """
        for _element_name, _element_data in group.items():
            _var_attrs = element_desc.get(_element_name)
            if _var_attrs is None:
                continue
            for _var_attr in _var_attrs:
                _item_data = _element_data
                _items = _var_attr.split('.')
                for _item in _items:
                    _item_data = _item_data[_item]
                self.assertTrue(_item_data.find('${USER}') < 0)
                self.assertTrue(_item_data.find('unittest') >= 0)

    @staticmethod
    def unittest_toml_data(file_name: str = 'unittest.toml') -> dict:
        """
        :returns: TOML-Daten einer einzelnen Datei für Unit-Test
        """
        _file_path = os.path.join(TestConfig.unit_test_home(), file_name)
        with open(_file_path, 'r') as _f:
            _file_contents = _f.read()
            return tomli.loads(_file_contents)

    @staticmethod
    def unittest_toml_dataset(pattern: str) -> dict:
        """
        :param pattern: das Pattern für die Dateinamen.
        :returns: TOML-Daten mehrerer Dateien für Unit-Test; Key ist der Dateiname ohne Pfad, Value die TOML-Daten
        """
        _dataset = {}
        for _file_path in Path(TestConfig.unit_test_home()).glob(pattern):
            with open(_file_path, 'r') as _f:
                _file_contents = _f.read()
                _toml_data = tomli.loads(_file_contents)
                _dataset[os.path.basename(_file_path)] = _toml_data
        return _dataset

    @staticmethod
    def unittest_configuration() -> LocalConfig:
        """
        :returns: Standard arestix-Konfiguration für Unit-Tests
        """
        _config_file_path = os.path.join(TestConfig.unit_test_home(), ARESTIX_CONFIG_FN)
        _arestix_config = LocalConfig.from_file(_config_file_path)
        return _arestix_config

    @staticmethod
    def unit_test_home() -> str:
        """
        :returns: Wurzelverzeichnis für Testdateien der Unit-Tests
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'testdata', 'core', 'config'))


if __name__ == '__main__':
    unittest.main()
