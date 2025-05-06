# Erzeugt ein rpm-Installationspaket für eine Python-Applikation.

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomli


PY_CONFIG_FILE_NAME = 'pyproject.toml'
PROJECTS_ROOT = os.path.join(os.path.expanduser('~'), 'GITROOT', 'sw', 'projects')
RPM_WORK_PATH = os.path.join(os.path.expanduser('~'), 'rpmbuild')
BUILD_WHEEL_SCRIPT = os.path.join(os.path.expanduser('~'), 'bin', 'build_py_wheel')
RPM_WORK_SUBDIRS = ['BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS', 'tmp']

ATTR_PYTHON_PACKAGE_NAME = 'python-package-name'
ATTR_VERSION = 'version'
ATTR_WHEEL_FILE_NAME = 'wheel-file-name'


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


def create_work_dir():
    """
    Erzeugt das Arbeitsverzeichnis fuer den rpm build.
    """
    _rc = run_command(['rm', '-rf', RPM_WORK_PATH])
    if _rc != 0:
        raise RuntimeError(f'Konnte Arbeitsverzeichnis {RPM_WORK_PATH} nicht löschen')
    _rc = run_command(['mkdir', RPM_WORK_PATH])
    if _rc != 0:
        raise RuntimeError(f'Konnte Arbeitsverzeichnis {RPM_WORK_PATH} nicht anlegen')
    for _sub_dir in RPM_WORK_SUBDIRS:
        _sub_dir_path = os.path.join(RPM_WORK_PATH, _sub_dir)
        _rc = run_command(['mkdir', _sub_dir_path])
        if _rc != 0:
            raise RuntimeError(f'Konnte Verzeichnis {_sub_dir_path} nicht anlegen')


def copy_spec_file(source_path: str, file_name: str, target_path: str, project_name: str, feature: dict):
    """
    Kopiert eine Steuerdatei ins Build-Verzeichnis und ersetzt ggf. Variablen.
    :param source_path: Verzeichnis, in dem die Steuerdatei liegt
    :param file_name: Name der Steuerdatei
    :param target_path: Zielverzeichnis
    :param project_name: Name des Projekts
    :param feature: relevante Daten des Feature-Sets
    """
    _version = feature[ATTR_VERSION]
    _rpm_proj_dir = f'{project_name}-{_version}-root'
    _rpm_build_root = os.path.join(RPM_WORK_PATH, 'tmp', _rpm_proj_dir)
    _source_fn = os.path.join(source_path, file_name)
    _stat = os.stat(_source_fn)
    with open(_source_fn, 'r') as _f:
        _contents = _f.read()
    _contents = _contents.replace('${VERSION}', _version)
    _contents = _contents.replace('${PACKAGE_NAME}', feature[ATTR_PYTHON_PACKAGE_NAME])
    _contents = _contents.replace('${WHEEL_FILE_NAME}', feature[ATTR_WHEEL_FILE_NAME])
    _contents = _contents.replace('${RPM_BUILD_ROOT}', _rpm_build_root)
    _target_fn = os.path.join(target_path, file_name)
    with open(_target_fn, 'w') as _f:
        _f.write(_contents)
    os.chmod(_target_fn, _stat.st_mode)


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
    _wheel_file_name = f'{_py_package_name}-{_version}-py3-none-any.whl'
    return {ATTR_PYTHON_PACKAGE_NAME: _py_package_name, ATTR_VERSION: _version, ATTR_WHEEL_FILE_NAME: _wheel_file_name}


def feature_sets(project_name: str) -> list[str]:
    """
    :param project_name: Name des Projekts
    :returns: Namen der Feature-Sets des uebergebenen Projekts
    """
    _project_root = os.path.join(PROJECTS_ROOT, project_name)
    if not os.path.isdir(_project_root):
        raise RuntimeError(f'Projektverzeichnis {_project_root} nicht gefunden')
    _features_path = os.path.join(_project_root, 'build', 'featuresets')
    return os.listdir(_features_path) if os.path.isdir(_features_path) else []


def feature_info(project_name: str, feature_name: str | None) -> dict:
    """
    Liest die pyproject-toml-Datei und gibt die fuer das Bauen des deb-Pakets
    relevanten Daten zurueck.
    :param project_name: Name des Projekts
    :param feature_name: Name des Feature-Sets
    :returns: Daten des Feature-Sets
    """
    _project_root = os.path.join(PROJECTS_ROOT, project_name)
    if feature_name is None:
        _cfg_file_path = os.path.join(_project_root, PY_CONFIG_FILE_NAME)
    else:
        _cfg_file_path = os.path.join(_project_root, 'build', 'featuresets', feature_name,
                                      'wheel', PY_CONFIG_FILE_NAME)
    return py_config_info(_project_root, _cfg_file_path)


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


