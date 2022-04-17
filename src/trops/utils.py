import hashlib
import os

from datetime import datetime


def absolute_path(dir_path):
    return os.path.expanduser(os.path.expandvars(dir_path))


def generate_sid(args, other_args):

    now = datetime.now().isoformat()
    print(hashlib.sha256(bytes(now, 'utf-8')).hexdigest()[0:7])


def yes_or_no(question):
    while True:
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply in ['y', 'yes']:
            return True
        if reply in ['n', 'no']:
            return False
