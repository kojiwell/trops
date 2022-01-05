from subprocess import Popen, PIPE
import os


def run(cmd):
    """Execute a command and return returncode, stdout, and stderr"""
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    rc = proc.returncode
    stdout, stderr = proc.communicate()

    return rc, stdout, stderr


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
