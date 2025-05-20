# -*- coding: utf-8 -*-

# Erzeugt ein Debian-Installationspaket für eine Python-Applikation.
# Aufruf: python3 build_py_deb.py <Build-Script-Path> <Projekt-Root> [<Feature-Set>]

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomli


PY_CONFIG_FILE_NAME = 'pyproject.toml'
BUILD_WHEEL_SCRIPT = 'build_py_wheel'

ATTR_DEB_FILE_NAME = 'deb-file-name'
ATTR_PYTHON_PACKAGE_NAME = 'python-package-name'
ATTR_VERSION = 'version'
ATTR_WHEEL_FILE_NAME = 'wheel-file-name'

CONTROL_ARCHIVE_FILE_NAME = 'control.tar.xz'
DATA_ARCHIVE_FILE_NAME = 'data.tar.xz'
PACKAGE_VERSION_FILE_NAME = 'debian-binary'


def run_command(cmd: list[str]) -> int:
    """
    Fuehrt den uebergebenen Befehl aus.
    :param cmd: Befehl, ggf. mit Parametern
    :returns: Returncode, 0 fuer OK
    """
    res = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    if len(res.stderr) > 0: print(res.stderr)
    if len(res.stdout) > 0: print(res.stdout)
    return res.returncode


def copy_customizable_file(project_name: str, source_path: str, file_name: str, target_path: str, feature: dict):
    """
    Kopiert eine Datei ins Build-Verzeichnis und ersetzt ggf. Variablen.
    :param project_name: Name des Projekts
    :param source_path: Verzeichnis, in dem die Datei liegt
    :param file_name: Name der Datei
    :param target_path: Zielverzeichnis
    :param feature: relevante Daten des Feature-Sets
    """
    _install_path = os.path.join('/opt', project_name)
    _source_fn = os.path.join(source_path, file_name)
    _stat = os.stat(_source_fn)
    with open(_source_fn, 'r') as _f:
        _contents = _f.read()
    _contents = _contents.replace('${VERSION}', feature[ATTR_VERSION])
    _contents = _contents.replace('${PACKAGE_NAME}', feature[ATTR_PYTHON_PACKAGE_NAME])
    _contents = _contents.replace('${WHEEL_FILE_NAME}', feature[ATTR_WHEEL_FILE_NAME])
    _contents = _contents.replace('${INSTALL_PATH}', _install_path)
    _target_fn = os.path.join(target_path, file_name)
    with open(_target_fn, 'w') as _f:
        _f.write(_contents)
    os.chmod(_target_fn, _stat.st_mode)


def copy_customizable_file_tree(project_name: str, source_path: str, target_path: str, feature: dict):
    """
    Kopiert einen Verzeichnisbaum ins Build-Verzeichnis und ersetzt ggf. Variablen in den kopierten Dateien.
    :param project_name: Name des Projekts
    :param source_path: Verzeichnis, in dem die Datei liegt
    :param target_path: Zielverzeichnis
    :param feature: relevante Daten des Feature-Sets
    """
    for _dir, _sub_dirs, _files in os.walk(source_path):
        _source_dir = _dir[len(source_path):].lstrip(os.sep)
        _target_dir = os.path.join(target_path, _source_dir)
        os.makedirs(_target_dir, mode=0o755, exist_ok=True)
        for _f in _files:
            copy_customizable_file(project_name, _dir, _f, _target_dir, feature)


def py_config_info(project_root: str, file_path: str) -> dict:
    """
    :param project_root: Root-Verzeichnis des Projekts
    :param file_path: Name und Pfad der hatchling-Konfigurationsdatei
    :returns: relevante Daten der hatchling-Konfigurationsdatei
    """
    if not os.path.isfile(file_path):
        raise RuntimeError(f'Konfigurationsdatei {file_path} nicht gefunden')
    with open(file_path, "rb") as _config_file:
        _toml_data = tomli.load(_config_file)
        _py_package_name = _toml_data['project']['name']
        _version_fn = _toml_data['tool']['hatch']['version']['path']
        _version_file_path = os.path.join(project_root, _version_fn)
        _version_pattern = re.compile(r'^\s*VERSION\s*=\s*(.*)$')
        with open(_version_file_path, 'r') as _src_file:
            _lines = _src_file.readlines()
            for _line in _lines:
                _vm = _version_pattern.match(_line.strip())
                if _vm:
                    _version = _vm.group(1).strip('"').strip("'")
                    break
    _deb_file_name = f'{_py_package_name}-{_version}.deb'.replace('_', '-')
    _wheel_file_name = f'{_py_package_name}-{_version}-py3-none-any.whl'
    return {ATTR_PYTHON_PACKAGE_NAME: _py_package_name, ATTR_VERSION: _version,
            ATTR_DEB_FILE_NAME: _deb_file_name, ATTR_WHEEL_FILE_NAME: _wheel_file_name}


