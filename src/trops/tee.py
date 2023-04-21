import os
import sys

from .trops import Trops

class TropsTee(Trops):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        self.file_path = args.file_path

    def read_output_via_pipe(self):

        return sys.stdin.read()

def trops_tee(args, other_args):

    ti = TropsTee(args, other_args)
    print(ti.read_output_via_pipe())

def add_tee_subparsers(subparsers):

    # trops tee
    parser_tee = subparsers.add_parser('tee', help="Trops Tee")
    parser_tee.add_argument('file_path', help='file path')
    parser_tee.set_defaults(handler=trops_tee)
