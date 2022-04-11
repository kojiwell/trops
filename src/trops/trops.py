import distutils.util
import logging
import os
import subprocess
import time
from configparser import ConfigParser
from getpass import getuser
from pathlib import Path
from socket import gethostname
from textwrap import dedent

from trops.utils import real_path


class Trops:
    """Trops Class"""

    def __init__(self, args, other_args):

        # Make args sharable among functions
        self.args = args
        self.other_args = other_args

        # Set username and hostname
        self.username = getuser()
        self.hostname = gethostname().split('.')[0]

        # Set trops_dir
        if os.getenv('TROPS_DIR'):
            self.trops_dir = real_path(os.getenv('TROPS_DIR'))
        else:
            print("TROPS_DIR has not been set")
            exit(1)

        # Create the log directory
        self.trops_log_dir = self.trops_dir + '/log'
        self.trops_logfile = self.trops_log_dir + '/trops.log'
        os.makedirs(self.trops_log_dir, exist_ok=True)

        # Set trops_env
        if hasattr(args, 'env') and args.env:
            self.trops_env = args.env
        elif os.getenv('TROPS_ENV'):
            self.trops_env = os.getenv('TROPS_ENV')
        else:
            self.trops_env = False

        # Set trops_sid
        if os.getenv('TROPS_SID'):
            self.trops_sid = os.getenv('TROPS_SID')
        else:
            self.trops_sid = False

        self.config = ConfigParser()
        self.conf_file = self.trops_dir + '/trops.cfg'
        if os.path.isfile(self.conf_file):
            self.config.read(self.conf_file)

            if self.config.has_section(self.trops_env):
                try:
                    self.git_dir = real_path(
                        self.config[self.trops_env]['git_dir'])
                except KeyError:
                    print('git_dir does not exist in your configuration file')
                    exit(1)
                try:
                    self.work_tree = real_path(
                        self.config[self.trops_env]['work_tree'])
                except KeyError:
                    print('work_tree does not exist in your configuration file')
                    exit(1)

                self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                                '--work-tree=' + self.work_tree]

                try:
                    self.sudo = distutils.util.strtobool(
                        self.config[self.trops_env]['sudo'])
                    if self.sudo:
                        self.git_cmd = ['sudo'] + self.git_cmd
                except KeyError:
                    pass

                if 'logfile' in self.config[self.trops_env]:
                    self.trops_logfile = real_path(
                        self.config[self.trops_env]['logfile'])

                if 'ignore_cmds' in self.config[self.trops_env]:
                    self.ignore_cmds = self.config[self.trops_env]['ignore_cmds'].split(
                        ',')
                else:
                    self.ignore_cmds = False

                if 'git_remote' in self.config[self.trops_env]:
                    self.git_remote = self.config[self.trops_env]['git_remote']

                if os.getenv('TROPS_TAGS'):
                    self.trops_tags = os.getenv('TROPS_TAGS')
                elif 'tags' in self.config[self.trops_env]:
                    self.trops_tags = self.config[self.trops_env]['tags'].replace(
                        ' ', '')
                else:
                    self.trops_tags = False

        if self.trops_logfile:
            logging.basicConfig(format=f'%(asctime)s { self.username }@{ self.hostname } %(levelname)s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S',
                                filename=self.trops_logfile,
                                level=logging.DEBUG)
            self.logger = logging.getLogger()


class TropsMain(Trops):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

    def git(self):
        """Git wrapper command"""

        cmd = self.git_cmd + self.other_args
        subprocess.call(cmd)

    def check(self):
        """Git status wrapper command"""

        cmd = self.git_cmd + ['status']
        subprocess.call(cmd)

    def ll(self):
        """Shows the list of git-tracked files"""

        dirs = self.args.dirs
        for dir in dirs:
            if os.path.isdir(dir):
                os.chdir(dir)
                cmd = self.git_cmd + ['ls-files']
                output = subprocess.check_output(cmd)
                for f in output.decode("utf-8").splitlines():
                    cmd = ['ls', '-al', f]
                    subprocess.call(cmd)

    def show(self):
        """trops show hash[:path]"""

        cmd = self.git_cmd + ['show', self.args.commit]
        subprocess.call(cmd)

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

    def touch(self):

        for file_path in self.args.paths:

            self._touch_file(file_path)

    def _touch_file(self, file_path):
        """Add a file or directory in the git repo"""

        file_path = real_path(file_path)

        # Check if the path exists
        if not os.path.exists(file_path):
            print(f"{ file_path } doesn't exists")
            exit(1)
        # TODO: Allow touch directory later
        if not os.path.isfile(file_path):
            message = f"""\
                Error: { file_path } is not a file
                Only file is allowed to be touched"""
            print(dedent(message))
            exit(1)

        # Check if the path is in the git repo
        cmd = self.git_cmd + ['ls-files', file_path]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(result.stderr.decode('utf-8'))
            exit(result.returncode)
        output = result.stdout.decode('utf-8')
        # Set the message based on the output
        if output:
            git_msg = f"Update { file_path }"
            log_note = "UPDATE"
        else:
            git_msg = f"Add { file_path }"
            log_note = "ADD"
        if self.trops_tags:
            git_msg = f"{ git_msg } ({ self.trops_tags })"
        # Add and commit
        cmd = self.git_cmd + ['add', file_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m', git_msg, file_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['log', '--oneline', '-1', file_path]
        output = subprocess.check_output(
            cmd).decode("utf-8").split()
        if file_path in output:
            env = self.trops_env
            commit = output[0]
            path = real_path(file_path).lstrip(self.work_tree)
            mode = oct(os.stat(file_path).st_mode)[-4:]
            owner = Path(file_path).owner()
            group = Path(file_path).group()
            message = f"FL trops show -e { env } { commit }:{ path }  #> { log_note } O={ owner },G={ group },M={ mode }"
            if self.trops_sid:
                message = message + f" TROPS_SID={ self.trops_sid }"
            message = message + f" TROPS_ENV={ env }"
            self.logger.info(message)

    def drop(self):

        for file_path in self.args.paths:

            self._drop_file(file_path)

    def _drop_file(self, file_path):
        """Remove a file from the git repo"""

        file_path = real_path(file_path)

        # Check if the path exists
        if not os.path.exists(file_path):
            print(f"{ file_path } doesn't exists")
            exit(1)
        # TODO: Allow touch directory later
        if not os.path.isfile(file_path):
            message = f"""\
                Error: { file_path } is not a file.
                A directory is not allowed to say goodbye"""
            print(dedent(message))
            exit(1)

        # Check if the path is in the git repo
        cmd = self.git_cmd + ['ls-files', file_path]
        output = subprocess.check_output(cmd).decode("utf-8")
        # Set the message based on the output
        if output:
            cmd = self.git_cmd + ['rm', '--cached', file_path]
            subprocess.call(cmd)
            git_msg = f"Goodbye { file_path }"
            if self.trops_tags:
                git_msg = f"{ git_msg } ({ self.trops_tags })"
            cmd = self.git_cmd + ['commit', '-m', git_msg]
            subprocess.call(cmd)
        else:
            message = f"{ file_path } is not in the git repo"
            exit(1)
        cmd = self.git_cmd + ['log', '--oneline', '-1', file_path]
        output = subprocess.check_output(
            cmd).decode("utf-8").split()
        message = f"FL trops show -e { self.trops_env } { output[0] }:{ real_path(file_path).lstrip('/')}  #> BYE BYE"
        if self.trops_sid:
            message = message + f" TROPS_SID={ self.trops_sid }"
        message = message + f" TROPS_ENV={ self.trops_env }"
        self.logger.info(message)
