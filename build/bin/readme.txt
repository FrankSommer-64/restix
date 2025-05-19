Die Build-Skripte sollten in $HOME/bin abgelegt werden, $HOME/bin muss im PATH enthalten sein.
Alternativ kann Umgebungsvariable BUILD_SCRIPTS_PATH auf das Verzeichnis mit den Build-Skripten gesetzt werden.

Die Python-Skripte benötigen ein Python Virtual Environment mit den installierten Packages hatchling und tomli.
Es sollte in $HOME/.python_venv/build liegen, alternativ kann Umgebungsvariable BUILD_PY_VENV_PATH auf das Verzeichnis
mit dem Python Virtual Environment gesetzt werden.

Projekte sollten in $HOME/GITROOT/sw/projects abgelegt werden.
Alternativ kann Umgebungsvariable SW_PROJECTS_ROOT auf das Root-Verzeichnis für Projekte gesetzt werden.

Bei Projekten mit nur einer Ausprägung muss die Verzeichnisstruktur für den Build wie folgt aussehen:
<Projekt-Root>
|- build
   |- deb
   |  |- control
   |  |- data
   |  |- debian.binary
   |- pyproject.toml
   |- rpm
   |  |- SOURCES
   |  |- SPECS
   |- win

Bei Projekten mit mehreren Feature-Umfängen muss die Verzeichnisstruktur für den Build wie folgt aussehen:
<Projekt-Root>
|- build
   |- featuresets
   |  |- <Feature-Set>
   |     |- deb
   |     |  |- control
   |     |  |- data
   |     |  |- debian.binary
   |     |- rpm
   |     |  |- SOURCES
   |     |  |- SPECS
   |     |- wheel
   |     |  |- pyproject.toml
   |     |- win
