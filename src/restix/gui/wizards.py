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
Assistenten für die restix GUI.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy,
                               QVBoxLayout, QWizard, QWizardPage, QGridLayout,
                               QFileDialog, QComboBox)

from restix.core import *
from restix.core.config import create_default_config, LocalConfig, create_pgp_file
from restix.core.messages import *
from restix.core.restix_exception import RestixException
from restix.core.util import relative_config_path_of
from restix.gui import *
from restix.gui.dialogs import PgpFileDialog
from restix.gui.editors import ScopeEditor


class CreateConfigWizardStartPage(QWizardPage):
    """
    Erste Seite des Assistenten für die restix-Konfiguration.
    Fragt ab, ob eine Default-Konfiguration oder eine benutzerdefinierte Konfiguration
    erzeugt werden soll.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__()
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_1))
        self.setFinalPage(True)
        _layout = QVBoxLayout(self)
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_DEFAULT), wordWrap=True))
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_1_USER), wordWrap=True))
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_CANCEL), wordWrap=True))


class CreateConfigWizardLastPage(QWizardPage):
    """
    Letzte Seite des Assistenten für die restix-Konfiguration.
    Festlegen der in die Sicherung ein- und auszuschliessenden Elemente.
    """
    def __init__(self, config_root_path: str):
        """
        Konstruktor.
        :param config_root_path: Verzeichnis, in der die restix Konfiguration angelegt werden soll.
        """
        super().__init__()
        self.includes_file_path = os.path.join(config_root_path, f'{self.field(_FIELD_SCOPE_ALIAS)}.includes')
        self.excludes_file_path = os.path.join(config_root_path, f'{self.field(_FIELD_SCOPE_ALIAS)}.excludes')
        self.__config_root_path = config_root_path
        self.setTitle(localized_label(L_WIZ_PAGE_TITLE_CREATE_CONFIG_5))
        self.setFinalPage(True)
        _layout = QVBoxLayout(self)
        _layout.addWidget(QLabel(localized_label(L_WIZ_PAGE_CREATE_CONFIG_5_SCOPE), wordWrap=True))
        _editor_button = QPushButton(localized_label(L_SCOPE))
        _editor_button.clicked.connect(self._open_scope_editor)
        _layout.addWidget(_editor_button)

    def _open_scope_editor(self):
        """
        Wird aufgerufen, wenn der Button zum Öffnen des Scope-Editors geklickt wurde.
        """
        _ignore_list = self.field(_FIELD_SCOPE_IGNORES).split(',')
        _editor = ScopeEditor(self, self.__config_root_path, self.includes_file_path,
                              self.excludes_file_path, _ignore_list)
        if _editor.exec() != QDialog.DialogCode.Accepted:
            return
        _editor_includes_file_name, _editor_excludes_file_name = _editor.scope_files()
        self.includes_file_path = relative_config_path_of(_editor_includes_file_name,
                                                          self.__config_root_path)
        self.excludes_file_path = relative_config_path_of(_editor_excludes_file_name,
                                                          self.__config_root_path)


class CreateConfigWizardInputPage(QWizardPage):
    """
    Basisklasse für alle Folgeseiten des Assistenten für die restix-Konfiguration.
    """
    def __init__(self, title_id: str, text_id: str, alias_field_name: str, comment_field_name: str):
        """
        Konstruktor.
        :param title_id: ID der Seitenüberschrift
        :param text_id: ID des Hinweistextes
        :param alias_field_name: Name des Felds für den Aliasnamen
        :param comment_field_name: Name des Felds für die Kurzbeschreibung
        """
        super().__init__()
        self.setTitle(localized_label(title_id))
        self.page_layout = QGridLayout(self)
        self.page_layout.setContentsMargins(WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN,
                                            WIDE_CONTENT_MARGIN, WIDE_CONTENT_MARGIN)
        self.page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        _desc_info = QLabel(localized_label(text_id), wordWrap=True)
        _desc_info.setStyleSheet(CAPTION_STYLE)
        self.page_layout.addWidget(_desc_info, 0, 0, 1, 2)
        _alias_label, _alias_text = _text_input(L_ALIAS, _ALIAS_CHAR_SET)
        self.page_layout.addWidget(_alias_label, 1, 0)
        self.page_layout.addWidget(_alias_text, 1, 1)
        _comment_label, _comment_text = _text_input(L_COMMENT)
        self.page_layout.addWidget(_comment_label, 2, 0)
        self.page_layout.addWidget(_comment_text, 2, 1)
        self.registerField(f'{alias_field_name}*', _alias_text)
        self.registerField(comment_field_name, _comment_text)


class CreateConfigWizardTargetPage(CreateConfigWizardInputPage):
    """
    Zweite Seite des Assistenten für die restix-Konfiguration.
    Festlegen des Sicherungsziels.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__(L_WIZ_PAGE_TITLE_CREATE_CONFIG_2, T_WIZ_TARGET_DESC_INFO,
                         _FIELD_TARGET_ALIAS, _FIELD_TARGET_COMMENT)
        _location_info = QLabel(localized_label(T_WIZ_TARGET_LOCATION_INFO), wordWrap=True)
        _location_info.setStyleSheet(CAPTION_STYLE)
        self.page_layout.addWidget(_location_info, 3, 0, 1, 2)
        self.__location_button = QPushButton(localized_label(L_LOCAL_TARGET))
        self.__location_button.clicked.connect(self._select_local_target)
        self.page_layout.addWidget(self.__location_button, 4, 0)
        self.__location_text = QLineEdit()
        self.__location_text.setStyleSheet(TEXT_FIELD_STYLE)
        self.__location_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.page_layout.addWidget(self.__location_text, 4, 1)
        self.registerField(f'{_FIELD_TARGET_LOCATION}*', self.__location_text)

    def _select_local_target(self):
        """
        Wird aufgerufen, wenn der Button zur Auswahl eines lokalen Ziels aufgerufen wird.
        """
        _dir = QFileDialog.getExistingDirectory(self, localized_label(L_SELECT))
        if len(_dir) > 0:
            self.__location_text.setText(_dir)


