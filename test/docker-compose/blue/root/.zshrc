if ! which trops > /dev/null; then
    cd /usr/local/src/trops
    python3 setup.py develop
fi

export TROPS_DIR="/opt/shared/trops"
test -d $TROPS_DIR || mkdir $TROPS_DIR
eval "$(trops init zsh)"