from subprocess import Popen, PIPE
import os
import random
import hashlib

from datetime import datetime


def real_path(path):
    """\
    Return the realpath of any of these:
    > ~/path/to/dir
    > $HOME/path/to/dir
    > path/to/dir"""
    if '~' == path[0]:
        return os.path.expanduser(path)
    elif '$' in path:
        new_path = os.path.expandvars(path)
        if '~' == new_path[0]:
            return os.path.expanduser(new_path)
        elif '/' == new_path[0]:
            return os.path.expandvars(path)
        else:
            print(f'{ path } is not a path...')
            exit(1)
    if '/' == path[0]:
        return path
    else:
        return os.path.realpath(path)


def generate_sid(args, other_args):

    now = datetime.now().isoformat()
    print(hashlib.sha256(bytes(now, 'utf-8')).hexdigest()[0:7])


def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False
