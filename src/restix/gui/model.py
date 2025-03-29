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

from PySide6.QtCore import Qt, Signal, QObject, QAbstractProxyModel, QAbstractListModel, QModelIndex, \
    QPersistentModelIndex

from restix.core import *
from restix.core.config import LocalConfig


class CredentialNamesModel(QAbstractListModel):
    """
    Model für Combobox-Widgets, die nur mit dem Namen von Zugriffsdaten arbeiten.
    """
    def __init__(self, configuration_data: LocalConfig):
        """
        Konstruktor.
        :param configuration_data: die Daten aus der lokalen restix-Konfigurationsdatei
        """
        super().__init__()
        self.__data = configuration_data
        #self.rowsAboutToBeInserted.connect(self._add_credential_requested)
        self.rowsAboutToBeRemoved.connect(self._remove_credential_requested)

    def rowCount(self, /, parent: QModelIndex | QPersistentModelIndex= ...) -> int:
        """
        :param parent:
        :returns: Anzahl der Zugriffsdaten-Elemente
        """
        return len(self.__data[CFG_GROUP_CREDENTIALS])

    def data(self, index: QModelIndex | QPersistentModelIndex, /, role: int = ...) -> Any:
        if not index.isValid() or index.row() >= len(self.__data[CFG_GROUP_CREDENTIALS]):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.__data[CFG_GROUP_CREDENTIALS][index.row()][CFG_PAR_NAME]
        if role == Qt.ItemDataRole.UserRole:
            return self.__data[CFG_GROUP_CREDENTIALS][index.row()]
        return None

    def setData(self, index, value, /, role = ...):
        if index.row() < 0:
            print('new credential')
            self.beginInsertRows(QModelIndex(), index.row(), index.row())
            self.__data[CFG_GROUP_CREDENTIALS].append(value)
            self.endInsertRows()
            self.rowsInserted.emit(index, len(self.__data[CFG_GROUP_CREDENTIALS]), 1)
            self.layoutChanged.emit()
        else:
            print('existing credential')
            self.__data[CFG_GROUP_CREDENTIALS][index.row()].update(value)
            self.dataChanged.emit()

    def removeRow(self, row, /, parent = ...) -> bool:
        print('removeRow')
        self.beginRemoveRows(QModelIndex(), row, row)
        print('after beginRemoveRows')
        self.endRemoveRows()
        return False

    def _add_credential_requested(self):
        print('_add_credential_requested')

    def _remove_credential_requested(self):
        print('_remove_credential_requested')


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

    def credential_names_model(self) -> CredentialNamesModel:
        return self.__credential_names_model

    def configuration_data(self) -> LocalConfig:
        return self.__data

