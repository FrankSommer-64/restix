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
Model der restix-Konfiguration zur Nutzung in der GUI.
"""

from typing import Any

import re

from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QPersistentModelIndex, QAbstractItemModel, QDir
from PySide6.QtWidgets import QFileSystemModel

from restix.core import *
from restix.core.config import LocalConfig


class CheckBoxFileSystemModel(QFileSystemModel):
    """
    Model für den Verzeichnisbaum im Scope-Editor.
    """
    def __init__(self, includes: list[str], excludes: list[str], ignores: list[str]):
        """
        Konstruktor.
        :param includes: einzuschließende Dateien und Verzeichnisse
        :param excludes: auszuschließende Dateien und Verzeichnisse
        :param ignores: zu ignorierende Dateien und Verzeichnisse
        """
        super().__init__()
        self.__check_state = {}
        for _element in excludes:
            self.__check_state[_element] = False
        for _element in includes:
            self.__check_state[_element] = True
        self.__ignore_patterns = CheckBoxFileSystemModel._regex_patterns_for(ignores)
        print(self.__check_state)
        print(self.__ignore_patterns)
        self.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)

    def flags(self, index: QModelIndex | QPersistentModelIndex, /) -> Qt.ItemFlag:
        """
        Fügt den angezeigten Elementen eine Checkbox hinzu.
        :param index: Index des Elements
        :returns: Flags für das Element
        """
        return super().flags(index) | Qt.ItemFlag.ItemIsUserCheckable

    def check_state(self, index):
        """
        :param index: Index des Elements
        :returns: Status der Checkbox des Elements
        """
        return self.__check_state.get(self.filePath(index), Qt.CheckState.Unchecked)

    def check_parent(self, parent):
        if not parent.isValid():
            return
        childStates = [self.check_state(self.index(r, 0, parent)) for r in range(self.rowCount(parent))]
        newState = Qt.CheckState.Checked if all(childStates) else Qt.CheckState.Unchecked
        oldState = self.check_state(parent)
        if newState != oldState:
            self.set_check_state(parent, newState)
            self.dataChanged.emit(parent, parent)
        self.check_parent(parent.parent())

    def set_check_state(self, index, state):
        path = self.filePath(index)
        if self.__check_state.get(path) == state:
            return
        self.__check_state[path] = state

    def data(self, index: QModelIndex | QPersistentModelIndex, role = Qt.ItemDataRole.DisplayRole):
        """
        :param index: Index der Zugriffsdaten
        :param role: Role
        :return: Daten des Elements mit angegebenem Index und Role
        """
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            return self.check_state(index)
        return super().data(index, role)

    def setData(self, index: QModelIndex | QPersistentModelIndex, value, role):
        """
        Ändert Zugriffsdaten im Model.
        :param index: Index der Zugriffsdaten
        :param role: Typ-Selektor
        :param value: Wert des Elements
        """
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            self.set_check_state(index, value)
            for row in range(self.rowCount(index)):
                self.setData(self.index(row, 0, index), value, Qt.ItemDataRole.CheckStateRole)
            self.dataChanged.emit(index, index)
            return True
        return super().setData(index, value, role)

    @classmethod
    def _regex_patterns_for(cls, patterns: list[str]) -> list[re.Pattern]:
        _regex_patterns = []
        for _pattern in patterns:
            _regex_pattern = ''
            for _ch in _pattern:
                if _ch in r'\.[]{}()+-=^$':
                    _regex_pattern += f'\\{_ch}'
                elif _ch == '*':
                    _regex_pattern += '.*'
                else:
                    _regex_pattern += _ch
            _regex_patterns.append(re.compile(_regex_pattern))
        return _regex_patterns


class ConfigGroupNamesModel(QAbstractListModel):
    """
    Basis-Model für Combobox-Widgets, die nur mit dem Aliasnamen von Daten einer Group arbeiten.
    """
    def __init__(self, group: str, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param group: Name der Group
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__()
        self.__group = group
        self.__data = configuration_data

    def rowCount(self, /, parent: QModelIndex | QPersistentModelIndex= ...) -> int:
        """
        :param parent:
        :returns: Anzahl der Zugriffsdaten-Elemente
        """
        return len(self.__data[self.__group])

    def data(self, index: QModelIndex | QPersistentModelIndex, /, role: int = ...) -> Any:
        """
        Gibt die Daten von Zugriffsdaten zurück, bei DisplayRole der Aliasname für die Anzeige in einer Combobox,
        bei UserRole das Dictionary mit den gesamten Daten.
        :param index: Index der Zugriffsdaten
        :param role: Role
        :returns: Zugriffsdaten für die role
        """
        if not index.isValid() or index.row() >= len(self.__data[self.__group]):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.__data[self.__group][index.row()][CFG_PAR_ALIAS]
        if role == Qt.ItemDataRole.UserRole:
            return self.__data[self.__group][index.row()]
        return None

    def setData(self, index: QModelIndex | QPersistentModelIndex, value: dict, /, role = ...):
        """
        Ändert Zugriffsdaten im Model.
        :param index: Index der Zugriffsdaten
        :param value: komplette Zugriffsdaten
        :param role: Typ-Selektor
        """
        if index.row() < 0:
            # neue Zugriffsdaten
            self.beginInsertRows(QModelIndex(), index.row(), index.row())
            self.__data[self.__group].append(value)
            self.endInsertRows()
            self.rowsInserted.emit(index, len(self.__data[self.__group]), 1)
            self.layoutChanged.emit()
        else:
            # existierende Zugriffsdaten
            _model_data = self.__data[self.__group][index.row()]
            if value[CFG_PAR_ALIAS] != _model_data[CFG_PAR_ALIAS]:
                # Alias wurde umbenannt, Referenzen in den Backup-Zielen aktualisieren
                self.__data.element_renamed(self.__group, _model_data[CFG_PAR_ALIAS], value[CFG_PAR_ALIAS])
            _model_data.update(value)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def removeRow(self, row, /, parent = ...) -> bool:
        """
        Löscht Zugriffsdaten im Model.
        :param row: Index der Zugriffsdaten
        :param parent: immer None
        """
        self.beginRemoveRows(QModelIndex(), row, row)
        del self.__data[self.__group][row]
        self.endRemoveRows()
        self.layoutChanged.emit()
        return True


class ConfigGroupModel(QAbstractItemModel):
    """
    Model für Widgets, die mit allen Daten der Elemente einer Group arbeiten.
    """
    def __init__(self, group: str, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param group: Name der Group
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__()
        self.__group = group
        self.__data = configuration_data

    def parent(self):
        return QModelIndex()

    def index(self, row: int, column: int, /, parent: QModelIndex | QPersistentModelIndex = ...) -> QModelIndex:
        """
        :param row: Zeile
        :param column: Spalte
        :param parent: immer ungültiger Index
        :returns: Anzahl der Zugriffsdaten-Elemente
        """
        return QAbstractItemModel.createIndex(self, row, column)

    def rowCount(self, /, parent: QModelIndex | QPersistentModelIndex= ...) -> int:
        """
        :param parent: immer ungültiger Index
        :returns: Anzahl der Zugriffsdaten-Elemente
        """
        return len(self.__data[self.__group])

    def columnCount(self, /, parent: QModelIndex | QPersistentModelIndex= ...) -> int:
        """
        :param parent: immer ungültiger Index
        :returns: Anzahl der Zugriffsdaten-Elemente
        """
        # alias, comment, type, value
        return 4

    def data(self, index: QModelIndex | QPersistentModelIndex, /, role: int = ...) -> Any:
        """
        Gibt die Daten von Zugriffsdaten zurück, bei DisplayRole der Aliasname für die Anzeige in einer Combobox,
        bei UserRole das Dictionary mit den gesamten Daten.
        :param index: Index der Zugriffsdaten
        :param role: Role
        :returns: Zugriffsdaten für die role
        """
        if not index.isValid() or index.row() >= len(self.__data[self.__group]):
            return None
        if role == Qt.ItemDataRole.DisplayRole or Qt.ItemDataRole.UserRole:
            return self.__data[self.__group][index.row()]
        return None

    def setData(self, index: QModelIndex | QPersistentModelIndex, value: dict, /, role = ...):
        """
        Ändert Zugriffsdaten im Model.
        :param index: Index der Zugriffsdaten
        :param value: komplette Zugriffsdaten
        :param role: Typ-Selektor
        """
        if index.row() < 0:
            # neue Zugriffsdaten
            self.beginInsertRows(QModelIndex(), index.row(), index.row())
            self.__data[self.__group].append(value)
            self.endInsertRows()
            self.rowsInserted.emit(index, len(self.__data[self.__group]), 1)
            self.layoutChanged.emit()
        else:
            # existierende Zugriffsdaten
            _model_data = self.__data[self.__group][index.row()]
            _value_alias = value.get(CFG_PAR_ALIAS)
            if _value_alias is not None and _value_alias != _model_data[CFG_PAR_ALIAS]:
                # Alias wurde umbenannt, Referenzen in den Backup-Zielen aktualisieren
                self.__data.element_renamed(self.__group, _model_data[CFG_PAR_ALIAS], _value_alias)
            _model_data.update(value)


class CredentialNamesModel(ConfigGroupNamesModel):
    """
    Model für Combobox-Widgets, die nur mit dem Aliasnamen von Zugriffsdaten arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__(CFG_GROUP_CREDENTIALS, configuration_data)