class CreateConfigWizardCredentialsPage(CreateConfigWizardInputPage):
    """
    Dritte Seite des Assistenten für die restix-Konfiguration.
    Festlegen der Zugangsdaten.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__(L_WIZ_PAGE_TITLE_CREATE_CONFIG_3, T_WIZ_CREDENTIALS_DESC_INFO,
                         _FIELD_CREDENTIALS_ALIAS, _FIELD_CREDENTIALS_COMMENT)
        _pw_info = QLabel(localized_label(T_WIZ_CREDENTIALS_PW_INFO), wordWrap=True)
        _pw_info.setStyleSheet(CAPTION_STYLE)
        self.page_layout.addWidget(_pw_info, 3, 0, 1, 2)
        _type_label = QLabel(localized_label(L_TYPE))
        _type_combo = QComboBox()
        _type_combo.setMinimumWidth(MIN_COMBO_WIDTH)
        _type_combo.setStyleSheet(CONFIG_COMBO_BOX_STYLE)
        for _i, _type in enumerate(CFG_CREDENTIAL_TYPES):
            _tooltip = localized_label(_CREDENTIAL_TYPE_TOOLTIPS[_type])
            _type_combo.addItem(_type)
            _type_combo.setItemData(_i, _tooltip, Qt.ItemDataRole.ToolTipRole)
        _type_combo.setCurrentIndex(-1)
        self.page_layout.addWidget(_type_label, 4, 0)
        self.page_layout.addWidget(_type_combo, 4, 1)
        _pw_label, _pw_text = _text_input(L_PASSWORD, None, QLineEdit.EchoMode.Password)
        self.page_layout.addWidget(_pw_label, 5, 0)
        self.page_layout.addWidget(_pw_text, 5, 1)
        self.registerField(f'{_FIELD_CREDENTIALS_TYPE}*', _type_combo, "currentText",
                           _type_combo.currentTextChanged)
        self.registerField(f'{_FIELD_CREDENTIALS_VALUE}', _pw_text)

    def validatePage(self, /) -> bool:
        """
        Prüfen, ob Passwort eingegeben wurde, falls es erforderlich ist.
        :return:
        """
        _type = self.field(_FIELD_CREDENTIALS_TYPE)
        _value = self.field(_FIELD_CREDENTIALS_VALUE)
        if _type != CFG_VALUE_CREDENTIALS_TYPE_NONE and \
            _type != CFG_VALUE_CREDENTIALS_TYPE_PROMPT and \
            len(self.field(_FIELD_CREDENTIALS_VALUE)) == 0:
                QMessageBox.information(self, localized_label(L_MBOX_TITLE_INFO),
                                        localized_message(I_GUI_NO_PASSWORD_SPECIFIED),
                                        QMessageBox.StandardButton.Ok)
                return False
        return super().validatePage()


class CreateConfigWizardScopePage(CreateConfigWizardInputPage):
    """
    Vierte Seite des Assistenten für die restix-Konfiguration.
    Festlegen des Sicherungsumfangs.
    """
    def __init__(self):
        """
        Konstruktor.
        """
        super().__init__(L_WIZ_PAGE_TITLE_CREATE_CONFIG_4, T_WIZ_SCOPE_DESC_INFO,
                         _FIELD_SCOPE_ALIAS, _FIELD_SCOPE_COMMENT)
        _ignores_info = QLabel(localized_label(T_WIZ_SCOPE_IGNORES_INFO), wordWrap=True)
        _ignores_info.setStyleSheet(CAPTION_STYLE)
        self.page_layout.addWidget(_ignores_info, 3, 0, 1, 2)
        _ignores_label, _ignores_text = _text_input(L_IGNORES)
        self.page_layout.addWidget(_ignores_label, 4, 0)
        self.page_layout.addWidget(_ignores_text, 4, 1)
        self.registerField(f'{_FIELD_SCOPE_IGNORES}', _ignores_text)


class CreateConfigWizard(QWizard):
    """
    Assistent zum Anlegen der initialen restix-Konfiguration.
    """
    def __init__(self, config_root_path: str):
        """
        Konstruktor.
        :param config_root_path: Verzeichnis, in der die restix Konfiguration angelegt werden soll.
        """
        super().__init__()
        self.__config_root_path = config_root_path
        self.default_config_requested = True
        self.setWindowTitle(localized_label(L_WIZ_TITLE_CREATE_CONFIG))
        self.setButtonText(QWizard.WizardButton.BackButton, localized_label(L_WIZ_BUTTON_BACK))
        self.setButtonText(QWizard.WizardButton.CancelButton, localized_label(L_WIZ_BUTTON_CANCEL))
        self.setButtonText(QWizard.WizardButton.NextButton, localized_label(L_WIZ_BUTTON_NEXT))
        self.setButtonText(QWizard.WizardButton.FinishButton, localized_label(L_WIZ_BUTTON_FINISH))
        self.addPage(CreateConfigWizardStartPage())
        self.__target_page = CreateConfigWizardTargetPage()
        self.addPage(self.__target_page)
        self.addPage(CreateConfigWizardCredentialsPage())
        self.addPage(CreateConfigWizardScopePage())
        self.__last_page = CreateConfigWizardLastPage(config_root_path)
        self.addPage(self.__last_page)
        self.currentIdChanged.connect(self.page_changed)

    def page_changed(self, page_id):
        """
        Wird aufgerufen, wenn eine andere Seite des Assistenten aufgerufen wird
        """
        self.default_config_requested = self.default_config_requested and page_id <= 0

    def user_data(self) -> dict:
        """
        :return: vom Benutzer eingegebene Werte
        """
        _credentials_type = self.field(_FIELD_CREDENTIALS_TYPE)
        _credentials_value = self.field(_FIELD_CREDENTIALS_VALUE)
        _credentials = {CFG_PAR_ALIAS: self.field(_FIELD_CREDENTIALS_ALIAS),
                        CFG_PAR_COMMENT: self.field(_FIELD_CREDENTIALS_COMMENT),
                        CFG_PAR_TYPE: _credentials_type}
        if _credentials_type == CFG_VALUE_CREDENTIALS_TYPE_FILE:
            _credentials[CFG_PAR_VALUE] = _DEFAULT_PW_FILE_NAME
            _pw_file_path = os.path.join(self.__config_root_path, _DEFAULT_PW_FILE_NAME)
            with open(_pw_file_path, 'w') as _f:
                _f.write(_credentials_value)
        elif _credentials_type == CFG_VALUE_CREDENTIALS_TYPE_PGP:
            _dlg = PgpFileDialog(self, False)
            if _dlg.exec() ==  QDialog.DialogCode.Accepted:
                _, _, _email, _ascii_flag = _dlg.data_for_file_creation()
                _file_name = f'{_DEFAULT_PGP_FILE_NAME}.asc' if _ascii_flag else f'{_DEFAULT_PGP_FILE_NAME}.gpg'
                _file_path = os.path.join(self.__config_root_path, _file_name)
                create_pgp_file(_file_path, _credentials_value, _email, _ascii_flag)
                _credentials[CFG_PAR_VALUE] = _file_name
            else:
                raise RestixException(E_CFG_CONFIG_WIZARD_ABORTED)
        _scope = {CFG_PAR_ALIAS: self.field(_FIELD_SCOPE_ALIAS),
                  CFG_PAR_COMMENT: self.field(_FIELD_SCOPE_COMMENT),
                  CFG_PAR_INCLUDES: self.__last_page.includes_file_path}
        if self.__last_page.excludes_file_path is not None:
            _credentials[CFG_PAR_EXCLUDES] = self.__last_page.excludes_file_path
        _scope_ignores = self.field(_FIELD_SCOPE_IGNORES)
        if _scope_ignores is not None:
            _credentials[CFG_PAR_IGNORES] = _scope_ignores
        _target = {CFG_PAR_ALIAS: self.field(_FIELD_TARGET_ALIAS),
                   CFG_PAR_COMMENT: self.field(_FIELD_TARGET_COMMENT),
                   CFG_PAR_LOCATION: self.field(_FIELD_TARGET_LOCATION),
                   CFG_PAR_SCOPE: self.field(_FIELD_SCOPE_ALIAS),
                   CFG_PAR_CREDENTIALS: self.field(_FIELD_CREDENTIALS_ALIAS)}
        return {CFG_GROUP_CREDENTIALS: [_credentials], CFG_GROUP_SCOPE: [_scope],
                CFG_GROUP_TARGET: [_target]}


def run_config_wizard(config_root_path: str):
    """
    Startet den Assistenten zum Anlegen einer restix-Konfiguration.
    :param config_root_path: Verzeichnis, in der die restix Konfiguration angelegt werden soll.
    :raises RestixException: falls der Assistent abgebrochen wird oder die Konfiguration nicht
    erzeugt werden kann
    """
    _wizard = CreateConfigWizard(config_root_path)
    if _wizard.exec() == QDialog.DialogCode.Accepted:
        if _wizard.default_config_requested:
            # Standard-Konfiguration erzeugen
            create_default_config(config_root_path)
        else:
            # benutzerdefinierte Konfiguration erzeugen
            _config_file_path = os.path.join(config_root_path, RESTIX_CONFIG_FN)
            _cfg = LocalConfig.from_toml(_wizard.user_data(), _config_file_path)
            _cfg.to_file(_config_file_path)
        QMessageBox.information(None, localized_label(L_MBOX_TITLE_INFO),
                                localized_message(I_GUI_COMPLETE_CONFIG_LATER),
                                QMessageBox.StandardButton.Ok)
    else:
        # Assistent abgebrochen
        raise RestixException(E_CFG_CONFIG_WIZARD_ABORTED)


def _text_input(label_id, allowed_chars=None, echo_mode=QLineEdit.EchoMode.Normal) -> tuple[QLabel, QLineEdit]:
    """
    Erzeugt ein Label und ein Texteingabefeld.
    :param label_id: Resource-ID des Label-Texts
    :param allowed_chars: optional erlaubte Zeichen im Textfeld
    :param echo_mode: optional Echo-Mode bei der Texteingabe
    :return: Label und Texteingabefeld
    """
    _label = QLabel(localized_label(label_id))
    _text = QLineEdit(echoMode=echo_mode)
    _text.setStyleSheet(TEXT_FIELD_STYLE)
    _text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    if allowed_chars is not None:
        _text.setValidator(QRegularExpressionValidator(allowed_chars))
    return _label, _text


_ALIAS_CHAR_SET = r'[\p{L}0-9._-]+'
_DEFAULT_PGP_FILE_NAME = 'pw.pgp'
_DEFAULT_PW_FILE_NAME = 'pw.txt'
_FIELD_CREDENTIALS_ALIAS = 'credentials.alias'
_FIELD_CREDENTIALS_COMMENT = 'credentials.comment'
_FIELD_CREDENTIALS_TYPE = 'credentials.type'
_FIELD_CREDENTIALS_VALUE = 'credentials.value'
_FIELD_SCOPE_ALIAS = 'scope.alias'
_FIELD_SCOPE_COMMENT = 'scope.comment'
_FIELD_SCOPE_IGNORES = 'scope.ignores'
_FIELD_TARGET_ALIAS = 'target.alias'
_FIELD_TARGET_COMMENT = 'target.comment'
_FIELD_TARGET_LOCATION = 'target.location'

_CREDENTIAL_TYPE_TOOLTIPS = {
    CFG_VALUE_CREDENTIALS_TYPE_FILE: T_CFG_CREDENTIAL_VALUE_FILE,
    CFG_VALUE_CREDENTIALS_TYPE_NONE: T_CFG_CREDENTIAL_VALUE_NONE,
    CFG_VALUE_CREDENTIALS_TYPE_PGP: T_CFG_CREDENTIAL_VALUE_PGP,
    CFG_VALUE_CREDENTIALS_TYPE_PROMPT: T_CFG_CREDENTIAL_VALUE_PROMPT,
    CFG_VALUE_CREDENTIALS_TYPE_TEXT: T_CFG_CREDENTIAL_VALUE_TEXT
}