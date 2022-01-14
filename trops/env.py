import os
import subprocess
from configparser import ConfigParser
from textwrap import dedent

from trops.utils import real_path


class TropsEnv:

    def __init__(self, args, other_args):
        # NOTE: The args.handler cannot pass args to the class,
        # so I use self._setup_vars() instead.

        if hasattr(args, 'dir'):
            self.trops_dir = real_path(args.dir) + '/trops'
        elif 'TROPS_DIR' in os.environ:
            self.trops_dir = os.path.expandvars('$TROPS_DIR')
        else:
            print('TROPS_ENV does not exists')
            exit(1)

        if hasattr(args, 'work_tree'):
            self.trops_work_tree = args.work_tree

        if hasattr(args, 'env'):
            self.trops_env = args.env
            self.trops_bash_rcfile = self.trops_dir + \
                f'/bash_{ self.trops_env }rc'
            self.trops_zsh_rcfile = self.trops_dir + \
                f'/zsh_{ self.trops_env }rc'
            self.trops_git_dir = self.trops_dir + f'/{ self.trops_env }.git'

        self.trops_conf = self.trops_dir + '/trops.cfg'
        self.trops_log_dir = self.trops_dir + '/log'

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
                print(
                    f"The '{ self.trops_env }' environment already exists on { self.trops_conf }")
                exit(1)

        config[self.trops_env] = {'git_dir': f'$TROPS_DIR/{ self.trops_env }.git',
                                  'sudo': 'False',
                                  'work_tree': f'{ self.trops_work_tree }'}
        with open(self.trops_conf, mode='w') as configfile:
            config.write(configfile)

    def _setup_bare_git_repo(self):

        # Create trops's bare git directory
        if not os.path.isdir(self.trops_git_dir):
            cmd = ['git', 'init', '--bare', self.trops_git_dir]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                print(result.stdout.decode('utf-8'))
            else:
                print(result.stderr.decode('utf-8'))
                exit(result.returncode)

        # Prepare for updating trops.git/config
        git_cmd = ['git', '--git-dir=' + self.trops_git_dir]
        git_conf = ConfigParser()
        git_conf.read(self.trops_git_dir + '/config')
        # Set "status.showUntrackedFiles no" locally
        if not git_conf.has_option('status', 'showUntrackedFiles'):
            cmd = git_cmd + ['config', '--local',
                             'status.showUntrackedFiles', 'no']
            subprocess.call(cmd)
        # Set $USER as user.name
        if not git_conf.has_option('user', 'name'):
            username = os.environ['USER']
            cmd = git_cmd + ['config', '--local', 'user.name', username]
            subprocess.call(cmd)
        # Set $USER@$HOSTNAME as user.email
        if not git_conf.has_option('user', 'email'):
            useremail = username + '@' + os.uname().nodename
            cmd = git_cmd + ['config', '--local', 'user.email', useremail]
            subprocess.call(cmd)

        # TODO: branch name should become an option, too
        # Set branch name as trops
        cmd = git_cmd + ['branch', '--show-current']
        branch_name = subprocess.check_output(cmd).decode("utf-8")
        new_branch_name = 'trops_' + self.trops_env
        if new_branch_name not in branch_name:
            cmd = git_cmd + ['--work-tree=/',
                             'checkout', '-b', new_branch_name]
            subprocess.call(cmd)

    def initialize(self):

        self._setup_dirs()
        self._setup_rcfiles()
        self._setup_trops_conf()
        self._setup_bare_git_repo()

    def update(self):

        config = ConfigParser()
        if os.path.isfile(self.trops_conf):
            config.read(self.trops_conf)
            if not config.has_section(self.trops_env):
                print(
                    f"The '{ self.trops_env }' environment does not exists on { self.trops_conf }")
                exit(1)

        config[self.trops_env] = {'git_dir': f'$TROPS_DIR/{ self.trops_env }.git',
                                  'sudo': 'False',
                                  'work_tree': f'{ self.trops_work_tree }'}
        with open(self.trops_conf, mode='w') as configfile:
            config.write(configfile)

    def show(self):

        self.trops_conf = self.trops_dir + '/trops.cfg'

        print('ENV')
        try:
            print(f"  TROPS_DIR = {os.environ['TROPS_DIR']}")
        except KeyError:
            print(f"  {os.environ['TROPS_DIR']} = None")
            exit(1)
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
