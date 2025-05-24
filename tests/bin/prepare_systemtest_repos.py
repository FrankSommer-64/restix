#!/usr/bin/python3

import os
import shutil
import sys


def copy_file(source_path, target_path):
    if source_path.endswith('.toml') or source_path.endswith('.list'):
        with open(source_path, 'r') as _source:
            _contents = _source.read()
            _contents = _contents.replace('${RESTIX_TESTING_ROOT}', os.environ.get('RESTIX_TESTING_ROOT'))
            with open(target_path, 'w') as _target:
              _target.write(_contents)
        return
    shutil.copyfile(source_path, target_path)


def create_repos(parent_path):
    _repos_path = os.path.join(parent_path, 'repos')
    os.mkdir(_repos_path)
    for _repo_dir in ['pw', 'pwfile', 'pgp_pass', 'pgp_token', 'readonly']:
        os.mkdir(os.path.join(_repos_path, _repo_dir))
    os.chmod(os.path.join(_repos_path, 'readonly'), 0o555)


if len(sys.argv) != 2:
    print('Aufruf: prepare_systemtest_data <Komponente>')
    sys.exit(1)
component_to_test = sys.argv[1]

projects_root_path = os.environ.get('SW_PROJECTS_ROOT')
if projects_root_path is None or not os.path.isdir(projects_root_path):
    print('+++ Umgebungsvariable SW_PROJECTS_ROOT ist nicht auf ein Verzeichnis gesetzt +++')
    sys.exit(1)

test_data_root_path = os.path.join(projects_root_path, 'restix', 'tests', 'testdata', 'systemtest')
if not os.path.isdir(test_data_root_path):
    print(f'+++ Testdaten-Verzeichnis {test_data_root_path} nicht gefunden +++')
    sys.exit(1)

testing_root_path = os.environ.get('RESTIX_TESTING_ROOT')
if testing_root_path is None or not os.path.isdir(testing_root_path):
    print('+++ Umgebungsvariable RESTIX_TESTING_ROOT ist nicht auf ein Verzeichnis gesetzt +++')
    sys.exit(1)
systemtest_root_path = os.path.join(testing_root_path, 'systemtest')

if component_to_test == 'init':
    # bei Init müssen keine Benutzerdaten angelegt werden
    shutil.rmtree(systemtest_root_path, ignore_errors=True)
    os.mkdir(systemtest_root_path)
    shutil.copytree(os.path.join(test_data_root_path, 'config'), os.path.join(systemtest_root_path, 'config'), copy_function = copy_file)
    create_repos(systemtest_root_path)
elif component_to_test == 'backup':
    shutil.rmtree(systemtest_root_path)
    os.mkdir(systemtest_root_path)
    shutil.copytree(os.path.join(test_data_root_path, 'config'), os.path.join(systemtest_root_path, 'config'), copy_function = copy_file)
    create_repos(systemtest_root_path)
    shutil.copytree(os.path.join(test_data_root_path, 'userdata'), os.path.join(systemtest_root_path, 'userdata'))
