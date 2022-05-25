import os
import time

from configparser import ConfigParser
from textwrap import dedent

from .trops import Trops

class TropsLog(Trops):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

    def _follow(self, file):

        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def log(self):
        """Print trops log"""

        log_file = self.trops_logfile
        numlines = 15

        # -t/--tail <num>
        if self.args.tail:
            numlines = self.args.tail

        # -a/--all
        if self.args.all:
            with open(log_file) as ff:
                for line in ff.readlines():
                    print(line, end='')
        else:
            with open(log_file) as ff:
                for line in ff.readlines()[-numlines:]:
                    print(line, end='')

        if self.args.follow:
            ff = open(log_file, "r")
            try:
                lines = self._follow(ff)
                for line in lines:
                    print(line, end='')
            except KeyboardInterrupt:
                print('\nClosing trops log...')


def trops_log(args, other_args):

    trlog = TropsLog(args, other_args)
    trlog.log()


def add_log_subparsers(subparsers):

    parser_log = subparsers.add_parser('log', help='show log')
    parser_log.add_argument(
        '-t', '--tail', type=int, help='set number of lines to show')
    parser_log.add_argument(
        '-f', '--follow', action='store_true', help='follow log interactively')
    parser_log.add_argument(
        '-a', '--all', action='store_true', help='show all log')
    parser_log.set_defaults(handler=trops_log)
