import argparse
import os

from .capcmd import add_capture_cmd_subparsers
from .env import add_env_subparsers
from .file import add_file_subparsers
from .init import add_init_subparsers
from .koumyo import add_koumyo_subparsers
from .log import add_log_subparsers
from .release import __version__
from .repo import add_repo_subparsers
from .trops import TropsMain
from .utils import generate_sid
from .view import add_view_subparsers


def trops_git(args, other_args):

    tr = TropsMain(args, other_args)
    tr.git()


def trops_glab(args, other_args):

    tr = TropsMain(args, other_args)
    tr.glab()


def trops_check(args, other_args):

    tr = TropsMain(args, other_args)
    tr.check()


def trops_ll(args, other_args):

    tr = TropsMain(args, other_args)
    tr.ll()


def trops_show(args, other_args):

    tr = TropsMain(args, other_args)
    tr.show()


def trops_branch(args, other_args):

    tr = TropsMain(args, other_args)
    tr.branch()


def trops_fetch(args, other_args):

    tr = TropsMain(args, other_args)
    tr.fetch()


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
    parser_git.add_argument('-v', '--verbose', help='Verbose: print wrapped git command', action='store_true')
    parser_git.set_defaults(handler=trops_git)


def add_glab_subparsers(subparsers):

    parser_glab = subparsers.add_parser('glab', help='glab wrapper')
    parser_glab.add_argument('-e', '--env', help="Set env")
    parser_glab.set_defaults(handler=trops_glab)


def add_show_subparsers(subparsers):

    parser_show = subparsers.add_parser(
        'show', help='trops show commit[:path]')
    parser_show.add_argument('-e', '--env', help="environment name")
    parser_show.add_argument('commit', help='Set commit[:path]')
    parser_show.set_defaults(handler=trops_show)

def add_branch_subparsers(subparsers):

    parser_branch = subparsers.add_parser(
        'branch', help='trops branch')
    parser_branch.set_defaults(handler=trops_branch)


def add_fetch_subparsers(subparsers):

    parser_fetch = subparsers.add_parser(
        'fetch', help='trops fetch')
    parser_fetch.set_defaults(handler=trops_fetch)


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
    parser_touch.add_argument('-v', '--verbose', help='Verbose: print wrapped git command(s)', action='store_true')
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

    # Avoid eval for safety; keep mapping explicit
    add_branch_subparsers(subparsers)
    add_capture_cmd_subparsers(subparsers)
    add_check_subparsers(subparsers)
    add_drop_subparsers(subparsers)
    add_env_subparsers(subparsers)
    add_fetch_subparsers(subparsers)
    add_file_subparsers(subparsers)
    add_gensid_subparsers(subparsers)
    add_git_subparsers(subparsers)
    add_glab_subparsers(subparsers)
    add_init_subparsers(subparsers)
    add_koumyo_subparsers(subparsers)
    add_ll_subparsers(subparsers)
    add_log_subparsers(subparsers)
    add_repo_subparsers(subparsers)
    add_view_subparsers(subparsers)
    add_show_subparsers(subparsers)
    add_touch_subparsers(subparsers)

    # Pass args and other args to the hander
    args, other_args = parser.parse_known_args()
    if hasattr(args, 'handler'):
        args.handler(args, other_args)
    else:
        parser.print_help()