def feature_sets(project_root: str) -> list[str]:
    """
    :param project_root: Root-Verzeichnis des Projekts
    :returns: Namen der Feature-Sets des Projekts
    """
    if not os.path.isdir(project_root):
        raise RuntimeError(f'Projektverzeichnis {project_root} nicht gefunden')
    _features_path = os.path.join(project_root, 'build', 'featuresets')
    return os.listdir(_features_path) if os.path.isdir(_features_path) else []


def feature_info(project_root: str, feature_name: str | None) -> dict:
    """
    Liest die pyproject-toml-Datei und gibt die fuer das Bauen des deb-Pakets
    relevanten Daten zurueck.
    :param project_root: Root-Verzeichnis des Projekts
    :param feature_name: Name des Feature-Sets
    :returns: Daten des Feature-Sets
    """
    if feature_name is None:
        _cfg_file_path = os.path.join(project_root, PY_CONFIG_FILE_NAME)
    else:
        _cfg_file_path = os.path.join(project_root, 'build', 'featuresets', feature_name, 'wheel', PY_CONFIG_FILE_NAME)
    return py_config_info(project_root, _cfg_file_path)


def build_wheel(build_scripts_path: str, project_name: str, feature_name: str | None):
    """
    Erzeugt ein Python wheel für Projekt und Feature in <Projekt-Root>/dist.
    :param build_scripts_path: Verzeichnis mit den Build-Scripts
    :param project_name: Name des Projekts
    :param feature_name: Name des Feature-Sets
    """
    _build_wheel_script_path = os.path.join(build_scripts_path, BUILD_WHEEL_SCRIPT)
    _cmd = [_build_wheel_script_path, project_name]
    if feature_name is not None and len(feature_name) > 0: _cmd.append(feature_name)
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Build Python wheel für {project_name} {feature_name} fehlgeschlagen')


