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
Dialogfenster für die arestix GUI.
"""

import datetime
import os.path
import tomli
import tomli_w

from typing import Callable

from PySide6 import QtCore
from PySide6.QtCore import qVersion, Qt
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QSizePolicy, QStyle, QTextEdit,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from arestix.core import *
from arestix.core.action import ArestixAction
from arestix.core.config import LocalConfig
from arestix.core.messages import *
from arestix.core.restic_interface import find_snapshot_elements, list_snapshot_elements
from arestix.core.snapshot import Snapshot
from arestix.gui import *


class TextFileViewerDialog(QDialog):
    """
    Zeigt den Inhalt einer Textdatei an.
    Wird für die Lizenzen benötigt.
    """
    def __init__(self, parent: QWidget, title_id: str, text: str):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param title_id: Resource-ID der Fensterüberschrift
        :param text: anzuzeigender Text
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(title_id))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _TEXT_FILE_VIEWER_OFFSET, _parent_rect.y() + _TEXT_FILE_VIEWER_OFFSET,
                         _TEXT_FILE_VIEWER_WIDTH, _TEXT_FILE_VIEWER_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QVBoxLayout(self)
        _text = QTextEdit(self, plainText=text, readOnly=True)
        _layout.addWidget(_text)


class SnapshotViewerDialog(QDialog):
    """
    Zeigt den Inhalt eines Snapshots an.
    Bietet die Möglichkeit, nach gesicherten Elementen zu suchen.
    Ermöglicht die Auswahl einzelner Elemente für die Wiederherstellung.
    """
    def __init__(self, parent: QWidget, snapshot_id: str, target_alias: str,
                 local_config: LocalConfig, hostname: str, year: str, pw: str):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param snapshot_id: ID des restic Snapshots.
        :param target_alias: Alias-Name des Backup-Ziels.
        :param local_config: lokale arestix-Konfiguration.
        :param hostname: Hostname, für den der Snapshot angelegt wurde.
        :param year: Jahr des restic Snapshots.
        """
        super().__init__(parent)
        self.__snapshot_id = snapshot_id
        self.__target_alias = target_alias
        self.__local_config = local_config
        self.__hostname = hostname
        self.__year = year
        self.__selected_elements = []
        self.__pw = pw
        self.setWindowTitle(localized_message(L_DLG_TITLE_SNAPSHOT_VIEWER, snapshot_id, hostname, year))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _SNAPSHOT_VIEWER_OFFSET, _parent_rect.y() + _SNAPSHOT_VIEWER_OFFSET,
                         _SNAPSHOT_VIEWER_WIDTH, _SNAPSHOT_VIEWER_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QVBoxLayout(self)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _viewer_pane = self._create_viewer_pane()
        _viewer_pane.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        _layout.addWidget(_viewer_pane)
        _action_pane = self._create_action_pane()
        _layout.addWidget(_action_pane)

    def selected_elements(self) -> list[str]:
        """
        :returns: Name und Pfad aller vom Benutzer ausgewählten Elemente
        """
        return self.__selected_elements

    def _create_viewer_pane(self) -> QGroupBox:
        """
        Erzeugt den oberen Bereich mit den Buttons zum Suchen oder Anzeigen des gesamten Snapshot-Inhalts.
        :returns: oberer Bereich des Dialogfensters
        """
        _group = QGroupBox(localized_label(L_SELECT_ELEMENTS))
        _group_layout = QVBoxLayout(_group)
        _group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _viewer_buttons_layout = QHBoxLayout()
        _show_all_button = QPushButton(localized_label(L_SHOW_ALL_ELEMENTS))
        _show_all_button.clicked.connect(self._show_full_snapshot)
        _viewer_buttons_layout.addWidget(_show_all_button)
        _search_button = QPushButton(localized_label(L_SEARCH))
        _search_button.clicked.connect(self._show_filtered_snapshot)
        _viewer_buttons_layout.addWidget(_search_button)
        self.__search_field = QLineEdit()
        self.__search_field.setStyleSheet(_STYLE_INPUT_FIELD)
        self.__search_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        _viewer_buttons_layout.addWidget(self.__search_field)
        _group_layout.addLayout(_viewer_buttons_layout)
        self.__tree_viewer = QTreeWidget(self)
        self.__tree_viewer.setColumnCount(1)
        self.__tree_viewer.setHeaderLabels([localized_label(L_ELEMENT)])
        self.__tree_viewer.itemChanged.connect(SnapshotViewerDialog._item_changed)
        _group_layout.addWidget(self.__tree_viewer)
        return _group

    @classmethod
    def _item_changed(cls, item: QTreeWidgetItem, column: int):
        """
        Wird aufgerufen, wenn der Benutzer die Checkbox eines Elements ändert. Setzt automatisch alle untergeordneten
        Elemente auf den gleichen Check-Status.
        :param item: das Element-Widget
        :param column: immer Spalte 0
        """
        _check_status = item.checkState(column)
        SnapshotViewerDialog._propagate_check_status(item, column, _check_status)

    @classmethod
    def _propagate_check_status(cls, item: QTreeWidgetItem, column: int, check_status: QtCore.Qt.CheckState):
        """
        Setzt den Checkbox-Status aller Nachkommen eines Snapshot-Elements auf den angegebenen Wert.
        :param item: Element-Widget
        :param column: immer Spalte 0
        :param check_status: Checkbox-Status
        """
        for _i in range(0, item.childCount()):
            _child = item.child(_i)
            _child.setCheckState(column, check_status)
            SnapshotViewerDialog._propagate_check_status(_child, column, check_status)

    def _create_action_pane(self) -> QWidget:
        """
        Erzeugt den unteren Bereich mit den Buttons zum Übernehmen der Selektion und zum Abbrechen des Dialogs.
        :returns: unterer Bereich des Dialogfensters
        """
        _button_pane = QWidget(self)
        _button_pane_layout = QHBoxLayout()
        _button_pane_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        _apply_button = QPushButton(localized_label(L_ADOPT_SELECTION))
        _apply_button.clicked.connect(self._adopt_selection)
        _button_pane_layout.addWidget(_apply_button)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.clicked.connect(self.reject)
        _button_pane_layout.addWidget(_cancel_button)
        _button_pane.setLayout(_button_pane_layout)
        return _button_pane

    def _show_full_snapshot(self):
        """
        Zeigt alle Elemente des Snapshots im Viewer an.
        """
        _options = {OPTION_HOST: self.__hostname, OPTION_YEAR: self.__year, OPTION_SNAPSHOT: self.__snapshot_id,
                    OPTION_JSON: True}
        if self.__pw is not None:
            _options[OPTION_PASSWORD] = self.__pw
        _action = ArestixAction.for_action_id(ACTION_LS, self.__target_alias, self.__local_config, _options)
        _snapshot = list_snapshot_elements(_action)
        _element_tree = _snapshot.element_tree()
        _tree_items = self._tree_items_for(_element_tree, os.sep)
        self.__tree_viewer.clear()
        self.__tree_viewer.addTopLevelItems(_tree_items)

    def _show_filtered_snapshot(self):
        """
        Zeigt die Elemente des Snapshots, die auf den eingegebenen Filter passen im Viewer an.
        """
        _options = {OPTION_HOST: self.__hostname, OPTION_YEAR: self.__year, OPTION_SNAPSHOT: self.__snapshot_id,
                    OPTION_JSON: True, OPTION_PATTERN: self.__search_field.text()}
        if self.__pw is not None:
            _options[OPTION_PASSWORD] = self.__pw
        _action = ArestixAction.for_action_id(ACTION_FIND, self.__target_alias, self.__local_config, _options)
        _elements = find_snapshot_elements(_action)
        _snapshot = Snapshot(self.__snapshot_id, datetime.datetime.now(), '')
        _snapshot.add_elements(_elements)
        _element_tree = _snapshot.element_tree()
        _tree_items = self._tree_items_for(_element_tree, os.sep)
        self.__tree_viewer.clear()
        self.__tree_viewer.addTopLevelItems(_tree_items)

    def _adopt_selection(self):
        """
        Übernimmt die im Viewer ausgewählten Elemente in eine interne Variable und schließt das Dialogfenster.
        """
        self.__selected_elements = [_item.data(0, Qt.ItemDataRole.UserRole) for _item in self._checked_items()]
        self.accept()

    def _checked_items(self, parent: QTreeWidgetItem = None) -> list[QTreeWidgetItem]:
        """
        :param parent: Widget des Parent-Elements; None für oberste Ebene
        :returns: Widgets aller ausgewählten Elemente unterhalb des angegebenen Parents
        """
        _items = []
        if parent is None:
            # gesamten Tree prüfen
            for _i in range(0, self.__tree_viewer.topLevelItemCount()):
                _item = self.__tree_viewer.topLevelItem(_i)
                if _item.checkState(0) == QtCore.Qt.CheckState.Checked:
                    _items.append(_item)
                _items.extend(self._checked_items(_item))
        else:
            # Elemente unterhalb des Parent-Widgets prüfen
            for _i in range(0, parent.childCount()):
                _item = parent.child(_i)
                if _item.checkState(0) == QtCore.Qt.CheckState.Checked:
                    _items.append(_item)
                _items.extend(self._checked_items(_item))
        return _items

    def _tree_items_for(self, node: dict, parent_path: str) -> list[QTreeWidgetItem]:
        """
        Erzeugt rekursiv für alle Nachkommen des übergebenen Snapshot-Elements ein Widget für den Tree-Viewer.
        :param node: Daten des Elements
        :returns: Widgets für alle untergeordneten Elemente
        """
        _children = []
        for _k, _v in node.items():
            _child_path = os.path.join(parent_path, _k)
            _child = QTreeWidgetItem()
            _child.setText(0, _k)
            _child.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            _child.setData(0, Qt.ItemDataRole.UserRole, _child_path)
            if _v.get(ATTR_TYPE) == ELEMENT_TYPE_DIR:
                _icon_pixmap = QStyle.StandardPixmap.SP_DirIcon
                _child.setIcon(0, self.style().standardIcon(_icon_pixmap))
            else:
                _icon_pixmap = QStyle.StandardPixmap.SP_FileIcon
                _child.setIcon(0, self.style().standardIcon(_icon_pixmap))
            _children.append(_child)
            if len(_v.get(ATTR_CHILDREN)) > 0:
                _child.addChildren(self._tree_items_for(_v.get(ATTR_CHILDREN), _child_path))
        return _children


