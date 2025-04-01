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

from PySide6 import QtCore
from PySide6.QtCore import qVersion, Qt, QPoint
from PySide6.QtWidgets import (QWidget, QLabel, QDialog, QPushButton,
                               QMessageBox, QGridLayout, QVBoxLayout, QGroupBox, QHBoxLayout, QSizePolicy, QLineEdit,
                               QTreeWidget, QTreeWidgetItem, QStyle, QFileDialog, QTreeView)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.gui.model import CheckBoxFileSystemModel


class CheckBoxFileViewer(QTreeView):
    def __init__(self, parent):
        super().__init__(parent)
        self.__model = CheckBoxFileSystemModel()
        self.__model.setRootPath('')
        self.setModel(self.__model)


class ScopeEditor(QDialog):
    """
    Editor zum Auswählen der ein- und auszuschliessenden Elemente eines Backup-Umfangs.
    """
    def __init__(self, parent: QWidget, includes_file_path: str | None, excludes_file_path: str | None):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param includes_file_path: Pfad und Name der Datei, in der die einzuschliessenden Elemente enthalten sind.
        :param excludes_file_path: Pfad und Name der Datei mit den auszuschliessenden Elementen.
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_SCOPE_EDITOR))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _SCOPE_EDITOR_OFFSET, _parent_rect.y() + _SCOPE_EDITOR_OFFSET,
                         _SCOPE_EDITOR_WIDTH, _SCOPE_EDITOR_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QVBoxLayout(self)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # oberer Bereich Tree-Viewer mit dem Dateisystem
        self.__tree_viewer = CheckBoxFileViewer(self)
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


_SAVE_DIALOG_HEIGHT = 240
_SAVE_DIALOG_OFFSET = 80
_SAVE_DIALOG_WIDTH = 360
_SCOPE_EDITOR_HEIGHT = 720
_SCOPE_EDITOR_OFFSET = 10
_SCOPE_EDITOR_WIDTH = 1200

_STYLE_INPUT_FIELD = 'background-color: #ffffcc'
_STYLE_WHITE_BG = 'background-color: white'
_STYLE_BOLD_TEXT = 'font-weight: bold'
_STYLE_EXCEPTION_BOX_INFO = 'QLabel#qt_msgbox_informativelabel {font-weight: bold}'
_STYLE_RUN_BUTTON = 'background-color: green; color: white; font-weight: bold'
