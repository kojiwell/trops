import argparse
import os

from .capcmd import add_capture_cmd_subparsers
from .env import add_env_subparsers
from .file import add_file_subparsers
from .init import add_init_subparsers
from .koumyo import add_koumyo_subparsers
from .release import __version__
from .repo import add_repo_subparsers
from .trops import TropsMain
from .utils import generate_sid


def trops_git(args, other_args):

    tr = TropsMain(args, other_args)
    tr.git()


def trops_check(args, other_args):

    tr = TropsMain(args, other_args)
    tr.check()


def trops_ll(args, other_args):

    tr = TropsMain(args, other_args)
    tr.ll()


def trops_show(args, other_args):

    tr = TropsMain(args, other_args)
    tr.show()


def trops_log(args, other_args):

    tr = TropsMain(args, other_args)
    tr.log()


def trops_touch(args, other_args):

    tr = TropsMain(args, other_args)
    tr.touch()


def trops_drop(args, other_args):

    tr = TropsMain(args, other_args)
    tr.drop()


def add_git_subparsers(subparsers):

    parser_git = subparsers.add_parser('git', help='git wrapper')
    parser_git.add_argument('-s', '--sudo', help="Use sudo",
                            action='store_true')
    parser_git.add_argument('-e', '--env', help="Set env")
    parser_git.set_defaults(handler=trops_git)


def add_show_subparsers(subparsers):

    parser_show = subparsers.add_parser(
        'show', help='trops show commit[:path]')
    parser_show.add_argument('-e', '--env', help="environment name")
    parser_show.add_argument('commit', help='Set commit[:path]')
    parser_show.set_defaults(handler=trops_show)


def add_log_subparsers(subparsers):

    parser_log = subparsers.add_parser('log', help='show log')
    parser_log.add_argument(
        '-t', '--tail', type=int, help='set number of lines to show')
    parser_log.add_argument(
        '-f', '--follow', action='store_true', help='follow log interactively')
    parser_log.add_argument(
        '-a', '--all', action='store_true', help='show all log')
    parser_log.set_defaults(handler=trops_log)


def add_ll_subparsers(subparsers):

    parser_ll = subparsers.add_parser('ll', help="list files")
    parser_ll.add_argument(
        'dirs', help='directory path', nargs='*', default=[os.getcwd()])
    parser_ll.add_argument(
        '-e', '--env', help='Set environment name')
    parser_ll.set_defaults(handler=trops_ll)


def add_touch_subparsers(subparsers):

    parser_touch = subparsers.add_parser(
        'touch', help="add/update file in the git repo")
    parser_touch.add_argument('paths', nargs='+', help='path of file')
    parser_touch.set_defaults(handler=trops_touch)


def add_drop_subparsers(subparsers):

    parser_drop = subparsers.add_parser(
        'drop', help="remove file from the git repo")
    parser_drop.add_argument('paths', nargs='+', help='path of file')
    parser_drop.set_defaults(handler=trops_drop)


def add_gensid_subparsers(subparsers):

    parser_gensid = subparsers.add_parser(
        'gensid', help='generate sid')
    parser_gensid.set_defaults(handler=generate_sid)


def add_check_subparsers(subparsers):

    parser_check = subparsers.add_parser('check', help='check status')
    parser_check.add_argument('-s', '--sudo', help="Use sudo",
                              action='store_true')
    parser_check.add_argument('-e', '--env', help="Set env")
    parser_check.set_defaults(handler=trops_check)


def main():

    parser = argparse.ArgumentParser(prog='trops',
                                     description='Trops - Tracking Operations')
    subparsers = parser.add_subparsers()
    parser.add_argument('-v', '--version', action='version',
                        version=f'%(prog)s {__version__}')

    for func in [
        'init',
        'env',
        'file',
        'koumyo',
        'repo',
        'git',
        'show',
        'capture_cmd',
        'log',
        'll',
        'touch',
        'drop',
        'gensid',
        'check'
    ]:
        eval(f'add_{ func }_subparsers(subparsers)')

    # Pass args and other args to the hander
    args, other_args = parser.parse_known_args()
    if hasattr(args, 'handler'):
        args.handler(args, other_args)
    else:
        parser.print_help()
