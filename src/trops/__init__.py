import sys

if sys.version_info < (3, 8):
    raise SystemExit(
        "ERROR: Ansible requires Python 3.8 or newer on the controller. "
        f"Current version: {''.join(sys.version.splitlines())}"
    )
