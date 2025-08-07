# Trops

Trops is a command-line tool designed for tracking system operations on destributed Linux systems. It keeps a log of executed commands and modified files, being helpful for developing Ansible roles, Dockerfiles, and similar tasks. It is portable and easy to use, and it can be used in a variety of environments, such as local, remote, and containerized environments. You can store your log on a private, internal Git repository (not public) and link it to issues in tools such as GitLab and Redmine.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`

## Project Structure

```
.
├── README.md
├── requirements.txt
├── setup.py
├── src/
│   └── trops/
│       ├── __init__.py
│       ├── main.py
│       └── capcmd.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
└── venv/
``` 