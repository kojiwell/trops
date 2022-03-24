from subprocess import Popen, PIPE
import os
import random

from trops.namesgenerator import get_random_name


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


def random_word(args, other_args):

    try:
        with open('/usr/share/dict/words') as f:
            word_list = f.read().split()
        words = random.sample(word_list, args.number)
        for i in range(len(words)):
            words[i] = ''.join(e for e in words[i] if e.isalnum()).lower()
        print('_'.join(words))
    except FileNotFoundError:
        cmd = ['shuf', '-i', '1-100000', '-n', '1']
        subprocess.call(cmd)


def random_name(args, other_args):

    print(get_random_name())
