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
Hauptfenster der restix GUI.
"""

import os.path

from PySide6.QtCore import QSize, Qt, Signal, QObject, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout,
                               QPushButton, QLabel, QHBoxLayout, QSizePolicy, QMenu)

from restix.core import *
from restix.core.config import LocalConfig
from restix.core.restix_exception import RestixException
from restix.core.messages import *
from restix.gui.dialogs import (AboutDialog, PdfViewerDialog)
from restix.gui.settings import GuiSettings


class ImageButtonSignals(QObject):
    """
    Interne Signale für Klicks auf Image-Buttons.
    """
    # Links-Klick
    clicked = Signal()
    # Links- oder Rechts-Klick an Bildschirm-Position X, Y
    menu_triggered = Signal(int, int)


class ImageButton(QPushButton):
    """
    Button mit Hintergrundbild.
    Eigene Klasse, da Kontextmenü sowohl mit Klick auf rechte als auch linke Maustaste erscheinen soll.
    """
    def __init__(self, parent: QWidget, image_url: str, click_handler, triggers_menu=False):
        """
        Konstruktor.
        :param parent: die Pane für den Button
        :param image_url: URL des Hintergrundbilds
        :param click_handler: Slot für Klicks auf den Button
        :param triggers_menu: zeigt an, ob beim Klick auf den Button ein Kontextmenü angezeigt werden soll
        """
        super().__init__('', parent)
        self.__click_handler = click_handler
        self.__triggers_menu = triggers_menu
        self.__signals = ImageButtonSignals()
        if triggers_menu:
            self.__signals.menu_triggered.connect(click_handler)
        else:
            self.__signals.clicked.connect(click_handler)
        self.setStyleSheet(f'background-image : url({RESTIX_ASSETS_DIR}:{image_url}); border-width: 2px; border-color: black; border-style: solid')
        self.setMinimumSize(QSize(128, 128))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Event-Handler für Mausklicks.
        Löst das registrierte Signal aus.
        :param event: das Maus-Event
        """
        if self.__triggers_menu:
            # bei Kontextmenü wird Links- oder Rechts-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
                self.__signals.menu_triggered.emit(event.globalX(), event.globalY())
        else:
            # bei normalem Button wird nur Links-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton:
                self.__signals.clicked.emit()


