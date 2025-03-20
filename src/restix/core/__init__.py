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

# restix Version
VERSION = '0.1snapshot'

# Anfang des Dateinamens für die lokalisierten Benutzerhandbücher
USER_MANUAL_STEM = 'user_manual_'

# Umgebungsvariablen
ENVA_HOME = 'HOME'
ENVA_RESTIX_CONFIG_PATH = 'RESTIX_CONFIG_PATH'
ENVA_USER = 'USER'
ENVA_WIN_HOME = 'HOMEPATH'
ENVA_WIN_LOCAL_APP_DATA = 'LOCALAPPDATA'
ENVA_WIN_USER = 'USERNAME'

# Unterverzeichnis für Bilder und die Benutzerhandbücher
RESTIX_ASSETS_DIR = 'assets'

# Dateiname für die persönlichen Einstellungen der GUI
RESTIX_GUI_SETTINGS_FILE_PATH = '~/.restix'

# Name der restix-Konfigurationsdatei
RESTIX_CONFIG_FN = 'config.toml'

# Default-Unterverzeichnis für die restix-Konfiguration
RESTIX_CONFIG_SUBDIR = ['.config', 'restix']

# Parameter in der Konfigurationsdatei
CFG_GROUP_CREDENTIALS = 'credentials'
CFG_GROUP_SCOPE = 'scope'
CFG_GROUP_TARGET = 'target'
CFG_PAR_ALIAS = 'alias'
CFG_PAR_COMMENT = 'comment'
CFG_PAR_CREDENTIALS = 'credentials'
CFG_PAR_EXCLUDES = 'excludes'
CFG_PAR_IGNORES = 'ignores'
CFG_PAR_INCLUDES = 'includes'
CFG_PAR_LOCATION = 'location'
CFG_PAR_NAME = 'name'
CFG_PAR_SCOPE = 'scope'
CFG_PAR_TYPE = 'type'
CFG_PAR_VALUE = 'value'
CFG_VALUE_CREDENTIALS_TYPE_FILE = 'file'
CFG_VALUE_CREDENTIALS_TYPE_PROMPT = 'prompt'
CFG_VALUE_CREDENTIALS_TYPE_TEXT = 'text'
CFG_VALUE_CREDENTIALS_TYPE_TOKEN = 'token'

# unterstützte Variablen in der restix-Konfigurationsdatei
CFG_VAR_HOST = 'HOST'
CFG_VAR_USER = 'USER'
CFG_VAR_YEAR = 'YEAR'
CFG_VARS = {CFG_VAR_HOST, CFG_VAR_USER, CFG_VAR_YEAR}

# Befehle der restix Kommando-Zeile
CLI_COMMAND_BACKUP = 'backup'
CLI_COMMAND_FORGET = 'forget'
CLI_COMMAND_HELP = 'help'
CLI_COMMAND_INIT = 'init'
CLI_COMMAND_RESTORE = 'restore'
CLI_COMMAND_SNAPSHOTS = 'snapshots'
CLI_COMMAND_TAG = 'tag'
CLI_COMMAND_TARGETS = 'targets'
ALL_CLI_COMMANDS = (CLI_COMMAND_BACKUP, CLI_COMMAND_FORGET, CLI_COMMAND_HELP, CLI_COMMAND_INIT, CLI_COMMAND_RESTORE,
                    CLI_COMMAND_SNAPSHOTS, CLI_COMMAND_TAG, CLI_COMMAND_TARGETS)

# restic Befehle
RESTIC_COMMAND_BACKUP = 'backup'
RESTIC_COMMAND_FIND = 'find'
RESTIC_COMMAND_FORGET = 'forget'
RESTIC_COMMAND_INIT = 'init'
RESTIC_COMMAND_LS = 'ls'
RESTIC_COMMAND_RESTORE = 'restore'
RESTIC_COMMAND_SNAPSHOTS = 'snapshots'
RESTIC_COMMAND_TAG = 'tag'

# interne Aktionen
ACTION_BACKUP = 'backup'
ACTION_FORGET = 'forget'
ACTION_FIND = 'find'
ACTION_HELP = 'help'
ACTION_INIT = 'init'
ACTION_LS = 'ls'
ACTION_RESTORE = 'restore'
ACTION_SNAPSHOTS = 'snapshots'
ACTION_TAG = 'tag'

# interne Attribute
ATTR_CHILDREN = 'children'
ATTR_NAME = 'name'
ATTR_TYPE = 'type'
ELEMENT_TYPE_DIR = 'dir'
ELEMENT_TYPE_FILE = 'file'
JSON_ATTR_PATH = 'path'
JSON_ATTR_SHORT_ID = 'short_id'
JSON_ATTR_STRUCT_TYPE = 'struct_type'
JSON_ATTR_TAGS = 'tags'
JSON_ATTR_TIME = 'time'
JSON_ATTR_TYPE = 'type'
JSON_STRUCT_TYPE_NODE = 'node'
JSON_STRUCT_TYPE_SNAPSHOT = 'snapshot'

# Optionen
OPTION_AUTO_CREATE = '--auto-create'
OPTION_AUTO_TAG = '--auto-tag'
OPTION_BATCH = '--batch'
OPTION_COMPACT = '--compact'
OPTION_DRY_RUN = '--dry-run'
OPTION_EXCLUDE_FILE = '--exclude-file'
OPTION_FILES_FROM = '--files-from'
OPTION_FIND_PATTERN = '--FIND-PATTERN'
OPTION_HELP= '--help'
OPTION_HOST= '--host'
OPTION_INCLUDE_FILE = '--include-file'
OPTION_JSON = '--json'
OPTION_KEEP_LAST = '--keep-last'
OPTION_PASSWORD_FILE = '--password-file'
OPTION_PRUNE = '--prune'
OPTION_REPO = '--repo'
OPTION_RESTORE_PATH = '--restore-path'
OPTION_SET = '--set'
OPTION_SNAPSHOT = '--snapshot'
OPTION_TAG = '--tag'
OPTION_TARGET = '--target'
OPTION_UNTAGGED = '--untagged'
OPTION_USER = '--user'
OPTION_YEAR = '--year'

# restic Sondervariablen
RESTIC_SNAPSHOT_LATEST = 'latest'
RESTIC_RC_OK = 0
RESTIC_RC_CMD_FAILED = 1
RESTIC_RC_GO_RUNTIME_ERROR = 2
RESTIC_RC_READ_BACKUP_DATA_FAILED = 3
RESTIC_RC_REPO_DOES_NOT_EXIST = 10
RESTIC_RC_REPO_LOCK_FAILED = 11
RESTIC_RC_REPO_WRONG_PASSWORD = 12
RESTIC_RC_CMD_INTERRUPTED = 130

# Asynchrone Verarbeitung
SEVERITY_ERROR = 'e'
SEVERITY_INFO = 'i'
SEVERITY_WARNING = 'w'
TASK_SUCCEEDED = 0
TASK_FAILED = 1
