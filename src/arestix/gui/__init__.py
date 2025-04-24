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


# Style für die Buttons zum Starten einer Aktion
ACTION_BUTTON_STYLE = 'background-color: green; color: white; font-weight: bold'

# Style für den Abbrechen-Button
CANCEL_BUTTON_STYLE = 'background-color: red; color: white'

# Style für die Beschreibung einer Option
CAPTION_STYLE = 'color: black; font-weight: bold'

# Style für Kontext-Menüs
CONTEXT_MENU_STYLE = 'QMenu {background-color: #ABABAB; border: 1px solid black; margin: 2px;}' \
                     'QMenu::item:selected {color: white; background: darkblue;}'

# Content margins
DEFAULT_SPACING = 10
SMALL_CONTENT_MARGIN = 5
DEFAULT_CONTENT_MARGIN = 10
WIDE_CONTENT_MARGIN = 20

# Minimale Größen
MIN_COMBO_WIDTH = 240
MIN_MAIN_WIN_HEIGHT = 640
MIN_MAIN_WIN_WIDTH = 6 * 128 + 64
MIN_MESSAGE_PANE_HEIGHT = 256

# Style für die Umrahmung aller GroupBoxes
GROUP_BOX_STYLE = 'QGroupBox {font: bold; border: 1px solid blue; border-radius: 6px; margin-top: 6px} ' \
                  'QGroupBox::title {color: blue; subcontrol-origin: margin; left: 7px; padding: 0 5px 0 5px;}'

# Icons
BUTTON_ICON_BACKUP = 'svn-commit.png'
BUTTON_ICON_CONFIGURATION = 'configure.png'
BUTTON_ICON_EXIT = 'application-exit.png'
BUTTON_ICON_INFO = 'dialog-information.png'
BUTTON_ICON_MAINTENANCE = 'system-run.png'
BUTTON_ICON_RESTORE = 'svn-update.png'

#  Buttons in der Hauptauswahl
IMAGE_BUTTON_LABEL_STYLE_ACTIVE = 'background-color: yellow; font-weight: bold'
IMAGE_BUTTON_LABEL_STYLE_NORMAL = 'background-color: white; font-weight: bold'
IMAGE_BUTTON_PANE_STYLE = 'background-color: white; border-width: 2px; border-color: black; border-style: solid'
IMAGE_BUTTON_SIZE = 128

# Style für die Pane zur Ausgabe von Nachrichten
MESSAGE_PANE_STYLE = 'background-color: white; border-color: black; border-style: solid; border-width: 1px'

# Style für die Tabs in der Konfiguration
TAB_FOLDER_STYLE = 'QTabBar {font-weight: bold}'

# Style für die Table zur Auswahl eines Backup-Ziels
TARGET_TABLE_STYLE = 'background-color: white'

# Style für Editoren
EDITOR_STYLE = 'background-color: white'

# Style für die Texteingabe-Felder
TEXT_FIELD_STYLE = 'background-color: white'

# Anzahl angezeigter Jahre in der Vergangenheit bei den Comboboxen zur Jahresauswahl
PAST_YEARS_COUNT = 10