class PdfViewerDialog(QDialog):
    """
    Zeigt eine PDF-Datei an.
    """
    def __init__(self, parent: QWidget, title_id: str, file_path: str):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param title_id: Resource-ID für die Fensterüberschrift
        :param file_path: Name und Pfad der anzuzeigenden PDF-Datei
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(title_id))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _PDF_VIEWER_OFFSET, _parent_rect.y() + _PDF_VIEWER_OFFSET,
                         _PDF_VIEWER_WIDTH, _PDF_VIEWER_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _dlg_layout = QVBoxLayout(self)
        _web_view = QWebEngineView()
        _view_settings = _web_view.settings()
        _view_settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        _view_settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        _web_view.load(f'file://{file_path}')
        _dlg_layout.addWidget(_web_view)


class AboutDialog(QDialog):
    """
    Zeigt Informationen über arestix an.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: das übergeordnete Widget
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_ABOUT))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _ABOUT_DIALOG_OFFSET, _parent_rect.y() + _ARESTIX_IMAGE_SIZE,
                         _ABOUT_DIALOG_WIDTH, _ABOUT_DIALOG_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _dlg_layout = QGridLayout(self)
        _dlg_layout.setSpacing(DEFAULT_SPACING)
        _arestix_image = QWidget()
        _arestix_image.setFixedSize(_ARESTIX_IMAGE_SIZE, _ARESTIX_IMAGE_SIZE)
        _arestix_image.setStyleSheet(_STYLE_ARESTIX_IMAGE)
        _dlg_layout.addWidget(_arestix_image, 0, 0, 3, 1, Qt.AlignmentFlag.AlignTop)
        _dlg_layout.addWidget(self._arestix_group_box(), 0, 1, Qt.AlignmentFlag.AlignTop)
        _dlg_layout.addWidget(self._third_party_group_box(), 1, 1, Qt.AlignmentFlag.AlignBottom)
        _ok_button = QPushButton(localized_label(L_OK))
        _ok_button.setStyleSheet(ACTION_BUTTON_STYLE)
        _ok_button.clicked.connect(self.close)
        _dlg_layout.addWidget(_ok_button, 2, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

    def _arestix_group_box(self) -> QGroupBox:
        """
        :returns: GroupBox für die Informationen zur arestix-Applikation
        """
        _group_box = QGroupBox(localized_label(L_ARESTIX))
        _group_box.setStyleSheet(GROUP_BOX_STYLE)
        _grp_layout = QGridLayout(_group_box)
        _grp_layout.setContentsMargins(DEFAULT_CONTENT_MARGIN, WIDE_CONTENT_MARGIN,
                                       DEFAULT_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _row = 0
        _row += AboutDialog._create_component_header(_grp_layout, _row, I_GUI_ARESTIX_INFO, I_GUI_ARESTIX_COPYRIGHT)
        AboutDialog._create_component_part(_grp_layout, _row, None, VERSION, self._show_mit_license,
                                           I_GUI_ARESTIX_LINK, _URL_ARESTIX)
        return _group_box

    def _third_party_group_box(self) -> QGroupBox:
        """
        :returns: GroupBox für die Informationen zu verwendeten Bibliotheken
        """
        _group_box = QGroupBox(localized_label(L_LIBRARIES))
        _group_box.setStyleSheet(GROUP_BOX_STYLE)
        _grp_layout = QGridLayout(_group_box)
        _grp_layout.setContentsMargins(DEFAULT_CONTENT_MARGIN, WIDE_CONTENT_MARGIN,
                                       DEFAULT_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        _row = 0
        _row += AboutDialog._create_component_header(_grp_layout, _row, I_GUI_PYSIDE_INFO, None)
        _row += AboutDialog._create_component_part(_grp_layout, _row, _COMPONENT_PART_PYSIDE, qVersion(),
                                                   self._show_lgpl_license, I_GUI_PYSIDE_LINK, _URL_PYSIDE)
        _grp_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken, lineWidth=1),
                              _row, 0, 1, 4)
        _row += 1
        _row += AboutDialog._create_component_header(_grp_layout, _row, I_GUI_TOML_LIB_INFO, I_GUI_TOML_LIB_COPYRIGHT)
        _row += AboutDialog._create_component_part(_grp_layout, _row, _COMPONENT_PART_TOMLI, tomli.__version__,
                                                   self._show_mit_license, I_GUI_TOMLI_LINK, _URL_TOMLI)
        _row += AboutDialog._create_component_part(_grp_layout, _row, _COMPONENT_PART_TOMLI_W, tomli_w.__version__,
                                                   self._show_mit_license, I_GUI_TOMLIW_LINK, _URL_TOMLI_W)
        _grp_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken, lineWidth=1),
                              _row, 0, 1, 4)
        _row += 1
        _row += AboutDialog._create_component_header(_grp_layout, _row, I_GUI_ICONS_INFO, I_GUI_ICONS_COPYRIGHT)
        _row += AboutDialog._create_component_part(_grp_layout, _row, None, None,
                                                   self._show_lgpl_license, I_GUI_ICONS_LINK, _URL_ICONS)
        return _group_box

    @classmethod
    def _create_component_header(cls, layout: QGridLayout, row: int, info_id: str, copyright_id: str | None) -> int:
        """
        Erzeugt die Header-Zeilen für die About-Informationen einer Komponente.
        :param row: nächste freie Zeile im Layout
        :param info_id: Resource-ID für den Namen des Komponenten-Teils
        :param copyright_id: Resource-ID für das Copyright des Komponenten-Teils
        :returns: Anzahl der erzeugten Zeilen im Layout
        """
        _component_row = row
        _component_info = QLabel(localized_message(info_id))
        _component_info.setStyleSheet(_STYLE_BOLD_TEXT)
        layout.addWidget(_component_info, _component_row, 0, 1, 4)
        _component_row += 1
        if copyright_id is not None:
            _copyright = QLabel(localized_message(copyright_id), textFormat=Qt.TextFormat.PlainText)
            layout.addWidget(_copyright, _component_row, 0, 1, 4)
            _component_row += 1
        return _component_row - row

    @classmethod
    def _create_component_part(cls, layout: QGridLayout, row: int, part_name: str | None,
                               version: str | None, license_slot: Callable, link_url_id: str, link_tooltip: str) -> int:
        """
        Erzeugt die About-Informationen für einen Teil einer Komponente.
        :param row: nächste freie Zeile im Layout
        :param part_name: Name des Komponenten-Teils
        :param version: Version des Komponenten-Teils
        :param license_slot: Funktion zum Anzeigen des Lizenz-Texts
        :param link_url_id: Resource-ID der URL zur Homepage des Komponenten-Teils
        :param link_tooltip: Tooltip mit der URL zur Homepage des Komponenten-Teils
        :returns: Anzahl der erzeugten Zeilen im Layout
        """
        if part_name is not None:
            layout.addWidget(QLabel(part_name), row, 0, Qt.AlignmentFlag.AlignRight)
        if version is not None:
            _version_text = QLabel(localized_message(I_GUI_VERSION, version))
            layout.addWidget(_version_text, row, 1, Qt.AlignmentFlag.AlignHCenter)
        _license = QPushButton(localized_label(L_LICENSE))
        _license.clicked.connect(license_slot)
        layout.addWidget(_license, row, 2, Qt.AlignmentFlag.AlignHCenter)
        _link = QLabel(localized_label(link_url_id), openExternalLinks=True)
        _link.setToolTip(link_tooltip)
        layout.addWidget(_link, row, 3, Qt.AlignmentFlag.AlignHCenter)
        return 1

    def _show_lgpl_license(self):
        """
        Zeigt die LGPL Lizenz-Datei an.
        """
        self._show_license(_LGPL_LICENSE_FILE_NAME)

    def _show_mit_license(self):
        """
        Zeigt die MIT Lizenz-Datei an.
        """
        self._show_license(_MIT_LICENSE_FILE_NAME)

    def _show_license(self, license_file_name: str):
        """
        Zeigt eine Lizenz-Datei an.
        :param license_file_name: Name der Lizenz-Datei
        """
        _license_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath('.'))))
        _license_file_path = os.path.join(_license_dir, license_file_name)
        with open(_license_file_path, 'r') as _f:
            _contents = _f.read()
            _viewer = TextFileViewerDialog(self, L_LICENSE, _contents)
            _viewer.exec()


class SaveConfigDialog(QDialog):
    """
    Auswahldialog beim Beenden, falls die lokale arestix-Konfiguration geändert wurde.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: das übergeordnete Widget
        """
        super().__init__(parent)
        self.__selected_file_name = None
        self.setWindowTitle(localized_label(L_DLG_TITLE_SAVE_LOCAL_CONFIG))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _SAVE_DIALOG_OFFSET, _parent_rect.y() + _SAVE_DIALOG_OFFSET,
                         _SAVE_DIALOG_WIDTH, _SAVE_DIALOG_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QVBoxLayout(self)
        _layout.setSpacing(DEFAULT_SPACING)
        _layout.addWidget(QLabel(localized_label(I_GUI_LOCAL_CONFIG_CHANGED)))
        _button_pane = QWidget()
        _button_pane_layout = QHBoxLayout(_button_pane)
        _dismiss_button = QPushButton(localized_label(L_DISMISS))
        _dismiss_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _dismiss_button.clicked.connect(self.reject)
        _button_pane_layout.addWidget(_dismiss_button, alignment=Qt.AlignmentFlag.AlignCenter)
        _save_as_button = QPushButton(localized_label(L_SAVE_AS))
        _save_as_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _save_as_button.clicked.connect(self._save_as_button_clicked)
        _button_pane_layout.addWidget(_save_as_button, alignment=Qt.AlignmentFlag.AlignCenter)
        _save_button = QPushButton(localized_label(L_SAVE))
        _save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _save_button.clicked.connect(self.accept)
        _button_pane_layout.addWidget(_save_button, alignment=Qt.AlignmentFlag.AlignCenter)
        _layout.addWidget(_button_pane)

    def save_as_file_path(self) -> str | None:
        """
        :returns: Ausgewählter Dateiname für "Speichern unter"; ansonsten None
        """
        return self.__selected_file_name

    def _save_as_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den "Speichern unter"-Button geklickt hat.
        """
        _file_name, _filter = QFileDialog.getSaveFileName(self, localized_label(L_DLG_TITLE_SELECT_FILE))
        if _file_name is None:
            return
        self.__selected_file_name = _file_name
        self.accept()


