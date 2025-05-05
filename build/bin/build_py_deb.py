#!/usr/bin/python3

# Erzeugt ein Debian-Installationspaket für eine Python-Applikation.

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomli


PROJECTS_ROOT = os.path.join(os.path.expanduser('~'), 'GITROOT', 'sw', 'projects')
BUILD_WHEEL_SCRIPT = os.path.join(os.path.expanduser('~'), 'bin', 'build_py_wheel')

ATTR_DEB_FILE_NAME = 'deb-file-name'
ATTR_FEATURE_NAME = 'feature-name'
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


def copy_control_file(source_path, file_name: str, target_path: str, feature: dict):
    """
    Kopiert eine Steuerdatei ins Build-Verzeichnis und ersetzt ggf. Variablen.
    :param source_path: Verzeichnis, in dem die Steuerdatei liegt
    :param file_name: Name der Steuerdatei
    :param target_path: Zielverzeichnis
    :param feature: relevante Daten des Feature-Sets
    """
    _source_fn = os.path.join(source_path, file_name)
    _stat = os.stat(_source_fn)
    with open(_source_fn, 'r') as _f:
        _contents = _f.read()
    _contents = _contents.replace('${VERSION}', feature[ATTR_VERSION])
    _contents = _contents.replace('${WHEEL_FILE_NAME}', feature[ATTR_WHEEL_FILE_NAME])
    _target_fn = os.path.join(target_path, file_name)
    with open(_target_fn, 'w') as _f:
        _f.write(_contents)
    os.chmod(_target_fn, _stat.st_mode)


def hatchling_info(project_name: str) -> dict:
    """
    Liest die vorhandenen pyproject-toml-Dateien und gibt die fuer das Bauen des deb-Pakets
    relevanten Daten zurueck.
    :param project_name: Name des Projekts
    :returns: Daten jedes Feature-Sets fuer das Projekt
    """
    _project_root = os.path.join(PROJECTS_ROOT, project_name)
    if not os.path.isdir(_project_root):
        raise RuntimeError(f'Projektverzeichnis {_project_root} nicht gefunden')
    _build_wheel_dir = os.path.join(_project_root, 'build', 'wheel')
    if not os.path.isdir(_build_wheel_dir):
        raise RuntimeError(f'Build-Verzeichnis {_build_wheel_dir} nicht gefunden')
    _info = {}
    _version_pattern = re.compile(r'^\s*VERSION\s*=\s*(.*)$')
    _config_file_pattern = re.compile('pyproject(.*).toml')
    for _f in os.listdir(_build_wheel_dir):
        _m = _config_file_pattern.match(_f)
        if _m:
            _version = ''
            _feature_name = _m.group(1)[1:] if _m.group(1).startswith('-') else _m.group(1)
            _full_fn = os.path.join(_build_wheel_dir, _f)
            with open(_full_fn, "rb") as _config_file:
                _toml_data = tomli.load(_config_file)
                _feature_project_name = _toml_data['project']['name']
                _version_fn = _toml_data['tool']['hatch']['version']['path']
                _version_file_path = os.path.join(_project_root, _version_fn)
                with open(_version_file_path, 'r') as _src_file:
                    _lines = _src_file.readlines()
                    for _line in _lines:
                        _vm = _version_pattern.match(_line.strip())
                        if _vm:
                            _version = _vm.group(1).strip('"').strip("'")
                            break
            _deb_file_name = f'{_feature_project_name}-{_version}.deb'.replace('_', '-')
            _wheel_file_name = f'{_feature_project_name}-{_version}-py3-none-any.whl'
            _info[_feature_name] = {ATTR_FEATURE_NAME: _feature_name, ATTR_VERSION: _version,
                                    ATTR_DEB_FILE_NAME: _deb_file_name, ATTR_WHEEL_FILE_NAME: _wheel_file_name, }
    if len(_info) == 0:
        raise RuntimeError(f'Keine Konfigurationsdateien in {_build_wheel_dir} gefunden')
    return _info


def build_wheel(project_name: str, feature_name: str):
    """
    Erzeugt ein Python wheel für Projekt und Feature in <Projekt-Root>/dist.
    :param project_name: Name des Projekts
    :param feature_name: Name des Feature-Sets
    """
    _cmd = [BUILD_WHEEL_SCRIPT, project_name]
    if len(feature_name) > 0: _cmd.append(feature_name)
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Build Python wheel für {project_name} {feature_name} fehlgeschlagen')


