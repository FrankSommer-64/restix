#!/bin/bash

if [ "$RESTIX_TESTING_ROOT" == "" ]; then
  echo "+++ Umgebungsvariable RESTIX_TESTING_ROOT ist nicht gesetzt +++"
  exit 1
fi

repo_root_path=$RESTIX_TESTING_ROOT/repos
cd $repo_root_path

if [ "$1" == "init" ]; then
  repo_init_root_path=$repo_root_path/init
  rm -rf $repo_init_root_path
  mkdir init
  cd init
  mkdir pw pwfile pgp_pass pgp_token readonly
  chmod 555 readonly
fi

