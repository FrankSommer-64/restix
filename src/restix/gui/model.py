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
Models der restix-Konfiguration zur Nutzung in der GUI.
"""

import os.path
import re

from typing import Any

from PySide6.QtCore import Qt, QAbstractItemModel, QAbstractListModel, QDir, QModelIndex, QPersistentModelIndex
from PySide6.QtGui import QColorConstants
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
        self.__includes = set([_f.rstrip(os.sep) for _f in includes])
        self.__excludes = set([_f.rstrip(os.sep) for _f in excludes])
        self.__ignore_patterns = CheckBoxFileSystemModel._regex_patterns_for(ignores)
        self.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden)

    def excludes(self) -> list[str]:
        """
        :returns: alle nicht in die Sicherung einzuschließende Elemente
        """
        return sorted(list(self.__excludes))

    def includes(self) -> list[str]:
        """
        :returns: alle in die Sicherung einzuschließende Elemente
        """
        return sorted(list(self.__includes))

    def flags(self, index: QModelIndex | QPersistentModelIndex, /) -> Qt.ItemFlag:
        """
        Erlaubt für alle angezeigten Elemente ausser dem Wurzelverzeichnis das Bearbeiten der
        Checkbox vor dem Element-Namen.
        :param index: Index des Elements
        :returns: Flags für das Element
        """
        _flags = super().flags(index)
        if index.isValid() and index.column() == 0 and index.parent().isValid():
            _flags |= Qt.ItemFlag.ItemIsUserCheckable
        return _flags

    def data(self, index: QModelIndex | QPersistentModelIndex, role = Qt.ItemDataRole.DisplayRole):
        """
        Gibt eine Eigenschaft eines Elements im Tree zurück. In der Implementierung wird nur der Checkbox-Status und
        die Vordergrundfarbe des Element-Namens behandelt, der Rest wird der Basisklasse überlassen.
        :param index: Index des Elements
        :param role: Selektor für die Eigenschaft
        :returns: Daten der Eigenschaft des Elements mit angegebenem Index
        """
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            # Checkbox-Status
            if not index.isValid() or not index.parent().isValid():
                # Filesystem-Root ist immer unchecked
                return Qt.CheckState.Unchecked.value
            _element_path = self.filePath(index)
            if self._element_or_ancestor_ignored(_element_path):
                # Element selbst oder übergeordnetes Element ist in der Ignore-Liste,
                # dann hat das Element immer den Status Unchecked
                return Qt.CheckState.Unchecked.value
            if self._element_or_ancestor_excluded(_element_path):
                # Element selbst oder übergeordnetes Element ist in der Excludes-Liste,
                # dann hat das Element den Status Unchecked
                return Qt.CheckState.Unchecked.value
            if self._element_or_ancestor_included(_element_path):
                # Element selbst oder übergeordnetes Element ist in der Includes-Liste,
                # dann hat das Element den Status Checked
                return Qt.CheckState.Checked.value
            if self._descendant_included(_element_path):
                # Untergeordnetes Element ist in der Includes-Liste,
                # dann hat das Element den Status PartiallyChecked
                return Qt.CheckState.PartiallyChecked.value
            return Qt.CheckState.Unchecked.value
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 0:
            # Vordergrundfarbe
            _element_path = self.filePath(index)
            if not index.parent().isValid() or self._element_or_ancestor_ignored(_element_path):
                # Root-Element oder ignoriertes Element
                return QColorConstants.LightGray
            if self._element_or_ancestor_excluded(_element_path):
                # Element selbst oder übergeordnetes Element ist in der Excludes-Liste
                return QColorConstants.DarkRed
            if _element_path in self.__includes:
                # Element ist in der Includes-Liste
                return QColorConstants.DarkGreen
            return QColorConstants.Black
        # alles andere an die Basisklasse weiterreichen
        return super().data(index, role)

    def setData(self, index: QModelIndex | QPersistentModelIndex, value: Any,
                role: Qt.ItemDataRole = Qt.ItemDataRole.EditRole) -> bool:
        """
        Ändert die Eigenschaft eines Elements im Tree. In der Implementierung wird
        nur der Checkbox-Status behandelt, der Rest wird der Basisklasse überlassen.
        :param index: Index des Elements
        :param value: Wert der Eigenschaft des Elements, Checkbox-Status wird als int übergeben
                      (nicht als Qt.CheckState !)
        :param role: Selektor für die Eigenschaft
        :returns: True, falls die Eigenschaft geändert wurde
        """
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
            print(f'setData {self.filePath(index)} value={value}')
            # Checkbox-Status, value wird als int übergeben (nicht als Qt.CheckState !)
            if not index.isValid() or not index.parent().isValid():
                print('setData invalid index not accepted')
                return False
            _element_path = self.filePath(index)
            if self._element_or_ancestor_ignored(_element_path):
                # Element oder übergeordnetes Element in der Liste der zu ignorierenden Elemente,
                # Checkbox-Status immer unchecked
                print('setData element or ancestor is ignored')
                return value == Qt.CheckState.Unchecked.value
            if value == Qt.CheckState.Checked.value:
                if self._ancestor_excluded(_element_path):
                    # übergeordnetes Element in der Liste der auszuschliessenden Elemente,
                    # Element kann nicht angehakt werden
                    print('setData ancestor is excluded')
                    return False
                if _element_path in self.__excludes:
                    print('setData element removed from excludes')
                    CheckBoxFileSystemModel._remove_from_scope_list(self.__excludes, _element_path)
                CheckBoxFileSystemModel._add_to_scope_list(self.__includes, _element_path)
                self._update_tree(index)
                return True
            if value == Qt.CheckState.Unchecked.value:
                if _element_path in self.__includes:
                    CheckBoxFileSystemModel._remove_from_scope_list(self.__includes, _element_path)
                    self._update_tree(index)
                    return True
                CheckBoxFileSystemModel._add_to_scope_list(self.__excludes, _element_path)
                self._update_tree(index)
                return True
        # alles andere an die Basisklasse weiterreichen
        return super().setData(index, value, role)

    def _update_tree(self, index: QModelIndex | QPersistentModelIndex):
        """
        Aktualisiert den angegebenen Index mitsamt aller über- und untergeordneten Elemente.
        :param index: Index des Elements
        """
        # Element selbst aktualisieren
        self.dataChanged.emit(index, index, Qt.ItemDataRole.CheckStateRole)
        self.dataChanged.emit(index, index, Qt.ItemDataRole.ForegroundRole)
        # übergeordnete Elemente einzeln aktualisieren
        _parent_index = index.parent()
        while _parent_index.isValid() and _parent_index.parent().isValid():
            self.dataChanged.emit(_parent_index, _parent_index, Qt.ItemDataRole.CheckStateRole)
            self.dataChanged.emit(_parent_index, _parent_index, Qt.ItemDataRole.ForegroundRole)
            _parent_index = _parent_index.parent()
        # untergeordnete en bloc aktualisieren
        self._update_children(index)

    def _update_children(self, index: QModelIndex | QPersistentModelIndex):
        """
        Aktualisiert die direkt untergeordneten Elemente.
        :param index: Index des Elements
        """
        _child_count = self.rowCount(index)
        if _child_count == 0:
            return
        _top_index = self.index(0, 0, index)
        _bottom_index = _top_index
        for _row in range(0, _child_count):
            _bottom_index = self.index(_row, 0, index)
            self._update_children(_bottom_index)
        self.dataChanged.emit(_top_index, _bottom_index, Qt.ItemDataRole.CheckStateRole)
        self.dataChanged.emit(_top_index, _bottom_index, Qt.ItemDataRole.ForegroundRole)

    def _element_or_ancestor_ignored(self, file_path: str) -> bool:
        """
        :param file_path: vollständiger Pfad des Elements
        :returns: True, falls das Element selbst oder ein übergeordnetes Element
                  in der Liste der zu ignorierenden Elemente enthalten ist
        """
        _element_path_parts = file_path.split(os.sep)
        if len(_element_path_parts[1]) == 0:
            # File-System-Root
            return False
        for _p in _element_path_parts[1:]:
            for _pattern in self.__ignore_patterns:
                if _pattern.fullmatch(_p):
                    return True
        return False

    def _ancestor_excluded(self, file_path: str) -> bool:
        """
        :param file_path: vollständiger Pfad des Elements
        :returns: True, falls ein übergeordnetes Element in der excludes-Liste enthalten ist
        """
        return CheckBoxFileSystemModel._element_or_ancestor_in(self.__excludes, file_path, False)

    def _element_or_ancestor_excluded(self, file_path: str) -> bool:
        """
        :param file_path: vollständiger Pfad des Elements
        :returns: True, falls das Element selbst oder ein übergeordnetes Element
                  in der excludes-Liste enthalten ist
        """
        return CheckBoxFileSystemModel._element_or_ancestor_in(self.__excludes, file_path)

    def _element_or_ancestor_included(self, file_path: str) -> bool:
        """
        :param file_path: vollständiger Pfad des Elements
        :returns: True, falls das Element selbst oder ein übergeordnetes Element
                  in der includes-Liste enthalten ist
        """
        return CheckBoxFileSystemModel._element_or_ancestor_in(self.__includes, file_path)

    def _descendant_included(self, file_path: str) -> bool:
        """
        :param file_path: vollständiger Pfad des Elements
        :returns: True, falls ein untergeordnetes Element in der include-Liste enthalten ist
        """
        _elem_length = len(file_path)
        for _inc in self.__includes:
            if len(_inc) <= _elem_length:
                continue
            if _inc.startswith(file_path):
                return True
        return False

    @classmethod
    def _element_or_ancestor_in(cls, internal_list: set[str], file_path: str,
                                include_element: bool = True) -> bool:
        """
        :param file_path: vollständiger Pfad des Elements
        :returns: True, falls das Element selbst oder ein übergeordnetes Element
                  in der excludes-Liste enthalten ist
        """
        _element_path_parts = file_path.split(os.sep)
        if len(_element_path_parts[1]) == 0:
            # File-System-Root
            return False
        _part = ''
        _parts = _element_path_parts[1:] if include_element else _element_path_parts[1:-1]
        for _p in _parts:
            _part = f'{_part}{os.sep}{_p}'
            if _part in internal_list:
                return True
        return False

    @classmethod
    def _add_to_scope_list(cls, scope_list: set[str], file_path: str):
        """
        Fügt ein Element zu den Excludes oder Includes hinzu.
        :param scope_list: Exclude- oder Include-Liste
        :param file_path: vollständiger Pfad des Elements
        """
        if CheckBoxFileSystemModel._element_or_ancestor_in(scope_list, file_path):
            # Element oder übergeordnetes Element schon in der Liste
            print(f'_add_to_scope_list ignored {file_path}, element or parent already in list')
            return
        if os.path.isdir(file_path):
            # Element ist ein Verzeichnis, ggf. alle Elemente unterhalb aus der Liste entfernen
            _elements_to_remove = [_f for _f in scope_list if _f.startswith(file_path)]
            for _e in _elements_to_remove:
                print(f'_add_to_scope_list removed {_e}')
                scope_list.remove(_e)
        print(f'_add_to_scope_list added {file_path}')
        scope_list.add(file_path)

    @classmethod
    def _remove_from_scope_list(cls, scope_list: set[str], file_path: str):
        """
        Entfernt ein Element aus den Excludes oder Includes.
        :param scope_list: Exclude- oder Include-Liste
        :param file_path: vollständiger Pfad des Elements
        """
        if file_path in scope_list:
            print(f'_remove_from_scope_list {file_path}')
            scope_list.remove(file_path)

    @classmethod
    def _regex_patterns_for(cls, patterns: list[str]) -> list[re.Pattern]:
        """
        Wandelt die Patterns für zu ignorierende Dateien aus der restix-Konfiguration
        in reguläre Ausdrücke um.
        :param patterns: Patterns aus der restix-Konfiguration
        :returns: Patterns als reguläre Ausdrücke
        """
        _regex_patterns = []
        for _pattern in patterns:
            if len(_pattern) == 0:
                continue
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
