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
Editoren für die restix GUI.
"""
import os.path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QTreeView

from restix.core.messages import *
from restix.gui.model import CheckBoxFileSystemModel


class CheckBoxFileViewer(QTreeView):
    def __init__(self, parent, includes: list[str], excludes: list[str], ignores: list[str]):
        super().__init__(parent)
        self.__model = CheckBoxFileSystemModel(includes, excludes, ignores)
        self.__model.setRootPath('')
        self.setModel(self.__model)
        self.setColumnWidth(0, _SCOPE_EDITOR_WIDTH >> 1)


class ScopeEditor(QDialog):
    """
    Editor zum Auswählen der ein- und auszuschliessenden Elemente eines Backup-Umfangs.
    """
    def __init__(self, parent: QWidget, config_path: str, includes_file_path: str | None,
                 excludes_file_path: str | None, ignore_list: list[str]):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param config_path: Verzeichnis der lokalen restix-Konfiguration.
        :param includes_file_path: Pfad und Name der Datei, in der die einzuschliessenden Elemente enthalten sind.
        :param excludes_file_path: Pfad und Name der Datei mit den auszuschliessenden Elementen.
        :param ignore_list: Patterns zu ignorierender Elemente.
        """
        super().__init__(parent)
        self.__config_path = config_path
        self.__includes_file_path = includes_file_path
        self.__excludes_file_path = excludes_file_path
        self.setWindowTitle(localized_label(L_DLG_TITLE_SCOPE_EDITOR))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _SCOPE_EDITOR_OFFSET, _parent_rect.y() + _SCOPE_EDITOR_OFFSET,
                         _SCOPE_EDITOR_WIDTH, _SCOPE_EDITOR_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QVBoxLayout(self)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # oberer Bereich Tree-Viewer mit dem Dateisystem
        self.__tree_viewer = CheckBoxFileViewer(self, self._read_file(includes_file_path),
                                                self._read_file(excludes_file_path), ignore_list)
        _layout.addWidget(self.__tree_viewer)
        # unterer Bereich Buttons zum Speichern und Abbrechen
        _button_pane = QWidget(self)
        _button_pane_layout = QHBoxLayout(_button_pane)
        _button_pane_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        _save_button = QPushButton(localized_label(L_SAVE))
        _save_button.clicked.connect(self._save_button_clicked)
        _button_pane_layout.addWidget(_save_button)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.clicked.connect(self.reject)
        _button_pane_layout.addWidget(_cancel_button)
        _layout.addWidget(_button_pane)

    def _save_button_clicked(self):
        print('_save_button_clicked')
        self.accept()

    def _read_file(self, file_path) -> list[str]:
        if file_path is None:
            return []
        _file_path = file_path if os.path.isabs(file_path) else os.path.join(self.__config_path, file_path)
        if not os.path.isfile(_file_path):
            return []
        with open(_file_path, 'r') as _f:
            return _f.read().splitlines()


_SAVE_DIALOG_HEIGHT = 240
_SAVE_DIALOG_OFFSET = 80
_SAVE_DIALOG_WIDTH = 360
_SCOPE_EDITOR_HEIGHT = 720
_SCOPE_EDITOR_OFFSET = 10
_SCOPE_EDITOR_WIDTH = 1200

_STYLE_WHITE_BG = 'background-color: white'
