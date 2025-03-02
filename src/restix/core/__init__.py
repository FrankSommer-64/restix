# -----------------------------------------------------------------------------------------------
# restix - wrapper around restic archiving
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

# Package version
VERSION = '0.9snapshot'
USER_MANUAL_STEM = 'user_manual_'

# Umgebungsvariablen
ENVA_RESTIX_CONFIG_PATH = 'RESTIX_CONFIG_PATH'

RESTIX_ASSETS_DIR = 'assets'
RESTIX_GUI_SETTINGS_FILE_NAME = '~/.restix'

# Parameter in der Konfigurationsdatei
CFG_GROUP_CREDENTIALS = 'credentials'
CFG_GROUP_SCOPE = 'scope'
CFG_GROUP_TARGET = 'target'
CFG_PAR_ACCESS_RIGHTS = 'access_rights'
CFG_PAR_ALIAS = 'alias'
CFG_PAR_COMMENT = 'comment'
CFG_PAR_CREDENTIALS = 'credentials'
CFG_PAR_EXCLUDES = 'excludes'
CFG_PAR_HOST = 'host'
CFG_PAR_IGNORES = 'ignores'
CFG_PAR_INCLUDES = 'includes'
CFG_PAR_LOCATION = 'location'
CFG_PAR_NAME = 'name'
CFG_PAR_SCOPE = 'scope'
CFG_PAR_TYPE = 'type'
CFG_PAR_USER = 'user'
CFG_PAR_VALUE = 'value'
CFG_PAR_YEAR = 'year'
CFG_VALUE_CREDENTIALS_TYPE_FILE = 'file'
CFG_VALUE_CREDENTIALS_TYPE_PROMPT = 'prompt'
CFG_VALUE_CREDENTIALS_TYPE_TEXT = 'text'
CFG_VALUE_CREDENTIALS_TYPE_TOKEN = 'token'

# restix CLI actions
CLI_ACTION_HELP = 'help'
CLI_ACTION_BACKUP = 'backup'
CLI_ACTION_FORGET = 'forget'
CLI_ACTION_INIT = 'init'
CLI_ACTION_RESTORE = 'restore'
CLI_ACTION_SNAPSHOTS = 'snapshots'
CLI_ACTION_TAG = 'tag'
CLI_ACTION_TARGETS = 'targets'
ALL_CLI_ACTIONS = (CLI_ACTION_BACKUP, CLI_ACTION_FORGET, CLI_ACTION_INIT, CLI_ACTION_RESTORE, CLI_ACTION_SNAPSHOTS,
                   CLI_ACTION_TAG, CLI_ACTION_TARGETS)

# restix CLI options
CLI_OPTION_BATCH = 'batch'
CLI_OPTION_DRY_RUN = 'dry-run'
CLI_OPTION_HOST= 'host'
CLI_OPTION_RESTORE_PATH = 'restore-path'
CLI_OPTION_SNAPSHOT = 'snapshot'
CLI_OPTION_TAGS = 'tags'
CLI_OPTION_TARGET_MOUNT_PATH = 'target-mount-path'
CLI_OPTION_YEAR = 'year'

# environment variable names
ENVA_HOME = 'HOME'
ENVA_USER = 'USER'
ENVA_WIN_HOME = 'HOMEPATH'
ENVA_WIN_LOCAL_APP_DATA = 'LOCALAPPDATA'
ENVA_WIN_USER = 'USERNAME'

# used restic actions
RESTIC_ACTION_BACKUP = 'backup'
RESTIC_ACTION_FORGET = 'forget'
RESTIC_ACTION_INIT = 'init'
RESTIC_ACTION_RESTORE = 'restore'
RESTIC_ACTION_SNAPSHOTS = 'snapshots'
RESTIC_ACTION_TAG = 'tag'

# restix configuration file name and location
RESTIX_CONFIG_FN = 'config.toml'
RESTIX_CONFIG_SUBDIR = ['.config', 'restix']

# supported TOML keys in restix configuration file
RESTIX_TOML_KEY_ALIAS = 'alias'
RESTIX_TOML_KEY_EXCLUDES = 'excludes'
RESTIX_TOML_KEY_GUARD_FILE = 'guard-file'
RESTIX_TOML_KEY_GUARD_TEXT = 'guard-text'
RESTIX_TOML_KEY_IGNORES = 'ignores'
RESTIX_TOML_KEY_INCLUDES = 'includes'
RESTIX_TOML_KEY_NAME = 'name'
RESTIX_TOML_KEY_PW_FILE = 'pw-file'
RESTIX_TOML_KEY_REPO = 'repo'
RESTIX_TOML_KEY_SCOPE = 'scope'
RESTIX_TOML_KEY_TARGET = 'target'

# supported variables in restix configuration file
RESTIX_VAR_CONFIG = 'CONFIG'
RESTIX_VAR_HOME = 'HOME'
RESTIX_VAR_HOSTNAME = 'HOSTNAME'
RESTIX_VAR_USER = 'USER'
RESTIX_VAR_YEAR = 'YEAR'
RESTIX_CFG_VARS = [RESTIX_VAR_CONFIG, RESTIX_VAR_HOME, RESTIX_VAR_HOSTNAME, RESTIX_VAR_USER, RESTIX_VAR_YEAR]
