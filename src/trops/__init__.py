import os
import sys

from .utils import yes_or_no

# Check Python version
required_python_version = (3, 8)
if sys.version_info < required_python_version:
    raise SystemExit(
        f"ERROR: This program requires Python {required_python_version[0]}.{required_python_version[1]} or newer. "
        f"Current version: {'.'.join(map(str, sys.version_info[:3]))}"
    )

# Ensure TROPS_DIR environment variable is set
trops_dir = os.getenv('TROPS_DIR')
if not trops_dir:
    raise SystemExit('ERROR: The TROPS_DIR environment variable has not been set.')

# Resolve any environment variables and user symbols in TROPS_DIR path
trops_dir_expanded = os.path.expanduser(os.path.expandvars(trops_dir))

# Check if TROPS_DIR is an existing directory
if not os.path.isdir(trops_dir_expanded):
    try:
        os.makedirs(trops_dir_expanded)
    except Exception as e:
        raise SystemExit(f"ERROR: Unable to create {trops_dir}: {e}")
