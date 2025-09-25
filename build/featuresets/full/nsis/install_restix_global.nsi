# =============================================================================
# install_restix_global.nsi
#
# NSIS-Script zur systemweiten Installation von restix auf Windows.
# Benötigt special build mit max. Stringlänge 8192.
# Benötigt Plugin envar.
#
# Copyright (c) 2025 Frank Sommer.
# =============================================================================

!pragma warning error all
!include LogicLib.nsh

InstallDir "$PROGRAMFILES64\restix"
OutFile restix_install.exe
RequestExecutionLevel admin
XPStyle on

Page license
Page components
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

var actScript
var deactScript
var wheelFile

LoadLanguageFile "${NSISDIR}\Contrib\Language files\English.nlf"
LoadLanguageFile "${NSISDIR}\Contrib\Language files\German.nlf"

LicenseData restix_license.txt


# =============================================================================
# Lokalisierte String-Konstanten
# =============================================================================
LangString Name ${LANG_ENGLISH} "restix"
LangString Name ${LANG_GERMAN} "restix"
Name $(Name)

LangString ^ComponentsText ${LANG_ENGLISH} "restix components"
LangString ^ComponentsText ${LANG_GERMAN} "restix-Komponenten"

LangString CompletedText ${LANG_ENGLISH} "Restix installation complete"
LangString CompletedText ${LANG_GERMAN} "Restix-Installation abgeschlossen"

LangString CreatePyVenvMsg ${LANG_ENGLISH} "Creating Python virtual environment.$\r$\nThis will take a while..."
LangString CreatePyVenvMsg ${LANG_GERMAN} "Erzeuge Python virtual environment.$\r$\nDies kann einige Minuten dauern..."

LangString FileWriteFailed ${LANG_ENGLISH} "Could not write file "
LangString FileWriteFailed ${LANG_GERMAN} "Kein Schreibzugriff für Datei "

LangString PythonNotFound ${LANG_ENGLISH} "$(NAME) requires Python"
LangString PythonNotFound ${LANG_GERMAN} "$(NAME) benötigt Python"

LangString CreateDirFailed ${LANG_ENGLISH} "Could not create directory"
LangString CreateDirFailed ${LANG_GERMAN} "Fehler beim Anlegen von Verzeichnis"

LangString CreateVenvFailed ${LANG_ENGLISH} "Could not create Python virtual environment"
LangString CreateVenvFailed ${LANG_GERMAN} "Fehler beim Erzeugen von Python virtual environment"

LangString PrepareVenvFailed ${LANG_ENGLISH} "Could not install restix library to Python virtual environment"
LangString PrepareVenvFailed ${LANG_GERMAN} "Fehler beim Installieren der restix-Bibliothek in Python virtual environment"

LangString CommandExecutionFailed ${LANG_ENGLISH} "Error executing command "
LangString CommandExecutionFailed ${LANG_GERMAN} "Fehler beim Ausführen des Befehls "

LangString AbortMsg ${LANG_ENGLISH} "Installation aborted:$\r$\n"
LangString AbortMsg ${LANG_GERMAN} "Installation abgebrochen:$\r$\n"


# =============================================================================
# Sections
# =============================================================================

# Vollständige Installation mit GUI.
LangString Sec1Name ${LANG_ENGLISH} "GUI"
LangString Sec1Name ${LANG_GERMAN} "Grafische Oberfläche"
Section !$(Sec1Name) sec1
    StrCpy $wheelFile "restix-${VERSION}-py3-none-any.whl"
	SetOutPath $INSTDIR
	File /r "data\*.*"
	Push "restix"
	Call createStarterScript
	Push "grestix"
	Call createStarterScript
	Push $wheelFile
	Call createPythonVenv
	EnVar::SetHKLM
	EnVar::AddValue "PATH" "$INSTDIR;"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\restix" "DisplayName" "Restix"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\restix" "UninstallString" "$\"$INSTDIR\uninstall_restix.exe$\""
	WriteUninstaller $INSTDIR\uninstall_restix.exe
SectionEnd

# Core-Installation ohne GUI.
# Wird nur dann ausgeführt, wenn Komponente GUI vom Benutzer abgewählt wurde.
Section ""
    ${If} $wheelFile == ""
		SetOutPath $INSTDIR
		File /r "data\*.*"
		Push "restix"
		Call createStarterScript
		Push "restix_core-${VERSION}-py3-none-any.whl"
		Call createPythonVenv
		EnVar::SetHKLM
		EnVar::AddValue "PATH" "$INSTDIR;"
		WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\restix" "DisplayName" "Restix"
		WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\restix" "QuietUninstallString" '"$INSTDIR\uninstall_restix.exe" /S'
		WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\restix" "UninstallString" '"$INSTDIR\uninstall_restix.exe"'
		WriteUninstaller $INSTDIR\uninstall_restix.exe
	${EndIf}
SectionEnd

