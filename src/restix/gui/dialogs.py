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

import math

from PySide6.QtCore import qVersion, Qt, QPoint
from PySide6.QtGui import QPainter, QBrush, QColor, QColorConstants, QPen, QRadialGradient, QPixmap
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QWidget, QLabel, QDialog, QPushButton,
                               QMessageBox, QGridLayout, QVBoxLayout)

from restix.core import VERSION
from restix.core.messages import *


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

_STYLE_INPUT_FIELD = 'background-color: #ffffcc'
_STYLE_WHITE_BG = 'background-color: white'
_STYLE_BOLD_TEXT = 'font-weight: bold'
_STYLE_EXCEPTION_BOX_INFO = 'QLabel#qt_msgbox_informativelabel {font-weight: bold}'
_STYLE_RUN_BUTTON = 'background-color: green; color: white; font-weight: bold'
