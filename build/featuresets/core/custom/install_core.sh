#!/bin/bash

# Installation for user only
INSTALL_PATH=$HOME/apps/restix
LINK_PATH=$HOME/bin

# System wide installation
#INSTALL_PATH=/opt/restix
#LINK_PATH=/usr/local/bin


if [ ! -d $INSTALL_PATH ]; then
  mkdir -p $INSTALL_PATH
fi

WHEEL_FILE=`ls restix_core*whl`
VENV_PATH=$INSTALL_PATH/.venv
if [ ! -d $VENV_PATH ]; then
  python3 -m venv $VENV_PATH
  if [ $? -ne 0 ]; then
    exit 1
  fi
  source $VENV_PATH/bin/activate
  pip3 install ./$WHEEL_FILE
  deactivate
else
  source $VENV_PATH/bin/activate
  pip3 install ./$WHEEL_FILE --upgrade
  deactivate
fi

cat restix | sed -e s:$\{INSTALL_PATH\}:$INSTALL_PATH: > $INSTALL_PATH/restix
chmod 755 $INSTALL_PATH/restix
rm -f $LINK_PATH/restix
ln -s $INSTALL_PATH/restix $LINK_PATH/restix
