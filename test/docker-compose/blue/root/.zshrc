if ! which trops > /dev/null; then
    cd /usr/local/src/trops
    python3 setup.py develop
fi

if [ -f /opt/shared/trops/bluerc ]; then
    . /opt/shared/trops/bluerc
fi