def build_project_feature(project_name: str, feature: dict):
    """
    Erzeugt ein Debian deb-Paket für Projekt und Feature in <Projekt-Root>/dist.
    :param project_name: Name des Projekts
    :param feature: relevante Daten des Feature-Sets
    """
    # data-Archiv erzeugen
    with tempfile.TemporaryDirectory() as _target_path:
        # Python wheel erzeugen und in /opt/<project> ablegen
        build_wheel(project_name, feature[ATTR_FEATURE_NAME])
        _build_target_path = os.path.join(PROJECTS_ROOT, project_name, 'dist')
        _target_wheel_path = os.path.join(_target_path, 'opt', project_name)
        os.makedirs(_target_wheel_path, mode=0o755, exist_ok=True)
        shutil.move(os.path.join(_build_target_path, feature[ATTR_WHEEL_FILE_NAME]), _target_wheel_path)
        # projektspezifische Daten kopieren
        _source_data_path = os.path.join(PROJECTS_ROOT, project_name, 'build', 'deb', 'data')
        shutil.copytree(_source_data_path, _target_path, dirs_exist_ok=True)
        _data_elements = os.listdir(_target_path)
        os.chdir(_target_path)
        _cmd = ['tar', '-cJf', DATA_ARCHIVE_FILE_NAME]
        _cmd.extend(_data_elements)
        _rc = run_command(_cmd)
        if _rc != 0:
            raise RuntimeError(f'Konnte data-Archiv für {project_name} {feature[ATTR_FEATURE_NAME]} nicht erzeugen')
        shutil.copy(os.path.join(_target_path, DATA_ARCHIVE_FILE_NAME), _build_target_path)
    # control-Archiv erzeugen
    with tempfile.TemporaryDirectory() as _target_path:
        # Steuerdateien kopieren
        _source_data_path = os.path.join(PROJECTS_ROOT, project_name, 'build', 'deb', 'control')
        for _f in os.listdir(_source_data_path):
            copy_control_file(_source_data_path, _f, _target_path, feature)
        # control-Archiv erzeugen
        _control_elements = os.listdir(_target_path)
        os.chdir(_target_path)
        _cmd = ['tar', '-cJf', CONTROL_ARCHIVE_FILE_NAME]
        _cmd.extend(_control_elements)
        _rc = run_command(_cmd)
        if _rc != 0:
            raise RuntimeError(f'Konnte control-Archiv für {project_name} {feature[ATTR_FEATURE_NAME]} nicht erzeugen')
        shutil.copy(os.path.join(_target_path, CONTROL_ARCHIVE_FILE_NAME), _build_target_path)
    # Debian-Package-Version kopieren
    shutil.copy(os.path.join(PROJECTS_ROOT, project_name, 'build', 'deb', PACKAGE_VERSION_FILE_NAME), _build_target_path)
    # deb-Datei erzeugen
    _deb_project_name = project_name if len(feature[ATTR_FEATURE_NAME]) == 0 else f'{project_name}-{feature[ATTR_FEATURE_NAME]}'
    _deb_package_name = feature[ATTR_DEB_FILE_NAME]
    os.chdir(_build_target_path)
    _cmd = ['ar', 'cvr', _deb_package_name, PACKAGE_VERSION_FILE_NAME]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Konnte Debian-Installationspaket für {project_name} {feature[ATTR_FEATURE_NAME]} nicht erzeugen')
    _cmd = ['ar', 'vr', _deb_package_name, CONTROL_ARCHIVE_FILE_NAME]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Konnte Debian-Installationspaket für {project_name} {feature[ATTR_FEATURE_NAME]} nicht erzeugen')
    _cmd = ['ar', 'vr', _deb_package_name, DATA_ARCHIVE_FILE_NAME]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Konnte Debian-Installationspaket für {project_name} {feature[ATTR_FEATURE_NAME]} nicht erzeugen')
    os.remove(os.path.join(_build_target_path, CONTROL_ARCHIVE_FILE_NAME))
    os.remove(os.path.join(_build_target_path, DATA_ARCHIVE_FILE_NAME))
    os.remove(os.path.join(_build_target_path, PACKAGE_VERSION_FILE_NAME))
    print(f'Debian Installationspaket {_deb_package_name} erstellt.')


# Hauptprogramm
_project = None
_feature_set = None
if len(sys.argv) == 2:
    _project = sys.argv[1]
elif len(sys.argv) == 3:
    _project = sys.argv[1]
    _feature_set = sys.argv[2]
else:
    print('Aufruf: build_py_deb <Projekt> [<Feature-Umfang>]')
    sys.exit(1)
try:
    _project_info = hatchling_info(_project)
    if _feature_set is not None and _feature_set not in _project_info:
        raise RuntimeError(f'Feature-Set {_feature_set} nicht gefunden')
    if len(_project_info) == 1:
        build_project_feature(_project, next(iter(_project_info)))
    elif len(_project_info) > 1:
        if _feature_set is None:
            for _feature in _project_info.values():
                build_project_feature(_project, _feature)
        else:
            build_project_feature(_project, _project_info.get(_feature_set))
except RuntimeError as _e:
    print(f'+++ {_e} +++')
    sys.exit(1)
