import sys

# Minimal import-time checks only. Heavyweight runtime checks should live in command handlers.
required_python_major = 3
required_python_minor = 8
if sys.version_info < (required_python_major, required_python_minor):
    raise SystemExit(
        f"ERROR: This program requires Python {required_python_major}.{required_python_minor} or newer. "
        f"Current version: {'.'.join(map(str, sys.version_info[:3]))}"
    )