class PasswordDialog(QDialog):
    """
    Dialog zum Einlesen eines Passworts.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: das übergeordnete Widget
        """
        super().__init__(parent)
        self.__password = ''
        self.setWindowTitle(localized_label(L_DLG_TITLE_PASSWORD))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _PASSWORD_DIALOG_OFFSET, _parent_rect.y() + _PASSWORD_DIALOG_OFFSET,
                         _PASSWORD_DIALOG_WIDTH, _PASSWORD_DIALOG_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QGridLayout(self)
        _layout.setSpacing(DEFAULT_SPACING)
        _layout.addWidget(QLabel(localized_label(L_ENTER_PASSWORD)), 0, 0)
        self.__password_text = QLineEdit('', echoMode=QLineEdit.EchoMode.Password)
        _layout.addWidget(self.__password_text, 0, 1)
        _ok_button = QPushButton(localized_label(L_OK))
        _ok_button.clicked.connect(self._ok_button_clicked)
        _layout.addWidget(_ok_button, 1, 0)
        _cancel_button = QPushButton(localized_label(L_CANCEL))
        _cancel_button.clicked.connect(self.reject)
        _layout.addWidget(_cancel_button, 1, 1)

    def password(self) -> str:
        """
        :returns: Eingegebenes Passwort
        """
        return self.__password

    def _ok_button_clicked(self):
        """
        Wird aufgerufen, wenn der Benutzer den "OK"-Button geklickt hat.
        """
        self.__password = self.__password_text.text()
        self.accept()


