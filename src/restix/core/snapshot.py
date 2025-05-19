# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# issai - Framework to run tests specified in Kiwi Test Case Management System
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
Modelliert Snapshots von restic Repositories.
"""

from datetime import datetime

from restix.core import *
from restix.core.messages import *


class SnapshotElement:
    """
    Einzelnes Element in einem restic Snapshot.
    """
    def __init__(self, element_path: str, element_type: str):
        """
        Konstruktor.
        :param element_path: Name des Elements inklusive Pfad.
        :param element_type: Typ des Elements ('d' für Verzeichnis, 'f' für Datei)
        """
        self.__path = element_path
        self.__type = element_type

    def path(self) -> str:
        """
        :returns: vollständiger Element-Pfad
        """
        return self.__path

    def type(self) -> str:
        """
        :returns: Element-Typ
        """
        return self.__type

    def path_parts(self) -> list[str]:
        """
        :returns: alle Teile des vollständigen Element-Pfads
        """
        return self.__path.split(os.sep)[1:]

    def path_part_count(self) -> int:
        """
        :returns: Anzahl aller Teile des vollständigen Element-Pfads
        """
        return len(self.__path.split(os.sep)) - 1

    def is_dir(self) -> bool:
        """
        :returns: True, falls das Element ein Verzeichnis ist
        """
        return self.__type == ELEMENT_TYPE_DIR

    def __str__(self) -> str:
        """
        :returns: Daten des Snapshot-Elements in lesbarer Form.
        """
        return f'{self.__path}[{self.__type}]'


class Snapshot:
    """
    Daten eines restic Snapshots.
    """
    def __init__(self, snapshot_id: str, time_stamp: datetime, tag: str):
        """
        Konstruktor.
        :param snapshot_id: Snapshot-ID
        :param time_stamp: Zeitstempel des Snapshots
        :param tag: erster Tag des Snapshots; Leerstring, falls kein Tag
        """
        self.__snapshot_id = snapshot_id
        self.__time_stamp = time_stamp
        self.__tags = [] if tag is None or len(tag) == 0 else [tag]
        self.__elements = None

    def add_tag(self, tag: str):
        """
        :param tag: hinzuzufügender Tag
        """
        self.__tags.append(tag)

    def add_element(self, element: SnapshotElement):
        """
        :param element: hinzuzufügendes Element
        """
        if self.__elements is None:
            self.__elements = [element]
        else:
            self.__elements.append(element)

    def add_elements(self, elements: list[SnapshotElement]):
        """
        :param elements: hinzuzufügende Elemente
        """
        if self.__elements is None:
            self.__elements = elements
        else:
            self.__elements.extend(elements)

    def snapshot_id(self) -> str:
        """
        :returns: Snapshot-ID
        """
        return self.__snapshot_id

    def time_stamp(self) -> datetime:
        """
        :returns: Zeitstempel des Snapshots
        """
        return self.__time_stamp

    def tags(self) -> list[str]:
        """
        :returns: Tags des Snapshots
        """
        return self.__tags

    def combo_label(self) -> str:
        """
        :returns: Daten des Snapshots zur Anzeige in einer Combo-Box
        """
        _tags = '' if len(self.__tags) == 0 else f' [{",".join(self.__tags)}]'
        _time = self.__time_stamp.strftime('%Y-%m-%d %H:%M:%S')
        return f'{self.__snapshot_id} - {_time}{_tags}'

    def month(self) -> int:
        """
        :returns: Monat des Snapshot-Zeitstempels
        """
        return self.__time_stamp.month

    def is_tagged_with(self, tag: str) -> bool:
        """
        :param tag: zu prüfender Tag
        :returns: True, falls der Snapshot den angegebenen Tag besitzt
        """
        return tag in self.__tags

    def element_tree(self) -> dict:
        """
        :returns: Name und Typ aller Elemente in hierarchischer Form
        """
        _nodes = {}
        for _element in self.__elements:
            _node = _nodes
            _no_of_path_parts = _element.path_part_count()
            for _i, _p in enumerate(_element.path_parts()):
                if _node.get(_p) is None:
                    if _i == _no_of_path_parts - 1:
                        # letzter Teil des Element-Pfads
                        _node[_p] = {ATTR_NAME: _p, ATTR_TYPE: _element.type(), ATTR_CHILDREN: {}}
                    else:
                        _node[_p] = {ATTR_NAME: _p, ATTR_TYPE: ELEMENT_TYPE_DIR, ATTR_CHILDREN: {}}
                _node = _node.get(_p).get(ATTR_CHILDREN)
        return _nodes

    def __str__(self) -> str:
        """
        :returns: Inhalt des Snapshots in lesbarer Form.
        """
        _snapshot_data = f'ID:{self.__snapshot_id}/TIME:{self.__time_stamp}/TAGS:{",".join(self.__tags)}'
        if self.__elements is None:
            return _snapshot_data
        _element_data = os.linesep.join([str(_e) for _e in self.__elements])
        return f'{_snapshot_data}{os.linesep}{_element_data}'
