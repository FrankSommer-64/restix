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
Dialogfenster für die restix GUI.
"""
import datetime
import math

from PySide6 import QtCore
from PySide6.QtCore import qVersion, Qt, QPoint
from PySide6.QtGui import QPainter, QBrush, QColor, QColorConstants, QPen, QRadialGradient, QPixmap
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QWidget, QLabel, QDialog, QPushButton,
                               QMessageBox, QGridLayout, QVBoxLayout, QGroupBox, QHBoxLayout, QSizePolicy, QLineEdit,
                               QTreeWidget, QTreeWidgetItem, QStyle, QFileDialog)

from restix.core import *
from restix.core.action import RestixAction
from restix.core.config import LocalConfig
from restix.core.messages import *
from restix.core.restic_interface import find_snapshot_elements, list_snapshot_elements
from restix.core.snapshot import Snapshot


class SnapshotViewerDialog(QDialog):
    """
    Zeigt den Inhalt eines Snapshots an.
    Bietet die Möglichkeit, nach gesicherten Elementen zu suchen.
    Ermöglicht die Auswahl einzelner Elemente für die Wiederherstellung.
    """
    def __init__(self, parent: QWidget, snapshot_id: str, target_alias: str,
                 local_config: LocalConfig, hostname: str, year: str):
        """
        Konstruktor.
        :param parent: übergeordnetes Widget
        :param snapshot_id: ID des restic Snapshots.
        :param target_alias: Alias des Backup-Ziels.
        :param local_config: lokale restix-Konfiguration.
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
        self.setWindowTitle(localized_message(L_DLG_TITLE_SNAPSHOT_VIEWER, snapshot_id, hostname, year))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _SNAPSHOT_VIEWER_OFFSET, _parent_rect.y() + _SNAPSHOT_VIEWER_OFFSET,
                         _SNAPSHOT_VIEWER_WIDTH, _SNAPSHOT_VIEWER_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _layout = QVBoxLayout()
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _viewer_pane = self._create_viewer_pane()
        _viewer_pane.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        _layout.addWidget(_viewer_pane)
        _action_pane = self._create_action_pane()
        _layout.addWidget(_action_pane)
        self.setLayout(_layout)

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
        _group_layout = QVBoxLayout()
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
        #_search_field.setToolTip(_tooltip)
        _viewer_buttons_layout.addWidget(self.__search_field)
        _group_layout.addLayout(_viewer_buttons_layout)
        self.__tree_viewer = QTreeWidget(self)
        self.__tree_viewer.setColumnCount(1)
        self.__tree_viewer.setHeaderLabels([localized_label(L_ELEMENT)])
        self.__tree_viewer.itemChanged.connect(SnapshotViewerDialog._item_changed)
        _group_layout.addWidget(self.__tree_viewer)
        _group.setLayout(_group_layout)
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
        _action = RestixAction.for_action_id(ACTION_LS, self.__target_alias, self.__local_config, _options)
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
        _action = RestixAction.for_action_id(ACTION_FIND, self.__target_alias, self.__local_config, _options)
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
        :param parent: das übergeordnete Widget
        :param title_id: Resource-ID für die Fensterüberschrift
        :param file_path: Name und Pfad der anzuzeigenden PDF-Datei
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(title_id))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _PDF_VIEWER_OFFSET, _parent_rect.y() + _PDF_VIEWER_OFFSET,
                         _PDF_VIEWER_WIDTH, _PDF_VIEWER_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _dlg_layout = QVBoxLayout()
        _web_view = QWebEngineView()
        _view_settings = _web_view.settings()
        _view_settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        _view_settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        _web_view.load(f'file://{file_path}')
        _dlg_layout.addWidget(_web_view)
        self.setLayout(_dlg_layout)


