import hashlib
import os

from datetime import datetime
from random import randint



def strtobool(value):
    """Converts a string representation of truth to True or False"""
    _MAP = {
        'y': True,
        'yes': True,
        't': True,
        'true': True,
        'on': True,
        '1': True,
        'n': False,
        'no': False,
        'f': False,
        'false': False,
        'off': False,
        '0': False
    }

    try:
        return _MAP[str(value).lower()]
    except KeyError:
        raise ValueError(f'"{value}" is not a valid bool value')

def absolute_path(dir_path: str) -> str:
    """Returns absolute path"""
    if not dir_path:
        raise ValueError("The directory path cannot be None or an empty string.")
    
    try:
        return os.path.abspath(os.path.expanduser(os.path.expandvars(dir_path)))
    except Exception as e:
        raise ValueError(f"Error resolving path: {e}")

def yes_or_no(question):
    """Prompts for a yes/no question and return True for yes and False for no"""
    while True:
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply in ['y', 'yes']:
            return True
        elif reply in ['n', 'no']:
            return False
        else:
            print("Please answer with 'y' or 'n'.")
            exit(1)

def pick_out_repo_name_from_git_remote(git_remote: str) -> str:
    """Extracts the repository name from a git remote URL"""
    # Extract the last part after '/' which includes <repo_name>.git
    repo_with_suffix = git_remote.split('/')[-1]
    # Remove the '.git' suffix to get the repository name
    repo_name = repo_with_suffix[:-4] if repo_with_suffix.endswith('.git') else repo_with_suffix
    return repo_name

def generate_sid(args, other_args):
    """Generate a session ID"""
    s = sid_seed_text()
    # Three and seven are magic numbers
    hlen = 3
    tlen = 4
    n = randint(0, len(s)-hlen)
    now = datetime.now().isoformat()
    head = ''.join(list(s)[n:n+hlen]).lower()
    tail = hashlib.sha256(bytes(now, 'utf-8')).hexdigest()[0:tlen]
    print(head + tail)

def sid_seed_text():
    """Return an alphanumeric seed text used for SID generation.

    Previously named `that`, which was unclear. This function provides
    a deterministic, alphanumeric-only text used to derive the SID prefix.
    """
    s = """Tao Te Ching / Chapter 45
    Great support seems deficient,
    Employed it will not collapse;
    Great buoyancy seems empty,
    Utilized it will not be exhausted.
    Great honesty seems corrupt,
    Great skills seem incompetent,
    Great orations seem inarticulate.
    Movement overcomes coldness,
    Stillness overcomes heat,
    Tranquility makes the world become righteous."""
    # https://en.wikisource.org/wiki/Translation:Tao_Te_Ching
    # Creative Commons Attribution-ShareAlike License

    d = {}
    for c in (65, 97):
        for i in range(26):
            d[chr(i+c)] = chr((i+13) % 26 + c)

    return "".join([d.get(c, c) for c in s if c.isalnum()])
