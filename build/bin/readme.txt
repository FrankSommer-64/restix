Die Build-Skripte müssen in $HOME/bin abgelegt werden, $HOME/bin muss im PATH enthalten sein.

Die Python-Skripte benötigen ein Python Virtual Environment $HOME/.python_venv/build mit den
installierten Packages hatchling und tomli.

Projekte müssen in $HOME/GITROOT/sw/projects abgelegt werden.

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
