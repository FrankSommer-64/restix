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

import sys

from PySide6.QtCore import QDir, QTranslator, QLocale, QLibraryInfo
from PySide6.QtWidgets import QApplication, QMessageBox, QStyleFactory

from restix.core import RESTIX_ASSETS_DIR, RESTIX_CONFIG_FN
from restix.core.messages import *
from restix.core.config import config_root_path, LocalConfig
from restix.core.restix_exception import RestixException
from restix.gui import PREFERRED_STYLES
from restix.gui.mainwindow import MainWindow
from restix.gui.wizards import run_config_wizard


def gui_main():
    """
    Hauptprogramm der restix GUI.
    """
    try:
        # Verzeichnis mit den GUI assets (Hintergrundbilder, Handbuch) zum QT-Suchpfad hinzufügen
        _images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), RESTIX_ASSETS_DIR)
        QDir.addSearchPath(RESTIX_ASSETS_DIR, _images_path)
        app = QApplication(sys.argv)
        _app_style = _preferred_style()
        if _app_style is not None:
            app.setStyle(_app_style)
        # Lokalisierung für die System-Widgets installieren
        _system_locale = QLocale.languageToCode(QLocale.system().language())
        _tr_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        _qt_translator = QTranslator(app)
        if _qt_translator.load(f'qt_{_system_locale}', directory=_tr_path):
            app.installTranslator(_qt_translator)
        # Prüfen, ob restix Konfiguration existiert
        _config_root_path, _error_info = config_root_path()
        _config_file_path = os.path.join(_config_root_path, RESTIX_CONFIG_FN)
        if _error_info is None:
            if not os.path.isfile(_config_file_path):
                # Konfigurationsdatei existiert nicht
                _error_info = localized_message(E_CFG_CONFIG_FILE_NOT_FOUND, _config_file_path)
        if _error_info is not None:
            # Konfigurationsverzeichnis existiert nicht, Assistent zum Anlegen einer initialen
            # Konfiguration anbieten
            _buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
            _rc = _show_mbox(QMessageBox.Icon.Information, L_MBOX_TITLE_INFO, _error_info,
                             localized_message(I_GUI_RUN_CONFIG_WIZARD), _buttons)
            if _rc == QMessageBox.StandardButton.Cancel:
                # kein Assistent gewünscht, Programm beenden
                sys.exit(1)
            try:
                # ggf. Konfigurationsverzeichnis anlegen und Assistent starten
                os.makedirs(_config_root_path, 0o775, True)
                run_config_wizard(_config_root_path)
            except RestixException as _e:
                _show_mbox(QMessageBox.Icon.Critical, L_MBOX_TITLE_ERROR, I_GUI_CONFIG_PROBLEM,
                           str(_e), QMessageBox.StandardButton.Ok)
                sys.exit(1)

        # lokale restix-Konfiguration einlesen
        try:
            _restix_config = LocalConfig.from_file(_config_file_path)
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
    :param icon: Icon (Error, Warning, ...)
    :param title_id: Resource-ID der Fenster-Überschrift des Dialogfensters
    :param text_id: Resource-ID des Texts
    :param info_text: lokalisierter detaillierter Text
    :param buttons: Kombination der anzuzeigenden Buttons
    """
    _mbox = QMessageBox()
    _mbox.setIcon(icon)
    _mbox.setWindowTitle(localized_label(title_id))
    _mbox.setText(localized_label(text_id))
    _mbox.setInformativeText(info_text)
    _mbox.setStandardButtons(buttons)
    return _mbox.exec()


def _preferred_style() -> str|None:
    """
    :return: bevorzugter Qt-Style für die Applikation
    """
    _available_styles = QStyleFactory.keys()
    for _style in PREFERRED_STYLES:
        if _style in _available_styles:
            return _style
    return None


if __name__ == "__main__":
    gui_main()
