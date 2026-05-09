#!/bin/bash
#
# release.sh - bump version, build distributions, print release commands.
#
# Usage:
#   ./release.sh <version>
#
# <version> is bare semver, e.g. 0.2.36 (no leading 'v'). The 'v' prefix is
# added when creating the git tag in the printed next-steps.

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: ./release.sh <version>" >&2
    echo "  e.g., ./release.sh 0.2.36" >&2
    exit 1
fi

VERSION="$1"

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$ ]]; then
    echo "ERROR: '$VERSION' does not look like a valid version (expected X.Y.Z)" >&2
    exit 1
fi

# Pre-flight: working tree must be clean so the version-bump diff is reviewable.
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: working tree is not clean. Commit or stash changes first." >&2
    git status --short >&2
    exit 1
fi

# Portable in-place sed: BSD and GNU both accept -i.bak, then we delete the backup.
inplace_sed() {
    local pattern="$1"
    local file="$2"
    sed -i.bak "$pattern" "$file"
    rm "$file.bak"
}

inplace_sed "s/^release = .*/release = '$VERSION'/g" docs/conf.py
inplace_sed "s/^    version=.*/    version=\"$VERSION\",/g" setup.py
inplace_sed "s/^__version__ = .*/__version__ = '$VERSION'/g" src/trops/release.py
inplace_sed "s/^version = .*/version = '$VERSION'/" pyproject.toml

echo
echo "Version bumped to $VERSION in:"
echo "  - docs/conf.py"
echo "  - setup.py"
echo "  - src/trops/release.py"
echo "  - pyproject.toml"
echo

rm -rf dist
# Prefer Poetry build if available; fall back to PEP 517 build, then setup.py.
if command -v poetry >/dev/null 2>&1; then
    poetry build
elif python3 -m build --version >/dev/null 2>&1; then
    python3 -m build
else
    python3 setup.py sdist bdist_wheel
fi

echo
echo "Built dist:"
ls -1 dist/

cat <<EOF

Next steps (run manually after reviewing the diff):
  1. Update CHANGELOG.rst: rename 'Unreleased' to 'v$VERSION - $(date +%Y-%m-%d)'
     and add a fresh empty 'Unreleased' section above it.
  2. Review:    git diff
  3. Commit:    git commit -am "chore: update changelog and version to v$VERSION"
  4. Tag:       git tag -a v$VERSION -m "Release v$VERSION"
  5. Push:      git push origin develop --follow-tags
  6. Verify:    twine check dist/*
  7. Upload:    twine upload --repository pypi dist/*
EOF