def exception_box(icon, reason, question, buttons, default_button):
    """
    Creates and returns a message box in reaction to an exception.
    :param QMessageBox.Icon icon: the severity icon
    :param BaseException reason: the reason for the message box
    :param str question: the localized question to ask
    :param QMessageBox.StandardButtons buttons: the buttons to choose from
    :param QMessageBox.StandardButton default_button: the default button
    :returns: the message box
    :rtype: QMessageBox
    """
    _msg_box = QMessageBox()
    _msg_box.setIcon(icon)
    if icon == QMessageBox.Icon.Critical:
        _msg_box.setWindowTitle(localized_label(L_MBOX_TITLE_ERROR))
    elif icon == QMessageBox.Icon.Information:
        _msg_box.setWindowTitle(localized_label(L_MBOX_TITLE_WARNING))
    else:
        _msg_box.setWindowTitle(localized_label(L_MBOX_TITLE_INFO))
    _msg_box.setText(str(reason))
    _msg_box.setInformativeText(question)
    _msg_box.setStandardButtons(buttons)
    _msg_box.setDefaultButton(default_button)
    _msg_box.setStyleSheet(_STYLE_EXCEPTION_BOX_INFO)
    return _msg_box


_ABOUT_DIALOG_HEIGHT = 480
_ABOUT_DIALOG_OFFSET = 80
_ABOUT_DIALOG_WIDTH = 800
_ARESTIX_IMAGE_SIZE = 192
_ARESTIX_IMAGE_SPACING = 16
_PASSWORD_DIALOG_HEIGHT = 240
_PASSWORD_DIALOG_OFFSET = 80
_PASSWORD_DIALOG_WIDTH = 360
_PDF_VIEWER_HEIGHT = 720
_PDF_VIEWER_OFFSET = 10
_PDF_VIEWER_WIDTH = 640
_SAVE_DIALOG_HEIGHT = 240
_SAVE_DIALOG_OFFSET = 80
_SAVE_DIALOG_WIDTH = 360
_SCOPE_EDITOR_HEIGHT = 720
_SCOPE_EDITOR_OFFSET = 10
_SCOPE_EDITOR_WIDTH = 1200
_SNAPSHOT_VIEWER_HEIGHT = 720
_SNAPSHOT_VIEWER_OFFSET = 10
_SNAPSHOT_VIEWER_WIDTH = 640
_TEXT_FILE_VIEWER_HEIGHT = 720
_TEXT_FILE_VIEWER_OFFSET = 10
_TEXT_FILE_VIEWER_WIDTH = 640

