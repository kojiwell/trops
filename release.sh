#!/bin/bash
#
# release.sh - update files for new release

set -eux

if [ $# -ne 1 ]; then
    echo "Usage: ./release.sh <version>"
fi

#sed -i "s/release =.*/release = '$1'/g" docs/conf.py
#sed -i "s/    version=.*/    version=\"$1\",/g" setup.py
#sed -i "s/__version__ =.*/__version__ = '$1'/g" src/trops/release.py
#sed -i "s/^version =.*/version = '$1'/" pyproject.toml

rm -rf dist
# Prefer Poetry build if available; fall back to PEP 517 build, then setup.py
if command -v poetry >/dev/null 2>&1; then
  poetry build
elif python3 -m build --version >/dev/null 2>&1; then
  python3 -m build
else
  python3 setup.py sdist bdist_wheel
fi

echo "Now verify and upload to PyPI (from an environment with creds):"
echo "  twine check dist/*"
echo "  twine upload --repository pypi dist/*"
