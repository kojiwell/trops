# Trops

Trops is a command line tool that allows 

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
├── src/
│   └── trops/
│       ├── __init__.py
│       └── main.py
└── tests/
    ├── __init__.py
    └── test_main.py
``` 