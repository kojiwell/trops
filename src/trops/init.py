import os
from configparser import ConfigParser

from trops.utils import real_path


class TropsInit:

    def __init__(self, args, other_args):

        self.args = args

        if self.args.shell not in ['bash', 'zsh']:
            print("# usage: trops init [bash/zsh]")
            exit(1)

        if os.getenv('TROPS_ROOT'):
            self.trops_root = real_path(os.getenv('TROPS_ROOT'))
        else:
            self.trops_root = real_path('$HOME/.trops')

        self.trops_conf = self.trops_root + '/trops.cfg'
        self.trops_log_dir = self.trops_root + '/log'

        self.config = ConfigParser()
        if os.path.isfile(self.trops_conf):
            self.config.read(self.trops_conf)

            try:
                self.trops_env = self.config['default_vars']['environment']
            except KeyError:
                print(
                    '# Set environment in the [default_vars] of your trops.cfg')
                exit(1)

    def run(self):

        print(
            f"source { self.trops_root }/activate_{self.trops_env }.{ self.args.shell }")


def trops_init(args, other_args):

    ti = TropsInit(args, other_args)
    ti.run()


def add_init_subparsers(subparsers):

    # trops init
    parser_init = subparsers.add_parser('init', help="Initialize Trops")
    parser_init.add_argument('shell', help='shell [bash/zsh]')
    parser_init.set_defaults(handler=trops_init)
