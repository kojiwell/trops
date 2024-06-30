#!/bin/bash
#
# release.sh - update files for new release

set -eux

if [ $# -ne 1 ]; then
    echo "Usage: ./release.sh <version>"
fi

sed -i "s/release =.*/release = '$1'/g" docs/conf.py
sed -i "s/    version=.*/    version=\"$1\",/g" setup.py
sed -i "s/__version__ =.*/__version__ = '$1'/g" src/trops/release.py
sed -i "s/^version =.*/version = '$1'/" pyproject.toml

python3 setup.py sdist
python3 setup.py bdist_wheel

echo "Execute the twine upload where you have access to the pypi repository."
echo  > twine upload --repository pypi dist/trops-${1}.tar.gz
