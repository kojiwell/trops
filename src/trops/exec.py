import argparse
import os
import sys

from .release import __version__
from .trops import TropsCLI, TropsError
from .utils import generate_sid


# Lazy importers for subcommands defined in other modules. Only the module
# matching the invoked subcommand gets imported, which keeps the hot-path
# (e.g., ``trops capture-cmd`` from the shell prompt hook) from paying the
# cost of importing ``view``, ``tldr``, ``tablog``, etc.
def _lazy_capture_cmd_subparsers(subparsers):
    from .capcmd import add_capture_cmd_subparsers
    add_capture_cmd_subparsers(subparsers)


def _lazy_env_subparsers(subparsers):
    from .env import add_env_subparsers
    add_env_subparsers(subparsers)


def _lazy_file_subparsers(subparsers):
    from .file import add_file_subparsers
    add_file_subparsers(subparsers)


def _lazy_init_subparsers(subparsers):
    from .init import add_init_subparsers
    add_init_subparsers(subparsers)


def _lazy_tldr_subparsers(subparsers):
    from .tldr import add_tldr_subparsers
    add_tldr_subparsers(subparsers)


def _lazy_log_subparsers(subparsers):
    from .log import add_log_subparsers
    add_log_subparsers(subparsers)


def _lazy_repo_subparsers(subparsers):
    from .repo import add_repo_subparsers
    add_repo_subparsers(subparsers)


def _lazy_view_subparsers(subparsers):
    from .view import add_view_subparsers
    add_view_subparsers(subparsers)


def _lazy_tablog_subparsers(subparsers):
    from .tablog import add_tablog_subparsers
    add_tablog_subparsers(subparsers)


def _cli_handler(method_name):
    """Return an argparse handler that dispatches to TropsCLI.<method_name>."""

    def handler(args, other_args):
        getattr(TropsCLI(args, other_args), method_name)()

    return handler


def add_git_subparsers(subparsers):

    parser_git = subparsers.add_parser('git', help='git wrapper')
    parser_git.add_argument('-s', '--sudo', help="Use sudo",
                            action='store_true')
    parser_git.add_argument('-e', '--env', help="Set env")
    parser_git.add_argument('-v', '--verbose', help='Verbose: print wrapped git command', action='store_true')
    parser_git.set_defaults(handler=_cli_handler('git'))


 


def add_show_subparsers(subparsers):

    parser_show = subparsers.add_parser(
        'show', help='trops show commit[:path]')
    parser_show.add_argument('-e', '--env', help="environment name")
    parser_show.add_argument('commit', help='Set commit[:path]')
    parser_show.set_defaults(handler=_cli_handler('show'))

def add_branch_subparsers(subparsers):

    parser_branch = subparsers.add_parser(
        'branch', help='trops branch')
    parser_branch.set_defaults(handler=_cli_handler('branch'))


def add_fetch_subparsers(subparsers):

    parser_fetch = subparsers.add_parser(
        'fetch', help='trops fetch')
    parser_fetch.set_defaults(handler=_cli_handler('fetch'))


def add_ll_subparsers(subparsers):

    parser_ll = subparsers.add_parser('ll', help="list files")
    parser_ll.add_argument(
        'dirs', help='directory path', nargs='*', default=[os.getcwd()])
    parser_ll.add_argument(
        '-e', '--env', help='Set environment name')
    parser_ll.set_defaults(handler=_cli_handler('ll'))


def add_touch_subparsers(subparsers):

    parser_touch = subparsers.add_parser(
        'touch', help="add/update file in the git repo")
    parser_touch.add_argument('paths', nargs='+', help='path of file')
    parser_touch.add_argument('-v', '--verbose', help='Verbose: print wrapped git command(s)', action='store_true')
    parser_touch.set_defaults(handler=_cli_handler('touch'))


def add_drop_subparsers(subparsers):

    parser_drop = subparsers.add_parser(
        'drop', help="remove file from the git repo")
    parser_drop.add_argument('paths', nargs='+', help='path of file')
    parser_drop.set_defaults(handler=_cli_handler('drop'))


def add_gensid_subparsers(subparsers):

    parser_gensid = subparsers.add_parser(
        'gensid', help='generate sid')
    parser_gensid.set_defaults(handler=generate_sid)


def add_check_subparsers(subparsers):

    parser_check = subparsers.add_parser('check', help='check status')
    parser_check.add_argument('-s', '--sudo', help="Use sudo",
                              action='store_true')
    parser_check.add_argument('-e', '--env', help="Set env")
    parser_check.set_defaults(handler=_cli_handler('check'))


_SUBCOMMAND_REGISTRARS = {
    'branch': add_branch_subparsers,
    'capture-cmd': _lazy_capture_cmd_subparsers,
    'check': add_check_subparsers,
    'drop': add_drop_subparsers,
    'env': _lazy_env_subparsers,
    'fetch': add_fetch_subparsers,
    'file': _lazy_file_subparsers,
    'gensid': add_gensid_subparsers,
    'git': add_git_subparsers,
    'init': _lazy_init_subparsers,
    'tldr': _lazy_tldr_subparsers,
    'll': add_ll_subparsers,
    'log': _lazy_log_subparsers,
    'tablog': _lazy_tablog_subparsers,
    'repo': _lazy_repo_subparsers,
    'view': _lazy_view_subparsers,
    'show': add_show_subparsers,
    'touch': add_touch_subparsers,
}


def _detect_subcommand(argv):
    """Return the subcommand name from argv if uniquely identifiable, else None.

    The first non-flag argument that matches a known subcommand wins. If the
    first non-flag argument is unknown, returns None so that ``main`` falls
    back to registering every subparser (so help / unknown-command errors
    list all subcommands).
    """
    for arg in argv[1:]:
        if arg.startswith('-'):
            continue
        if arg in _SUBCOMMAND_REGISTRARS:
            return arg
        return None
    return None


def main():

    parser = argparse.ArgumentParser(prog='trops',
                                     description='Trops - Tracking Operations')
    subparsers = parser.add_subparsers()
    parser.add_argument('-v', '--version', action='version',
                        version=f'%(prog)s {__version__}')

    cmd = _detect_subcommand(sys.argv)
    if cmd is not None:
        # Hot path: register only the matched subcommand. This avoids
        # importing modules unrelated to the chosen subcommand.
        _SUBCOMMAND_REGISTRARS[cmd](subparsers)
    else:
        # No detectable subcommand (help, --version, unknown). Register all
        # so that ``trops --help`` lists every available subcommand.
        for registrar in _SUBCOMMAND_REGISTRARS.values():
            registrar(subparsers)

    # Pass args and other args to the hander
    args, other_args = parser.parse_known_args()
    try:
        if hasattr(args, 'handler'):
            args.handler(args, other_args)
        else:
            parser.print_help()
    except TropsError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(1)