class AboutDialog(QDialog):
    """
    Zeigt Informationen über restix an.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: das übergeordnete Widget
        """
        super().__init__(parent)
        self.setWindowTitle(localized_label(L_DLG_TITLE_ABOUT))
        _parent_rect = parent.contentsRect()
        self.setGeometry(_parent_rect.x() + _ABOUT_DIALOG_OFFSET, _parent_rect.y() + _RESTIX_IMAGE_SIZE,
                         _ABOUT_DIALOG_WIDTH, _ABOUT_DIALOG_HEIGHT)
        self.setStyleSheet(_STYLE_WHITE_BG)
        _dlg_layout = QGridLayout()
        _dlg_layout.setSpacing(10)
        self.__issai_image = QLabel()
        _pixmap = QPixmap(_RESTIX_IMAGE_SIZE, _RESTIX_IMAGE_SIZE)
        _pixmap.fill(QColorConstants.White)
        self.__issai_image.setPixmap(_pixmap)
        _dlg_layout.addWidget(self.__issai_image, 0, 0, 4, 1)
        _dlg_layout.addWidget(QLabel(localized_message(I_GUI_ABOUT_TEXT)), 0, 1,
                              Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        _dlg_layout.addWidget(QLabel(localized_message(I_GUI_ABOUT_DETAIL_TEXT, VERSION, qVersion())),
                              1, 1, Qt.AlignmentFlag.AlignCenter)
        _dlg_layout.addWidget(QLabel(localized_message(I_GUI_ABOUT_INFO_TEXT)), 2, 1,
                              Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        _ok_button = QPushButton(localized_label(L_OK))
        _ok_button.clicked.connect(self.close)
        _dlg_layout.addWidget(_ok_button, 3, 1, 1, 1, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(_dlg_layout)
        self._draw_image()

    def _draw_image(self):
        """
        Draws an issai fruit image.
        """
        _pixmap = self.__issai_image.pixmap()
        painter = QPainter(_pixmap)
        _bright_yellow = QColor(0xff, 0xee, 0xcc)
        _rect = _pixmap.rect()
        # draw background regions
        _center = QPoint(_rect.x() + (_rect.width() >> 1), _rect.y() + (_rect.height() >> 1))
        _radius = (min(_rect.width(), _rect.height()) >> 1) - _RESTIX_IMAGE_SPACING
        _gradient = QRadialGradient(_center, _radius)
        _gradient.setColorAt(0.1, _bright_yellow)
        _gradient.setColorAt(0.5, QColorConstants.Yellow)
        _gradient.setColorAt(1.0, QColorConstants.DarkGreen)
        painter.setPen(QPen(QColorConstants.DarkGray, 2, Qt.PenStyle.SolidLine))
        painter.setBrush(QBrush(_gradient))
        painter.drawEllipse(_center, _radius, _radius)
        # draw beams
        _inner_radius = _radius * 0.3
        _outer_radius = _radius * 0.9
        _step = math.pi / 10.0
        _inner_beam_width = math.pi / 50
        _outer_beam_width = _inner_beam_width / 3
        _angle = 0.0
        painter.setPen(QPen(QColorConstants.Yellow, 1, Qt.PenStyle.SolidLine))
        while _angle < 2 * math.pi:
            _inner_x = int(_center.x() + _inner_radius * math.cos(_angle))
            _inner_y = int(_center.y() + _inner_radius * math.sin(_angle))
            _inner_x1 = int(_center.x() + _inner_radius * math.cos(_angle-_inner_beam_width))
            _inner_y1 = int(_center.y() + _inner_radius * math.sin(_angle-_inner_beam_width))
            _inner_x2 = int(_center.x() + _inner_radius * math.cos(_angle+_inner_beam_width))
            _inner_y2 = int(_center.y() + _inner_radius * math.sin(_angle+_inner_beam_width))
            _outer_x1 = int(_center.x() + _outer_radius * math.cos(_angle-_outer_beam_width))
            _outer_y1 = int(_center.y() + _outer_radius * math.sin(_angle-_outer_beam_width))
            _outer_x2 = int(_center.x() + _outer_radius * math.cos(_angle+_outer_beam_width))
            _outer_y2 = int(_center.y() + _outer_radius * math.sin(_angle+_outer_beam_width))
            _beam_gradient = QRadialGradient(QPoint(_inner_x, _inner_y), _outer_radius - _inner_radius)
            _beam_gradient.setColorAt(0.3, QColorConstants.Yellow)
            _beam_gradient.setColorAt(1.0, _bright_yellow)
            painter.setBrush(QBrush(_beam_gradient))
            painter.drawPolygon([QPoint(_inner_x1, _inner_y1), QPoint(_outer_x1, _outer_y1),
                                 QPoint(_outer_x2, _outer_y2), QPoint(_inner_x2, _inner_y2)])
            _angle += _step
        # draw pits
        _pit_radius = _radius * 0.45
        _pit_width = int(_radius * 0.08)
        _pit_height = int(_pit_width / 4)
        _angle = math.pi / 20.0
        _pit_color = QColor(0x44, 0x22, 0x55)
        painter.setPen(QPen(_pit_color, 1, Qt.PenStyle.SolidLine))
        painter.setBrush(QBrush(_pit_color))
        while _angle < 2 * math.pi:
            _pit_x = int(_center.x() + _pit_radius * math.cos(_angle))
            _pit_y = int(_center.y() + _pit_radius * math.sin(_angle))
            painter.save()
            painter.translate(QPoint(_pit_x, _pit_y))
            painter.rotate(_angle * 180 / math.pi)
            painter.drawEllipse(QPoint(0, 0), _pit_width, _pit_height)
            painter.restore()
            _angle += _step
        painter.end()
        self.__issai_image.setPixmap(_pixmap)


class SaveConfigDialog(QDialog):
    """
    Auswahldialog beim Beenden, falls die lokale restix-Konfiguration geändert wurde.
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
        _layout.setSpacing(10)
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


_ABOUT_DIALOG_HEIGHT = 320
_ABOUT_DIALOG_OFFSET = 80
_ABOUT_DIALOG_WIDTH = 560
_RESTIX_IMAGE_SIZE = 256
_RESTIX_IMAGE_SPACING = 16
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

_STYLE_INPUT_FIELD = 'background-color: #ffffcc'
_STYLE_WHITE_BG = 'background-color: white'
_STYLE_BOLD_TEXT = 'font-weight: bold'
_STYLE_EXCEPTION_BOX_INFO = 'QLabel#qt_msgbox_informativelabel {font-weight: bold}'
_STYLE_RUN_BUTTON = 'background-color: green; color: white; font-weight: bold'
