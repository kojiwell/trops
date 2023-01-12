import os

from .trops import Trops

class TropsTee(Trops):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

    def hello_world(self):

        return "Hello world!"

def trops_tee(args, other_args):

    ti = TropsTee(args, other_args)
    ti.hello_world()

def add_tee_subparsers(subparsers):

    # trops tee
    parser_tee = subparsers.add_parser('tee', help="Trops Tee")
    parser_tee.add_argument('shell', help='shell [bash/zsh]')
    parser_tee.set_defaults(handler=trops_tee)
