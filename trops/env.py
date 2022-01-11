import os
from configparser import ConfigParser
from textwrap import dedent

from trops.utils import real_path


class TropsEnv:

    def __init__(self):
        # NOTE: The args.handler cannot pass args to the class,
        # so I use self._setup_vars() instead.
        pass

    def _setup_initial_trops_dir(self, args):

        if args.dir:
            self.trops_dir = real_path(args.dir) + '/trops'
        elif 'TROPS_DIR' in os.environ:
            self.trops_dir = os.path.expandvars('$TROPS_DIR') + '/trops'
        else:
            self.trops_dir = os.path.expandvars('$HOME') + '/.trops'

    def _read_env_trops_dir(self):

        if 'TROPS_DIR' in os.environ:
            self.trops_dir = os.path.expandvars('$TROPS_DIR')
        else:
            print('TROPS_ENV does not exists')
            exit(1)

    def _setup_vars(self, args):

        self.trops_conf = self.trops_dir + '/trops.cfg'
        self.trops_log_dir = self.trops_dir + '/log'
        self.trops_work_tree = args.work_tree
        self.trops_env = args.env
        self.trops_bash_rcfile = self.trops_dir + f'/bash_{ self.trops_env }rc'
        self.trops_zsh_rcfile = self.trops_dir + f'/zsh_{ self.trops_env }rc'
        self.trops_git_dir = self.trops_dir + f'/{ self.trops_env }.git'

    def _setup_dirs(self):

        # Create trops_dir
        try:
            os.mkdir(self.trops_dir)
        except FileExistsError:
            print(f"{ self.trops_dir } already exists")

        # Create trops_dir/log
        try:
            os.mkdir(self.trops_log_dir)
        except FileExistsError:
            print(f'{ self.trops_log_dir} already exists')

    def _setup_rcfiles(self):

        # Create bash rcfile
        if not os.path.isfile(self.trops_bash_rcfile):
            with open(self.trops_bash_rcfile, mode='w') as rcfile:
                lines = f"""\
                    export TROPS_DIR=$(dirname $(realpath $BASH_SOURCE))
                    export TROPS_SID=$(trops random-name)
                    export TROPS_ENV={ self.trops_env }

                    PROMPT_COMMAND='trops capture-cmd 1 $? $(history 1)'

                    alias trgit="trops git"
                    """
                rcfile.write(dedent(lines))
        # TODO: TROPS_ENV should be optional, which is not needed by default

        # Create zsh rcfile
        if not os.path.isfile(self.trops_zsh_rcfile):
            with open(self.trops_zsh_rcfile, mode='w') as rcfile:
                lines = f"""\
                    export TROPS_DIR=$(dirname $(realpath ${{(%):-%N}}))
                    export TROPS_SID=$(trops random-name)
                    export TROPS_ENV={ self.trops_env }

                    precmd() {{
                        trops capture-cmd 1 $? $(history|tail -1)
                    }}

                    alias trgit="trops git"
                    """
                rcfile.write(dedent(lines))
        # TODO: TROPS_ENV should be optional, which is not needed by default

    def _setup_trops_conf(self):

        config = ConfigParser()
        if os.path.isfile(self.trops_conf):
            config.read(self.trops_conf)
            if config.has_section(self.trops_env):
                print(f"The '{ self.trops_env }' environment already exists")
                exit(1)

        config[self.trops_env] = {'git_dir': f'$TROPS_DIR/{ self.trops_env }.git',
                                  'sudo': 'False',
                                  'work_tree': f'{ self.trops_work_tree }'}
        with open(self.trops_conf, mode='w') as configfile:
            config.write(configfile)

    def run(self, args, other_args):

        self._setup_initial_trops_dir(args)
        self._setup_vars(args)
        self._setup_dirs()
        self._setup_rcfiles()
        self._setup_trops_conf()
        print(f'trops_dir = { self.trops_dir }')

    def show(self, args, other_args):

        self._read_env_trops_dir()
        self.trops_conf = self.trops_dir + '/trops.cfg'

        print('ENV')
        print(f"  TROPS_DIR = {os.environ['TROPS_DIR']}")
        try:
            print(f"  TROPS_ENV = {os.environ['TROPS_ENV']}")
            trops_env = os.environ['TROPS_ENV']
        except KeyError:
            print('  TROPS_ENV = None')
            trops_env = 'default'
        print(f"  TROPS_SID = {os.environ['TROPS_SID']}")

        config = ConfigParser()
        config.read(self.trops_conf)
        print('Git')
        print(f"  git-dir = { config.get(trops_env, 'git_dir') }")
        print(f"  work-tree = { config.get(trops_env, 'work_tree') }")