# Startmenü-Eintrag.
LangString Sec2Name ${LANG_ENGLISH} "Start menu entry"
LangString Sec2Name ${LANG_GERMAN} "Eintrag im Startmenü"
Section !$(Sec2Name) sec2
    ${If} $wheelFile != ""
		SetShellVarContext all
		CreateShortcut "$SMPROGRAMS\restix.lnk" "$INSTDIR\grestix.cmd" "" "$INSTDIR\restix-icon.ico" 0 SW_SHOWMINIMIZED
	${EndIf}
SectionEnd

# Icon auf dem Schreibtisch.
LangString Sec3Name ${LANG_ENGLISH} "Desktop shortcut"
LangString Sec3Name ${LANG_GERMAN} "Icon auf dem Schreibtisch"
Section !$(Sec3Name) sec3
    ${If} $wheelFile != ""
		SetShellVarContext all
		CreateShortcut "$DESKTOP\restix.lnk" "$INSTDIR\grestix.cmd" "" "$INSTDIR\restix-icon.ico" 0 SW_SHOWMINIMIZED
	${EndIf}
SectionEnd

# Deinstallation.
LangString SecUninstName ${LANG_ENGLISH} "Remove $(NAME)"
LangString SecUninstName ${LANG_GERMAN} "$(NAME) entfernen"
Section "uninstall"
	SetShellVarContext all
	# Shortcuts entfernen
	Delete "$SMPROGRAMS\restix.lnk"
	Delete "$DESKTOP\restix.lnk"
	# restix-Verzeichnis aus PATH entfernen
	EnVar::SetHKLM
	EnVar::DeleteValue "PATH" "$INSTDIR;"
	# Uninstaller-Info aus Registry entfernen
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\restix"
	# Restix-Dateien entfernen
	RMDir /r $INSTDIR
SectionEnd


# =============================================================================
# Functions
# =============================================================================

# Sprachauswahl
Function .onInit
	Push ""
	Push ${LANG_ENGLISH}
	Push English
	Push ${LANG_GERMAN}
	Push Deutsch
	Push A
	LangDLL::LangDialog "Installer Language" "Please select the language of the installer"
	Pop $LANGUAGE
	StrCmp $LANGUAGE "cancel" 0 +2
		Abort
FunctionEnd

# Erzeugt ein cmd-Script zum Starten von restix.
# Parameter: vom Script zu startendes restix-Executable (restix.exe für CLI, grestix.exe für GUI).
Function createStarterScript
    Pop $0
	ClearErrors
	FileOpen $1 "$INSTDIR\$0.cmd" w
	IfErrors 0 +3
	Push "$(FileWriteFailed) $0"
	Call abortInstaller
	FileWrite $1 "@echo off$\r$\n"
	FileWrite $1 "setlocal$\r$\n"
    FileWrite $1 "set $\"VENV_ACTIVATION_FILE=$INSTDIR\.venv\Scripts\activate.bat$\"$\r$\n"
    FileWrite $1 "set $\"VENV_DEACTIVATION_FILE=$INSTDIR\.venv\Scripts\deactivate.bat$\"$\r$\n"
    FileWrite $1 'call "%VENV_ACTIVATION_FILE%"$\r$\n'
    FileWrite $1 '"$INSTDIR\.venv\Scripts\$0.exe" %*$\r$\n'
    FileWrite $1 'call "%VENV_DEACTIVATION_FILE%"$\r$\n'
	FileClose $1
FunctionEnd

# Erzeugt das Python virtual environment mit den nötigen Paketen.
# Parameter: Python wheel für restix (core/full).
Function createPythonVenv
    Pop $0
	Push "python --version"
	Call execAndAbortOnFail
	MessageBox MB_OK "$(CreatePyVenvMsg)"
	StrCpy $actScript "$INSTDIR\.venv\Scripts\activate.bat"
	StrCpy $deactScript "$INSTDIR\.venv\Scripts\deactivate.bat"
	CreateDirectory $INSTDIR\.venv
	IfErrors 0 +3
	Push "$(CreateDirFailed) $INSTDIR\.venv"
	Call abortInstaller
	Push 'python -m venv "$INSTDIR\.venv"'
	Call execAndAbortOnFail
	Push '"$actScript" && pip3 install "$INSTDIR\$0" && "$deactScript"'
	Call execAndAbortOnFail
FunctionEnd

# Führt einen Windows-Befehl aus und bricht die Installation bei Misserfolg ab.
# Parameter: auszuführender Befehl
Function execAndAbortOnFail
    Pop $9
	nsExec::ExecToStack $9
	Pop $8
	Pop $7
	${If} $8 == 0
	    Return
	${EndIf}
	Push "$(CommandExecutionFailed) $9$\r$\n$7"
	Call abortInstaller
	Abort
FunctionEnd

# Bricht die Installation ab.
# Parameter: Grund für den Abbruch
Function abortInstaller
    Pop $9
	MessageBox MB_OK|MB_ICONSTOP "$(AbortMsg)$9"
	Abort
FunctionEnd