_LGPL_LICENSE_FILE_NAME = 'LGPL-LICENSE'
_MIT_LICENSE_FILE_NAME = 'LICENSE'

_COMPONENT_PART_PYSIDE = 'PySide 6'
_COMPONENT_PART_TOMLI = 'tomli'
_COMPONENT_PART_TOMLI_W = 'tomli_w'

_URL_ARESTIX = 'https://github.com/frsommer64/arestix'
_URL_ICONS = 'https://github.com/KDE/oxygen-icons'
_URL_PYSIDE = 'https://wiki.qt.io/PySide6'
_URL_TOMLI = 'https://github.com/hukkin/tomli'
_URL_TOMLI_W = 'https://github.com/hukkin/tomli-w'

_STYLE_ARESTIX_IMAGE = f'border-image: url({ARESTIX_ASSETS_DIR}:arestix.jpg)'
_STYLE_INPUT_FIELD = 'background-color: #ffffcc'
_STYLE_WHITE_BG = 'background-color: white'
_STYLE_BOLD_TEXT = 'font-weight: bold'
_STYLE_EXCEPTION_BOX_INFO = 'QLabel#qt_msgbox_informativelabel {font-weight: bold}'
_STYLE_RUN_BUTTON = 'background-color: green; color: white; font-weight: bold'
