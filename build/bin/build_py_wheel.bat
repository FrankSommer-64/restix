@echo off

rem Erstellt Python wheel für ein Projekt.
rem Root-Verzeichnis für Projekte muss $HOME/GITROOT/sw/projects sein oder über Umgebungsvariable SW_PROJECTS_ROOT
rem definiert werden.
rem Verzeichnis mit dem virtuellen Python-Environment für Builds muss $HOME/.python_venv/build sein oder über
rem Umgebungsvariable BUILD_PY_VENV_PATH definiert werden.
rem Falls das Projekt wegen unterschiedlicher Features mehrere Installationspakete benötigt,
rem muss das Script für jeden Feature-Umfang aufgerufen werden.

set "CONFIG_FILE_NAME=pyproject.toml"

rem Argumente einlesen
if -%1-==-- (
  echo Kein Projekt angegeben
  echo Aufruf: build_py_wheel ^<Projekt^> [^<Feature-Umfang^>]
  exit /b
)
set PROJECT=%1
set FEATURE_SET=""
if not -%2-==-- set FEATURE_SET=%2

if -%BUILD_PY_VENV_PATH%-==-- set "BUILD_PY_VENV_PATH=%HOMEDRIVE%%HOMEPATH%\.python_venv\build"
set "VENV_ACT=%BUILD_PY_VENV_PATH%\Scripts\activate"
if -%SW_PROJECTS_ROOT%-==-- set "SW_PROJECTS_ROOT=%HOMEDRIVE%%HOMEPATH%\GITROOT\sw\projects"
set "PROJECT_ROOT=%SW_PROJECTS_ROOT%\%PROJECT%"

rem pruefen, ob noetige Dateien existieren
set REMOVE_CONFIG_FILE=false
set "BUILD_ROOT=%PROJECT_ROOT%\build"
set "CONFIG_FILE=%PROJECT_ROOT%\%CONFIG_FILE_NAME%"
if not exist %PROJECT_ROOT% (
  echo Projekt-Verzeichnis %PROJECT_ROOT% nicht gefunden
  exit /b
)
if not -%FEATURE_SET%-==-- (
  set "CONFIG_DIR=%BUILD_ROOT%\featuresets\%FEATURE_SET%\wheel"
  if not exist %CONFIG_DIR% (
    echo Konfigurations-Verzeichnis %CONFIG_DIR% nicht gefunden
    exit /b
  )
  set "FEATURE_SET_CONFIG_FILE=%CONFIG_DIR%\%CONFIG_FILE_NAME%"
  if not exist %FEATURE_SET_CONFIG_FILE% (
    echo Konfigurationsdatei %FEATURE_SET_CONFIG_FILE% nicht gefunden
    exit /b
  )
  copy %FEATURE_SET_CONFIG_FILE% %PROJECT_ROOT%\%CONFIG_FILE_NAME%
  set REMOVE_CONFIG_FILE=true
)
if not exist %CONFIG_FILE% (
  echo Konfigurationsdatei %CONFIG_FILE% nicht gefunden
  exit /b
)

rem Build starten
pushd %PROJECT_ROOT%
call %VENV_ACT%
echo Build %PROJECT% %FEATURE_SET%
hatchling build
call deactivate
if %REMOVE_CONFIG_FILE%==true del %CONFIG_FILE%
popd