def build_project_feature(project_name: str, feature_name: str | None):
    """
    Erzeugt ein rpm-Paket für Projekt und Feature in <Projekt-Root>/dist.
    :param project_name: Name des Projekts
    :param feature_name: Name des Feature-Sets
    """
    _feature = feature_info(project_name, feature_name)
    _py_package_name = _feature[ATTR_PYTHON_PACKAGE_NAME]
    create_work_dir()
    _project_dir = f'{_py_package_name}-{_feature[ATTR_VERSION]}'
    # Archiv mit den Projekt-Dateien erzeugen
    with tempfile.TemporaryDirectory() as _temp_path:
        _archive_project_root = os.path.join(_temp_path, _project_dir)
        _archive_file_name = f'{_project_dir}.tar.gz'
        os.mkdir(_archive_project_root, mode=0o755)
        # Python wheel erzeugen und in /opt/<project> ablegen
        build_wheel(project_name, feature_name)
        _wheel_source_path = os.path.join(PROJECTS_ROOT, project_name, 'dist')
        _wheel_target_path = os.path.join(_archive_project_root, 'opt', project_name)
        os.makedirs(_wheel_target_path, mode=0o755, exist_ok=True)
        shutil.move(os.path.join(_wheel_source_path, _feature[ATTR_WHEEL_FILE_NAME]), _wheel_target_path)
        # projektspezifische Daten kopieren
        if feature_name is None:
            _source_data_path = os.path.join(PROJECTS_ROOT, project_name, 'build', 'rpm', 'SOURCES')
        else:
            _source_data_path = os.path.join(PROJECTS_ROOT, project_name, 'build', 'featuresets',
                                                feature_name, 'rpm', 'SOURCES')
        shutil.copytree(_source_data_path, _archive_project_root, dirs_exist_ok=True)
        os.chdir(_temp_path)
        _cmd = ['tar', '-czf', _archive_file_name, _project_dir]
        _rc = run_command(_cmd)
        if _rc != 0:
            raise RuntimeError(f'Konnte Archiv für {project_name} {feature_name} nicht erzeugen')
        _archive_target_path = os.path.join(RPM_WORK_PATH, 'SOURCES')
        shutil.copy(os.path.join(_temp_path, _archive_file_name), _archive_target_path)
    # Steuerdateien kopieren
    if feature_name is None:
        _spec_data_path = os.path.join(PROJECTS_ROOT, project_name, 'build', 'rpm', 'SPECS')
    else:
        _spec_data_path = os.path.join(PROJECTS_ROOT, project_name, 'build', 'featuresets',
                                            feature_name, 'rpm', 'SPECS')
    _spec_target_path = os.path.join(RPM_WORK_PATH, 'SPECS')
    for _f in os.listdir(_spec_data_path):
        copy_spec_file(_spec_data_path, _f, _spec_target_path, project_name, _feature)
    # rpm-Paket erstellen
    _cmd = ['rpmbuild', '-bb', os.path.join(_spec_target_path, f'{_py_package_name}.spec')]
    _rc = run_command(_cmd)
    if _rc != 0:
        raise RuntimeError(f'Build rpm-Paket {project_name} {feature_name} fehlgeschlagen')
    _rpms_path = os.path.join(RPM_WORK_PATH, 'RPMS', 'noarch')
    _dist_path = os.path.join(PROJECTS_ROOT, project_name, 'dist')
    for _f in os.listdir(_rpms_path):
        shutil.copy(os.path.join(_rpms_path, _f), _dist_path)
    print('rpm Installationspaket erstellt.')


# Hauptprogramm
_project = None
_feature_set = None
if len(sys.argv) == 2:
    _project = sys.argv[1]
elif len(sys.argv) == 3:
    _project = sys.argv[1]
    _feature_set = sys.argv[2]
else:
    print('Aufruf: build_py_rpm <Projekt> [<Feature-Umfang>]')
    sys.exit(1)
try:
    _feature_sets = feature_sets(_project)
    if _feature_set == 'all':
        for _fs in _feature_sets:
            build_project_feature(_project, _fs)
    elif _feature_set is not None:
        if _feature_set not in _feature_sets:
            raise RuntimeError(f'Feature-Set {_feature_set} nicht gefunden')
        build_project_feature(_project, _feature_set)
    else:
        if len(_feature_sets) == 0:
            build_project_feature(_project, None)
        elif len(_feature_sets) == 1:
            build_project_feature(_project, _feature_sets[0])
        else:
            raise RuntimeError(f'Feature-Set muss angegeben werden {_feature_sets}')
except RuntimeError as _e:
    print(f'+++ {_e} +++')
    sys.exit(1)
