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
Prüft die Konsistenz der lokalisierten Messages für eine bestimmte Sprache.
Die zu prüfende Sprache muss in Umgebungsvariable LANG angegeben werden.
Das Root-Verzeichnis der restix Source-Dateien muss in Umgebungsvariable RESTIX_SOURCE_PATH angegeben werden.
Im Einzelnen werden folgende Prüfungen durchgeführt:
- alle Message-Codes in Datei core.messages.py müssen einen entsprechenden Eintrag in core.messages_<LANG>.txt haben
- alle Einträge in core.messages_<LANG>.txt müssen in core.messages.py definiert sein
- alle Message-Codes in Datei core.messages.py müssen von einer anderen Source-Datei benutzt werden
- alle Aufrufe mit einem Message-Code müssen die nötigen Parameter für den lokalisierten Text übergeben

Ein Message-Code ist der Name einer Python-Konstante, z.B. E_INTERNAL_ERROR.
Eine Message-ID ist der Wert der Python-Konstante, z.B. 'e-internal-error'.
Das Script liefert als Exit-Code 0 für ok, 1 für mindestens eine Prüfung fehlgeschlagen und 2 für Ausführungsfehler.
Meldungen werden auf der Konsole ausgegeben.
"""

import ast
import os.path
import re
import sys


MSG_CODE_DEF_PATTERN = r"^([EILTW]_\w+)\s*=\s*'(.*)'"
LOC_TEXT_PATTERN = r"^([eiltw]\-[a-z0-9\-]*?)\s+(.*)$"
MSG_CODE_PATTERN = re.compile(r"\b([EILTW]_\w+)\b")


class MessageCodeVisitor(ast.NodeVisitor):
    """
    Sucht nach Aufrufen der Funktionen 'localized_message' und 'localized_label' sowie nach Auslösen von
    RestixExceptions in einer Source-Datei.
    Ermittelt den benutzten Message-Code und die Anzahl der Parameter.
    Die Suchergebnisse werden intern in einer Liste mit Tupeln(Zeilennummer, Message-Code, Anzahl Parameter) gespeichert.
    """
    def __init__(self):
        """
        Konstruktor
        """
        super().__init__()
        self.referenced_message_codes = set()
        self.localized_message_calls = []
        self.localized_label_calls = []

    def visit_Call(self, node: ast.Call):
        """
        Funktionsaufruf in der Source-Datei.
        :param node: Node des Funktionsaufrufs im abstract syntax tree
        """
        _func_name = None
        _func_args = []
        #print(ast.dump(node))
        for k, v in ast.iter_fields(node):
            if k == 'func':
                if isinstance(v, ast.Name):
                    _func_name = v.id
            if k == 'args':
                _func_args = v
        if _func_name == 'localized_message':
            _msg_code = '-'
            if isinstance(_func_args[0], ast.Name):
                if MSG_CODE_PATTERN.match(_func_args[0].id):
                    _msg_code = _func_args[0].id
                    self.referenced_message_codes.add(_msg_code)
            self.localized_message_calls.append((node.lineno, _msg_code, len(_func_args)))
            return
        if _func_name == 'localized_label':
            if isinstance(_func_args[0], ast.Name):
                if MSG_CODE_PATTERN.match(_func_args[0].id):
                    self.referenced_message_codes.add(_func_args[0].id)
            self.localized_label_calls.append((node.lineno, '-', len(_func_args)))
            return
        for _arg in _func_args:
            if isinstance(_arg, ast.Call):
                if isinstance(_arg.func, ast.Name):
                    _func_name = _arg.func.id
                    if _func_name == 'localized_label':
                        _c_args = _arg.args
                        if isinstance(_c_args[0], ast.Name):
                            _msg_code = _c_args[0].id
                            if MSG_CODE_PATTERN.match(_msg_code):
                                self.referenced_message_codes.add(_msg_code)
                        self.localized_label_calls.append((node.lineno, '-', len(_c_args)))
                    if _func_name == 'localized_message':
                        _c_args = _arg.args
                        _msg_code = '-'
                        if isinstance(_c_args[0], ast.Name):
                            if MSG_CODE_PATTERN.match(_c_args[0].id):
                                _msg_code = _c_args[0].id
                                self.referenced_message_codes.add(_msg_code)
                        self.localized_message_calls.append((node.lineno, _msg_code, len(_c_args)))

    def visit_Raise(self, node: ast.Raise):
        """
        Exception in der Source-Datei.
        :param node: Node der ausgelösten Exception im abstract syntax tree
        """
        _exc_type = None
        _exc_args = []
        for k, v in ast.iter_fields(node):
            if k == 'exc' and v is not None:
                for ek, ev in ast.iter_fields(v):
                    if ek == 'func':
                        _exc_type = ev.id
                    if ek == 'args':
                        _exc_args = ev
        if _exc_type == 'RestixException':
            _msg_code = '-'
            if isinstance(_exc_args[0], ast.Name):
                if MSG_CODE_PATTERN.match(_exc_args[0].id):
                    _msg_code = _exc_args[0].id
                    self.referenced_message_codes.add(_msg_code)
            self.localized_message_calls.append((node.lineno, _msg_code, len(_exc_args)))


def read_message_codes(file_path: str) -> tuple[int, dict]:
    """
    Liest alle Message-Codes, die in der angegebenen Datei definiert wurden.
    :param file_path: Dateiname mit vollständigem Pfad
    :returns: Return code (0=ok, 1=Fehler) und alle gefundenen Message-Codes {Message-Code: Message-ID}
    """
    _msg_codes = {}
    _msg_ids = set()
    _dup_codes = []
    _dup_ids = []
    _pattern = re.compile(MSG_CODE_DEF_PATTERN)
    _file_name = os.path.basename(file_path)
    _duplicates_status = 0
    with open(file_path, 'r') as _f:
        _lines = _f.readlines()
    _line_nr = 0
    for _line in _lines:
        _line_nr += 1
        _line = _line.strip()
        if len(_line) == 0 or _line.startswith('#'):
            continue
        _match = _pattern.search(_line)
        if _match:
            _msg_code = _match.group(1)
            _msg_id = _match.group(2)
            if _msg_code in _msg_codes:
                # Message-Code ist schon definiert
                _dup_codes.append(f'{_line_nr}: {_msg_code}')
            if _msg_id in _msg_ids:
                # Message-ID ist schon definiert
                _dup_ids.append(f'{_line_nr}: {_msg_id}')
            else:
                _msg_codes[_msg_code] = _msg_id
    if len(_dup_codes) > 0:
        print(f'In Datei {_file_name} sind Message-Codes mehrfach definiert:')
        print('  %s' % ','.join(_dup_codes))
        _duplicates_status = 1
    if len(_dup_ids) > 0:
        print(f'In Datei {_file_name} sind Message-IDs mehrfach definiert:')
        print('  %s' % ','.join(_dup_ids))
        _duplicates_status = 1
    return _duplicates_status, _msg_codes


def read_localized_messages(file_path: str, overall_status: int) -> tuple[int,dict]:
    """
    Liest alle lokalisierten Messages, die in der angegebenen Datei definiert wurden.
    :param file_path: Dateiname mit vollständigem Pfad
    :param overall_status: aktueller Gesamtstatus aller Prüfungen
    :returns: Return code (0=ok, 1=Fehler) und alle gefundenen lokalisierten Messages {Message-ID: lokalisierter Text}
    """
    _duplicates_code = overall_status
    _msgs = {}
    _dup_ids = []
    _file_name = os.path.basename(file_path)
    _pattern = re.compile(LOC_TEXT_PATTERN)
    with open(file_path, 'r') as _f:
        _lines = _f.readlines()
    _line_nr = 0
    for _line in _lines:
        _line_nr += 1
        _line = _line.strip()
        if len(_line) == 0 or _line.startswith('#'):
            continue
        _match = _pattern.search(_line)
        if _match:
            _msg_id = _match.group(1)
            _msg_text = _match.group(2)
            if _msg_id in _msgs:
                _dup_ids.append(f'{_line_nr}: {_msg_id}')
            else:
                _msgs[_msg_id] = _msg_text
    if len(_dup_ids) > 0:
        print(f'In Datei {_file_name} sind Message-IDs mehrfach definiert:')
        print('  %s' % ','.join(_dup_ids))
        _duplicates_code = 1
    return _duplicates_code, _msgs


def check_localized_messages(messages: dict, localized_messages: dict, localized_messages_file_path: str, rc: int) -> int:
    """
    Prüft, ob zu jedem Message-Code eine Message-ID definiert wurde und umgekehrt.
    :param messages: Code und ID aller Messages
    :param localized_messages: Message ID und lokalisierter Text für alle Messages
    :param localized_messages_file_path: Name der Datei, in der die lokalisierten Messages definiert wurden
    :param rc: aktueller Gesamtstatus aller Prüfungen
    :returns: 0=Prüfung ok, 1=Prüfung fehlgeschlagen
    """
    _missing = []
    _undefined = []
    _msg_id_strings = set(messages.values())
    _file_name = os.path.basename(localized_messages_file_path)
    for _msg_id in messages.values():
        if _msg_id not in localized_messages:
            _missing.append(_msg_id)
    if len(_missing) > 0:
        rc = 1
        print(f'In Datei {_file_name} wurden folgende Message-IDs nicht definiert:')
        print('  %s' % ','.join(_missing))
    for _msg_id in localized_messages.keys():
        if _msg_id not in _msg_id_strings:
            _undefined.append(_msg_id)
    if len(_undefined) > 0:
        rc = 1
        print(f'In Datei {_file_name} gibt es für folgende Message-IDs keinen Message-Code:')
        print('  %s' % ','.join(_undefined))
    return rc


def check_message_code_references(source_path: str, messages: dict, localized_messages: dict, rc: int) -> int:
    """
    Prüft, ob bei allen Aufrufen mit lokalisierten Messages die korrekte Anzahl an Argumenten übergeben werden.
    :param source_path: das Wurzelverzeichnis, unterhalb dessen Python-Source-Dateien gesucht werden sollen.
    :param messages: Code und ID aller Messages
    :param localized_messages: Message ID und lokalisierter Text für alle Messages
    :param rc: aktueller Gesamtstatus aller Prüfungen
    :returns: 0=Prüfung ok, 1=Prüfung fehlgeschlagen
    :rtype: int
    """
    for path, sub_dirs, files in os.walk(source_path):
        for _file_name in files:
            if not _file_name.endswith('.py'):
                continue
            _file_path = os.path.join(path, _file_name)
            with open(_file_path, 'r') as _f:
                source_code = _f.read()
            _syntax_tree = ast.parse(source_code, _file_path)
            _visitor = MessageCodeVisitor()
            _visitor.visit(_syntax_tree)
            for _line_nr, _msg_code, _actual_arg_count in _visitor.localized_label_calls:
                if _actual_arg_count != 1:
                    rc = 1
                    print(f'{_file_name}:{_line_nr} localized_label erwartet 1 Argument, '
                          f'übergeben werden {_actual_arg_count}')
            for _line_nr, _msg_code, _actual_arg_count in _visitor.localized_message_calls:
                if _msg_code == '-':
                    print(f'{_file_name}:{_line_nr} Anzahl Argumente für localized_message kann nicht überprüft werden')
                    continue
                _msg_id = messages.get(_msg_code)
                _msg_text = localized_messages.get(_msg_id)
                _expected_arg_count = len(re.findall(r'\{\d+}', _msg_text))
                if _expected_arg_count != _actual_arg_count - 1:
                    rc = 1
                    print(f'{_file_name}:{_line_nr} {_msg_code} erwartet {_expected_arg_count} Argumente, '
                          f'übergeben werden {_actual_arg_count-1}')
    return rc


def check_unused_message_codes(source_path: str, messages: dict, rc: int) -> int:
    """
    Prüft, ob alle Message-Codes irgendwo im Source-Code benutzt werden.
    :param source_path: das Wurzelverzeichnis, unterhalb dessen Python-Source-Dateien gesucht werden sollen.
    :param messages: Code und ID aller Messages
    :param rc: aktueller Gesamtstatus aller Prüfungen
    :returns: 0=Prüfung ok, 1=Prüfung fehlgeschlagen
    :rtype: int
    """
    _used_msg_codes = set()
    for path, sub_dirs, files in os.walk(source_path):
        for _file_name in files:
            if not _file_name.endswith('.py'):
                continue
            _file_path = os.path.join(path, _file_name)
            with open(_file_path, 'r') as f:
                source_code = f.read()
            _matches = MSG_CODE_PATTERN.finditer(source_code)
            for _m in _matches:
                _msg_code = _m.group(1)
                _begin_pos, _end_pos = _m.span()
                _def_pattern = f'{_msg_code}\\s*='
                if re.match(_def_pattern, source_code[_begin_pos:]):
                    # Message-Code-Definition ignorieren
                    continue
                _used_msg_codes.add(_msg_code)
    for _msg_code in messages.keys():
        if _msg_code not in _used_msg_codes:
            rc = 1
            print(f'Message-Code {_msg_code} wird nicht verwendet')
    return rc


if __name__ == '__main__':
    _rc = 0
    try:
        # benötigte Umgebungsvariablen einlesen
        _lang = os.environ.get('LANG')
        if _lang is None:
            raise RuntimeError('Umgebungsvariable LANG ist nicht definiert')
        _locale = _lang[:2].lower()
        _source_path = os.environ.get('RESTIX_SOURCE_PATH')
        if _source_path is None:
            raise RuntimeError('Umgebungsvariable RESTIX_SOURCE_PATH ist nicht definiert')
        _core_package_path = os.path.join(_source_path, 'restix', 'core')
        _message_file_path = os.path.join(_core_package_path, 'messages.py')
        _localized_message_file_path = os.path.join(_core_package_path, f'messages_{_locale}.txt')
        # alle Message-Codes von Source-Datei core.messages.py einlesen
        _rc, _message_codes = read_message_codes(_message_file_path)
        # lokalisierte Messages aus Datei core.messages_<LANG>.txt einlesen
        _rc, _localized_messages = read_localized_messages(_localized_message_file_path, _rc)
        # prüfen, ob alle Message-Codes eine Lokalisierung haben und andersherum
        _rc = check_localized_messages(_message_codes, _localized_messages, _localized_message_file_path, _rc)
        # prüfen, ob alle Funktionsaufrufe mit Message Codes die korrekte Anzahl Parameter haben
        _rc = check_message_code_references(_source_path, _message_codes, _localized_messages, _rc)
        # prüfen, ob alle Message Codes im Source-Code benutzt werden
        _rc = check_unused_message_codes(_source_path, _message_codes, _rc)
    except Exception as e:
        print(e)
        sys.exit(2)
    if _rc == 0:
        print('Lokalisierung ist korrekt.')
    sys.exit(_rc)
