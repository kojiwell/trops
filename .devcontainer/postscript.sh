#!/bin/bash

if ! which poetry >/dev/null ; then
    poetry update && poetry install
fi

if ! which trops >/dev/null ; then
    sudo python3 setup.py develop
fi

export TROPS_DIR=$HOME/trops
export USER=devuser
test -d $TROPS_DIR || mkdir $TROPS_DIR
eval "$(trops init bash)"

test -d $TROPS_DIR/repo/devenv.git || trops env create devenv
test -L $TROPS_DIR/activate_trops || ln -s /workspaces/trops/.devcontainer/postscript.sh $TROPS_DIR/activate_trops 
ontrops devenv
