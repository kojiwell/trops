if ! which trops > /dev/null; then
    cd /usr/local/src/trops
    python3 setup.py develop
fi

export TROPS_ROOT="/opt/local/trops"
if [ -d $TROPS_ROOT ]; then
    eval "$(trops init bash)"
fi
