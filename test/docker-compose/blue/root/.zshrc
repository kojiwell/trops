if ! which trops > /dev/null; then
    cd /usr/local/src/trops
    python3 setup.py develop
fi

export TROPS_ROOT="/opt/shared/trops"
if [ -d $TROPS_ROOT ]; then
    eval "$(trops init zsh)"
fi