def build_project_feature(build_scripts_path: str, project_root: str, feature_name: str | None):
    """
    Erzeugt ein Debian deb-Paket für Projekt und Feature in <Projekt-Root>/dist.
    :param build_scripts_path: Verzeichnis mit den Build-Scripts
    :param project_root: Root-Verzeichnis des Projekts
    :param feature_name: Name des Feature-Sets
    """
    _project_name = os.path.basename(project_root)
    _feature = feature_info(project_root, feature_name)
    # data-Archiv erzeugen
    with tempfile.TemporaryDirectory() as _target_path:
        # Python wheel erzeugen und in /opt/<project> ablegen
        build_wheel(build_scripts_path, _project_name, feature_name)
        _build_target_path = os.path.join(project_root, 'dist')
        _target_wheel_path = os.path.join(_target_path, 'opt', _project_name)
        os.makedirs(_target_wheel_path, mode=0o755, exist_ok=True)
        shutil.move(os.path.join(_build_target_path, _feature[ATTR_WHEEL_FILE_NAME]), _target_wheel_path)
        # projektspezifische Daten kopieren
        if feature_name is None:
            _source_data_path = os.path.join(project_root, 'build', 'deb', 'data')
        else:
            _source_data_path = os.path.join(project_root, 'build', 'featuresets', feature_name, 'deb', 'data')
        copy_customizable_file_tree(_project_name, _source_data_path, _target_path, _feature)
        #shutil.copytree(_source_data_path, _target_path, dirs_exist_ok=True)
        _data_elements = os.listdir(_target_path)
        os.chdir(_target_path)
        _cmd = ['tar', '-cJf', DATA_ARCHIVE_FILE_NAME]
        _cmd.extend(_data_elements)
        _rc = run_command(_cmd)
        if _rc != 0:
            raise RuntimeError(f'Konnte data-Archiv für {_project_name} {feature_name} nicht erzeugen')
        shutil.copy(os.path.join(_target_path, DATA_ARCHIVE_FILE_NAME), _build_target_path)
    # control-Archiv erzeugen
    with tempfile.TemporaryDirectory() as _target_path:
        # Steuerdateien kopieren
        if feature_name is None:
            _source_data_path = os.path.join(project_root, 'build', 'deb', 'control')
        else:
            _source_data_path = os.path.join(project_root, 'build', 'featuresets', feature_name, 'deb', 'control')
        for _f in os.listdir(_source_data_path):
            copy_customizable_file(_project_name, _source_data_path, _f, _target_path, _feature)
        # control-Archiv erzeugen
        _control_elements = os.listdir(_target_path)
        os.chdir(_target_path)
        _cmd = ['tar', '-cJf', CONTROL_ARCHIVE_FILE_NAME]
        _cmd.extend(_control_elements)
        _rc = run_command(_cmd)
        if _rc != 0:
            raise RuntimeError(f'Konnte control-Archiv für {_project_name} {feature_name} nicht erzeugen')
        shutil.copy(os.path.join(_target_path, CONTROL_ARCHIVE_FILE_NAME), _build_target_path)
    # Debian-Package-Version kopieren
    if feature_name is None:
        _ver_file = os.path.join(project_root, 'build', 'deb', PACKAGE_VERSION_FILE_NAME)
    else:
        _ver_file = os.path.join(project_root, 'build', 'featuresets', feature_name, 'deb', PACKAGE_VERSION_FILE_NAME)
    shutil.copy(_ver_file, _build_target_path)
    # deb-Datei erzeugen
    _deb_project_name = _project_name if len(feature_name) == 0 else f'{_project_name}-{feature_name}'
    _deb_package_name = _feature[ATTR_DEB_FILE_NAME]
    os.chdir(_build_target_path)
    _cmd = ['ar', 'cvr', _deb_package_name, PACKAGE_VERSION_FILE_NAME]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Konnte Debian-Installationspaket für {_project_name} {feature_name} nicht erzeugen')
    _cmd = ['ar', 'vr', _deb_package_name, CONTROL_ARCHIVE_FILE_NAME]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Konnte Debian-Installationspaket für {_project_name} {feature_name} nicht erzeugen')
    _cmd = ['ar', 'vr', _deb_package_name, DATA_ARCHIVE_FILE_NAME]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Konnte Debian-Installationspaket für {_project_name} {feature_name} nicht erzeugen')
    os.remove(os.path.join(_build_target_path, CONTROL_ARCHIVE_FILE_NAME))
    os.remove(os.path.join(_build_target_path, DATA_ARCHIVE_FILE_NAME))
    os.remove(os.path.join(_build_target_path, PACKAGE_VERSION_FILE_NAME))
    print(f'Debian Installationspaket {_deb_package_name} erstellt.')


# Hauptprogramm
_project_root_path = None
_build_scripts_path = None
_feature_set = None
if len(sys.argv) == 3:
    _build_scripts_path = sys.argv[1]
    _project_root_path = sys.argv[2]
elif len(sys.argv) == 4:
    _build_scripts_path = sys.argv[1]
    _project_root_path = sys.argv[2]
    _feature_set = sys.argv[3]
else:
    print('Aufruf: python3 build_py_deb.py <Build-Script-Path> <Projekt-Root> [<Feature-Umfang>]')
    sys.exit(1)
try:
    _feature_sets = feature_sets(_project_root_path)
    if _feature_set == 'all':
        for _fs in _feature_sets:
            build_project_feature(_build_scripts_path, _project_root_path, _fs)
    elif _feature_set is not None:
        if _feature_set not in _feature_sets:
            raise RuntimeError(f'Feature-Set {_feature_set} nicht gefunden')
        build_project_feature(_build_scripts_path, _project_root_path, _feature_set)
    else:
        if len(_feature_sets) == 0:
            build_project_feature(_build_scripts_path, _project_root_path, None)
        elif len(_feature_sets) == 1:
            build_project_feature(_build_scripts_path, _project_root_path, _feature_sets[0])
        else:
            raise RuntimeError(f'Feature-Set muss angegeben werden {_feature_sets}')
except RuntimeError as _e:
    print(f'+++ {_e} +++')
    sys.exit(1)