class CredentialsModel(ConfigGroupModel):
    """
    Model für Widgets, die mit Zugriffsdaten arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__(CFG_GROUP_CREDENTIALS, configuration_data)


class ScopeNamesModel(ConfigGroupNamesModel):
    """
    Model für Combobox-Widgets, die nur den Aliasnamen von Backup-Umfängen arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__(CFG_GROUP_SCOPE, configuration_data)


class ScopeModel(ConfigGroupModel):
    """
    Model für Widgets, die mit Backup-Umfängen arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__(CFG_GROUP_SCOPE, configuration_data)


class TargetNamesModel(ConfigGroupNamesModel):
    """
    Model für Combobox-Widgets, die nur den Aliasnamen von Backup-Zielen arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__(CFG_GROUP_TARGET, configuration_data)


class TargetModel(ConfigGroupModel):
    """
    Model für Widgets, die mit Backup-Zielen arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__(CFG_GROUP_TARGET, configuration_data)


class ConfigModelFactory:
    """
    Models für die gesamte restix-Konfiguration.
    """

    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__()
        self.__data = configuration_data
        self.__credential_names_model = CredentialNamesModel(configuration_data)
        self.__credentials_model = CredentialsModel(configuration_data)
        self.__scope_names_model = ScopeNamesModel(configuration_data)
        self.__scope_model = ScopeModel(configuration_data)
        self.__target_names_model = TargetNamesModel(configuration_data)
        self.__target_model = TargetModel(configuration_data)

    def credential_names_model(self) -> CredentialNamesModel:
        """
        :returns: Model für die Anzeige der Aliasnamen von Zugriffsdaten in einer Combo-Box
        """
        return self.__credential_names_model

    def credentials_model(self) -> CredentialsModel:
        """
        :returns: Model für die Anzeige von Zugriffsdaten in einer Pane
        """
        return self.__credentials_model

    def scope_names_model(self) -> ScopeNamesModel:
        """
        :returns: Model für die Anzeige der Aliasnamen von Zugriffsdaten in einer Combo-Box
        """
        return self.__scope_names_model

    def scope_model(self) -> ScopeModel:
        """
        :returns: Model für die Anzeige von Zugriffsdaten in einer Pane
        """
        return self.__scope_model

    def target_names_model(self) -> TargetNamesModel:
        """
        :returns: Model für die Anzeige der Aliasnamen von Backup-Zielen in einer Combo-Box
        """
        return self.__target_names_model

    def target_model(self) -> TargetModel:
        """
        :returns: Model für die Anzeige von Backup-Zielen in einer Pane
        """
        return self.__target_model

    def configuration_data(self) -> LocalConfig:
        """
        :returns: Lokale restix-Konfiguration
        """
        return self.__data
