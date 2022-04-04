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
        return os.path.expandvars(path)
    if '/' == path[0]:
        return path
    else:
        return os.path.realpath(path)


def generate_sid(args, other_args):

    now = datetime.now().isoformat()
    print(hashlib.sha256(bytes(now, 'utf-8')).hexdigest()[0:7])
