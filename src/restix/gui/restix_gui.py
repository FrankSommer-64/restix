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
Hauptprogramm der restix GUI.
"""

import os
import sys

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QApplication, QMessageBox

from restix.core import RESTIX_ASSETS_DIR, RESTIX_CONFIG_FN
from restix.core.messages import (localized_label, localized_message, I_GUI_CONFIG_PROBLEM, I_GUI_CONFIG_WARNING,
                                  I_GUI_CREATE_CONFIG_ROOT, L_MBOX_TITLE_INFO, L_MBOX_TITLE_ERROR)
from restix.core.config import config_root_path, create_config_root, LocalConfig
from restix.core.restix_exception import RestixException
from restix.gui.mainwindow import MainWindow


def gui_main():
    """
    Hauptprogramm der restix GUI.
    """
    try:
        # Verzeichnis mit den GUI assets (Hintergrundbilder, ...) zum QT-Suchpfad hinzufügen
        _images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), RESTIX_ASSETS_DIR)
        QDir.addSearchPath(RESTIX_ASSETS_DIR, _images_path)
        app = QApplication(sys.argv)
        try:
            # Verzeichnis mit der restix-Konfiguration ermitteln
            _config_root_path = config_root_path()
        except RestixException as _e:
            # kein Konfigurationsverzeichnis gefunden, Fehlermeldung anzeigen und anbieten, das Verzeichnis mit
            # Standardeinstellungen anzulegen
            _buttons = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            _text = localized_message(I_GUI_CREATE_CONFIG_ROOT)
            _rc = _show_mbox(QMessageBox.Icon.Information, L_MBOX_TITLE_INFO, str(_e), _text, _buttons)
            if _rc == QMessageBox.StandardButton.Cancel:
                # Abbruch durch Benutzer
                return
            # Konfigurationsverzeichnis anlegen
            _config_root_path = create_config_root()

        # lokale restix-Konfiguration einlesen
        try:
            _restix_config = LocalConfig.from_file(os.path.join(_config_root_path, RESTIX_CONFIG_FN))
            if _restix_config.has_warnings():
                # beim Lesen der restix-Konfiguration gab es Probleme, Informationen dazu in einer Message-Box anzeigen
                _show_mbox(QMessageBox.Icon.Information, L_MBOX_TITLE_INFO, I_GUI_CONFIG_WARNING,
                           os.linesep.join(_restix_config.warnings()), QMessageBox.StandardButton.Ok)
        except RestixException as _e:
            _show_mbox(QMessageBox.Icon.Critical, L_MBOX_TITLE_ERROR, I_GUI_CONFIG_PROBLEM,
                       str(_e), QMessageBox.StandardButton.Ok)
            sys.exit(1)

        # restix GUI starten
        main_win = MainWindow(_restix_config)
        main_win.show()
        app.aboutToQuit.connect(main_win.save_settings)
        sys.exit(app.exec())
    except Exception as e:
        # nicht abgefangene Exceptions werden auf der Konsole ausgegeben
        print()
        print(e)
        sys.exit(1)


def _show_mbox(icon: QMessageBox.Icon, title_id: str, text_id: str, info_text: str,
               buttons: QMessageBox.StandardButton):
    """
    Zeigt eine Message-Box an.
    :param icon: das Icon (Error, Warning, ...)
    :param title_id: ID der Fenster-Überschrift des Dialogfensters
    :param text_id: ID des Texts
    :param info_text: vollständige Beschreibung
    :param buttons: Kombination der anzuzeigenden Buttons
    """
    _mbox = QMessageBox()
    _mbox.setIcon(icon)
    _mbox.setWindowTitle(localized_label(title_id))
    _mbox.setText(localized_label(text_id))
    _mbox.setInformativeText(info_text)
    _mbox.setStandardButtons(buttons)
    return _mbox.exec()


if __name__ == "__main__":
    gui_main()