class ImageButtonPane(QWidget):
    """
    Pane mit Hintergrundbild-Button im oberen und Label im unteren Bereich.
    """
    def __init__(self, parent: QWidget, image_url: str, label_id: str, click_handler, triggers_menu=False):
        """
        Konstruktor.
        :param parent: das Widget, das diese Pane enthält.
        :param image_url: URL des Hintergrundbilds
        :param label_id: Resource-ID der Beschriftung
        :param click_handler: Slot für Klicks auf die Pane
        :param triggers_menu: zeigt an, ob beim Klick auf die Pane ein Kontextmenü angezeigt werden soll
        """
        super().__init__(parent)
        self.__click_handler = click_handler
        self.__triggers_menu = triggers_menu
        self.__signals = ImageButtonSignals()
        if triggers_menu:
            self.__signals.menu_triggered.connect(click_handler)
        else:
            self.__signals.clicked.connect(click_handler)
        _layout = QVBoxLayout()
        _layout.setSpacing(0)
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__image_button = ImageButton(self, image_url, click_handler, triggers_menu)
        _layout.addWidget(self.__image_button)
        _label = QLabel(localized_label(label_id), self)
        _label.setStyleSheet('font-weight: bold')
        _label.setMinimumWidth(128)
        _label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        _label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        _layout.addWidget(_label)
        self.setLayout(_layout)
        self.setStyleSheet('background-color: white; border-width: 2px; border-color: black; border-style: solid')


    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Event-Handler für Mausklicks.
        Löst das registrierte Signal aus.
        :param event: das Maus-Event
        """
        if self.__triggers_menu:
            # bei Kontextmenü wird Links- oder Rechts-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
                self.__signals.menu_triggered.emit(event.globalX(), event.globalY())
        else:
            # bei normalem Button wird nur Links-Klick akzeptiert
            if event.button() == Qt.MouseButton.LeftButton:
                self.__signals.clicked.emit()


class ActionSelectionPane(QWidget):
    """
    Pane mit den Hintergrundbild-Buttons zur Auswahl der Aktionen.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: das Widget, das diese Pane enthält
        """
        super().__init__(parent)
        _layout = QHBoxLayout()
        _layout.setSpacing(0)
        _layout.setContentsMargins(0, 0, 0, 0)
        # Backup
        _backup_button_pane = ImageButtonPane(self, 'backup_icon.png', L_BACKUP, self._backup_action)
        _layout.addWidget(_backup_button_pane)
        # Restore
        _restore_button_pane = ImageButtonPane(self, 'restore_icon.png', L_RESTORE, self._restore_action)
        _layout.addWidget(_restore_button_pane)
        # Konfiguration
        _config_button_pane = ImageButtonPane(self, 'configuration_icon.png', L_CONFIGURATION, self._config_action)
        _layout.addWidget(_config_button_pane)
        # Wartung
        _restore_button_pane = ImageButtonPane(self, 'maintenance_icon.png', L_MAINTENANCE, self._maintenance_action)
        _layout.addWidget(_restore_button_pane)
        # Hilfe
        _help_button_pane = ImageButtonPane(self, 'help_icon.png', L_HELP, self._help_action, True)
        _layout.addWidget(_help_button_pane)
        # Beenden
        _exit_button = ImageButtonPane(self, 'exit_icon.png', L_EXIT, QApplication.instance().quit)
        _layout.addWidget(_exit_button)
        self.setLayout(_layout)
        self.setStyleSheet('background-color: white')

    def _help_action(self, mouse_x: int, mouse_y: int):
        """
        Zeigt das Hilfe-Menü an.
        :param mouse_x: X-Position des Mausklicks
        :param mouse_y: Y-Position des Mausklicks
        """
        _context_menu = QMenu(self)
        _context_menu.addAction(localized_label(L_MENU_USER_MANUAL)).triggered.connect(self._show_manual)
        _context_menu.addAction(localized_label(L_MENU_ABOUT)).triggered.connect(self._show_about)
        _context_menu.exec(QPoint(mouse_x, mouse_y))

    def _show_manual(self):
        """
        Zeigt das restix-Benutzerhandbuch an.
        """
        _locale = platform_locale()
        _cur_dir = str(os.path.dirname(__file__))
        _assets_path = os.path.join(_cur_dir, RESTIX_ASSETS_DIR)
        _manual_file_path = os.path.join(_assets_path, f'{USER_MANUAL_STEM}{_locale}.pdf')
        if not os.path.isfile(_manual_file_path):
            _manual_file_path = os.path.join(_assets_path, f'{USER_MANUAL_STEM}en.pdf')
        _dlg = PdfViewerDialog(self, L_DLG_TITLE_USER_MANUAL, _manual_file_path)
        _dlg.exec()

    def _show_about(self):
        """
        Zeigt ein Dialogfenster mit Informationen über die restix-Applikation an.
        """
        _about_dlg = AboutDialog(self)
        _about_dlg.exec()

    def _backup_action(self):
        print('_backup_action')

    def _restore_action(self):
        print('_restore_action')

    def _config_action(self):
        print('_config_action')

    def _maintenance_action(self):
        print('_maintenance_action')


class CentralPane(QWidget):
    """
    Arbeitsbereich der restix GUI.
    """
    def __init__(self, parent: QWidget):
        """
        Konstruktor.
        :param parent: das Hauptfenster
        """
        super().__init__(parent)
        _layout = QVBoxLayout()
        _layout.setSpacing(20)
        _layout.setContentsMargins(5, 5, 5, 5)
        _layout.addWidget(ActionSelectionPane(self))
        self.setLayout(_layout)


class MainWindow(QMainWindow):
    """
    Hauptfenster der restix GUI.
    """
    def __init__(self, config_path: str, local_config: LocalConfig):
        """
        Konstruktor.
        :param config_path: restix-Konfigurationsverzeichnis
        :param local_config: lokale restix-Konfiguration
        """
        super().__init__()
        self.__config_path = config_path
        self.__local_config = local_config
        self.__settings = GuiSettings.from_file()
        self.setGeometry(self.__settings.win_geometry())
        self.setWindowTitle(localized_label(L_MAIN_WIN_TITLE))
        # main menu
        #_exit_action = QAction(localized_label(L_ACTION_ITEM_EXIT), self)
        #_exit_action.triggered.connect(QApplication.quit)
        # central widget
        _welcome_pane = QWidget()
        _welcome_pane.setStyleSheet(_MAIN_WINDOW_STYLE)
        self.setCentralWidget(CentralPane(self))
        self.layout().setContentsMargins(_MAIN_WINDOW_MARGIN, _MAIN_WINDOW_MARGIN,
                                         _MAIN_WINDOW_MARGIN, _MAIN_WINDOW_MARGIN)
        self.layout().update()

    def save_settings(self):
        """
        Speichert die GUI-Einstellungen in einer Datei.
        """
        self.__settings.set_win_geometry(self.rect())
        try:
            self.__settings.save()
        except RestixException as _e:
            QMessageBox.warning(self, localized_label(L_MBOX_TITLE_WARNING), str(_e), QMessageBox.StandardButton.Ok)

    def _action_selection_pane(self) -> QWidget:
        """
        :returns: Pane mit den Buttons zur Auswahl der Aktionen
        """
        _pane = QWidget(self)
        return _pane


_MAIN_WINDOW_MARGIN = 16
_MAIN_WINDOW_STYLE = f'border-image: url({RESTIX_ASSETS_DIR}:restix-aq.jpg)'
