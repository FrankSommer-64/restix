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
Hilfsklasse zur Erkennung des Funktionsumfangs spezifischer Restic-Versionen.
"""

from packaging.version import Version

import re

from restix.core.messages import *
from restix.core.restix_exception import RestixException


class ResticVersion:
    """
    Restic-Version mit Informationen über die unterstützte Funktionalität.
    """
    def __init__(self, version: str):
        """
        Konstruktor
        :param version: die ermittelte restic-Version
        """
        self.__version = Version(version)

    def version(self) -> str:
        """
        :returns: restic-Version
        """
        return str(self.__version)

    def auto_create_supported(self) -> bool:
        """
        :returns: True, falls die restic-Version einen eigenen Fehlercode für nicht existierendes Repository liefert
        """
        return self.__version >= Version('0.17')

    def backup_dry_run_supported(self) -> bool:
        """
        :returns: True, falls die restic-Version die Option --dry-run für backup-Befehle unterstützt
        """
        return self.__version >= Version('0.13')

    def empty_password_supported(self) -> bool:
        """
        :returns: True, falls die restic-Version die Option --insecure-no-password unterstützt
        """
        return self.__version >= Version('0.17')

    def forget_dry_run_supported(self) -> bool:
        """
        :returns: True, falls die restic-Version die Option --dry-run für forget-Befehle unterstützt
        """
        return self.__version >= Version('0.12.1')

    def restore_dry_run_supported(self) -> bool:
        """
        :returns: True, falls die restic-Version die Option --dry-run für restore-Befehle unterstützt
        """
        return self.__version >= Version('0.17')

    def restore_include_file_supported(self) -> bool:
        """
        :returns: True, falls die restic-Version die Option --include-file für restore-Befehle unterstützt
        """
        return self.__version >= Version('0.17')

    def suitable_for_restix(self) -> bool:
        """
        :returns: True, falls die restic-Version für restix benutzt werden kann
        """
        return self.__version >= Version('0.10')

    @classmethod
    def from_version_command(cls, output: str) -> Self:
        """
        :param output: Ausgabe des restic-Befehls 'restic version'
        :returns: restic-Version mit Informationen über die unterstützte Funktionalität.
        :raises RestixException: falls die Version nicht erkannt wird
        """
        _match = re.match(r'^restic\s+([\d.]+)\s.*$', output)
        if _match is None:
            raise RestixException(E_RESTIC_VERSION_NOT_RECOGNIZED, output.strip())
        return ResticVersion(_match.group(1))
