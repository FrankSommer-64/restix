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
from PySide6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QMessageBox, QPushButton, QTreeView,
                               QVBoxLayout, QWidget)

from restix.core.messages import *
from restix.core.util import full_config_path_of
from restix.gui import EDITOR_STYLE
from restix.gui.model import CheckBoxFileSystemModel


class CheckBoxFileViewer(QTreeView):
    """
    Dateisystem-Viewer mit Checkboxen zur Auswahl von Dateien und Verzeichnissen.
    """
    def __init__(self, parent, includes: list[str], excludes: list[str], ignores: list[str]):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param includes: in die Sicherung einzuschließende Dateien und Verzeichnisse
        :param excludes: aus der Sicherung auszuschließende Dateien und Verzeichnisse
        :param ignores: Pattern mit zu ignorierenden Dateien und Verzeichnissen
        """
        super().__init__(parent)
        self.__model = CheckBoxFileSystemModel(includes, excludes, ignores)
        self.__model.setRootPath('')
        self.setModel(self.__model)
        self.setColumnWidth(0, _SCOPE_EDITOR_WIDTH >> 1)

    def excludes(self) -> list[str]:
        """
        :returns: alle nicht in die Sicherung einzuschließende Elemente
        """
        return self.__model.excludes()

    def includes(self) -> list[str]:
        """
        :returns: alle in die Sicherung einzuschließende Elemente
        """
        return self.__model.includes()


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
        self.__preferred_out_path = config_path if includes_file_path is None\
            else os.path.dirname(full_config_path_of(includes_file_path, config_path))
        self.setWindowTitle(localized_label(L_DLG_TITLE_SCOPE_EDITOR))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _SCOPE_EDITOR_OFFSET, _parent_rect.y() + _SCOPE_EDITOR_OFFSET,
                         _SCOPE_EDITOR_WIDTH, _SCOPE_EDITOR_HEIGHT)
        self.setStyleSheet(EDITOR_STYLE)
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
        if includes_file_path is not None:
            _save_as_button = QPushButton(localized_label(L_SAVE_AS))
            _save_as_button.clicked.connect(self._save_as_button_clicked)
            _button_pane_layout.addWidget(_save_as_button)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.clicked.connect(self.reject)
        _button_pane_layout.addWidget(_cancel_button)
        _layout.addWidget(_button_pane)

    def scope_files(self) -> tuple[str, str | None]:
        """
        :returns: Name der Includes-Datei, Name der Excludes-Datei
        """
        return self.__includes_file_path, self.__excludes_file_path

    def _save_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer auf den "Speichern"-Button klickt.
        Speichert Includes und ggf. Excludes in den Dateien, aus denen die geladen wurden.
        """
        self._save_scope()

    def _save_as_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer auf den "Speichern unter"-Button klickt.
        Speichert Includes und ggf. Excludes in neuen Dateien.
        """
        self.__includes_file_path = self.__excludes_file_path = None
        self._save_scope()

    def _save_scope(self):
        """
        Speichert den Sicherungsumfang in Dateien.
        """
        _includes = self.__tree_viewer.includes()
        if len(_includes) == 0:
            QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                    localized_label(I_GUI_NO_INCLUDES_SPECIFIED),
                                    QMessageBox.StandardButton.Ok)
            return
        self.__includes_file_path = self._save_scope_elements(_includes, self.__includes_file_path,
                                                              L_DLG_TITLE_SELECT_INCLUDES_FILE)
        if self.__includes_file_path is None:
            return
        _excludes = self.__tree_viewer.excludes()
        self.__excludes_file_path = self._save_scope_elements(_excludes, self.__excludes_file_path,
                                                              L_DLG_TITLE_SELECT_EXCLUDES_FILE)
        if len(_excludes) > 0 and self.__excludes_file_path is None:
            return
        self.accept()

    def _save_scope_elements(self, elements: list[str], file_path: str, dlg_title_id: str) -> str | None:
        """
        Speichert eine Liste von Include- oder Exclude-Dateien in Datei.
        :param elements: Liste der Include- oder Exclude-Dateien
        :param file_path: Name der Ausgabedatei
        :param dlg_title_id: Resource-ID für das Dialogfenster zur Auswahl eines Ausgabedatei-Namens
        :returns: Name und Pfad der Ausgabedatei; None, falls die Element-Liste leer ist oder der Benutzer den
                  Dialog zur Auswahl eines Ausgabedatei-Namens abgebrochen hat
        """
        _output_file_path = file_path
        if len(elements) > 0:
            if _output_file_path is None:
                _output_file_path, _filter = QFileDialog.getSaveFileName(self, localized_label(dlg_title_id),
                                                                         self.__preferred_out_path)
                if len(_output_file_path) == 0:
                    return None
            element_lines = [f'{_element}{os.linesep}' for _element in elements]
            with open(_output_file_path, 'w') as _f:
                _f.writelines(element_lines)
            return _output_file_path
        return None

    def _read_file(self, file_path) -> list[str]:
        """
        Liest eine Datei mit includes oder excludes ein. Falls der Dateiname nicht absolut angegeben wurde, wird diese
        unterhalb des restix-Konfigurationsverzeichnisses gesucht.
        :param file_path: Dateiname
        :returns: zeilenweiser Inhalt der Datei
        """
        if file_path is None:
            return []
        _file_path = file_path if os.path.isabs(file_path) else os.path.join(self.__config_path, file_path)
        if not os.path.isfile(_file_path):
            return []
        with open(_file_path, 'r') as _f:
            return _f.read().splitlines()


_SCOPE_EDITOR_HEIGHT = 600
_SCOPE_EDITOR_OFFSET = 40
_SCOPE_EDITOR_WIDTH = 1200
