import os
import sys
import subprocess
import time
import argparse
import logging
import distutils.util
from configparser import ConfigParser
from textwrap import dedent
from pathlib import Path
from getpass import getuser
from socket import gethostname

from trops.utils import real_path, random_name, generate_sid
from trops.env import add_env_subparsers
from trops.file import add_file_subparsers
from trops.repo import add_repo_subparsers
from trops.capcmd import capture_cmd_subparsers
from trops.koumyo import koumyo_subparsers
from trops.init import add_init_subparsers
from trops.release import __version__


class Trops:
    """Trops Class"""

    def __init__(self):

        # Set username and hostname
        self.username = getuser()
        self.hostname = gethostname().split('.')[0]

        # Set trops_dir
        if os.getenv('TROPS_DIR'):
            self.trops_dir = os.path.expandvars('$TROPS_DIR')
        else:
            self.trops_dir = False

        # Set trops_sid
        if os.getenv('TROPS_SID'):
            self.trops_sid = os.path.expandvars('$TROPS_SID')
        else:
            self.trops_sid = False

        if os.getenv('TROPS_TAGS'):
            self.trops_tags = os.path.expandvars('$TROPS_TAGS')
        else:
            self.trops_tags = False

        # Set trops_env
        if os.getenv('TROPS_ENV'):
            self.trops_env = os.getenv('TROPS_ENV')
        else:
            self.trops_env = self.hostname

        self.config = ConfigParser()
        if self.trops_dir:
            self.conf_file = self.trops_dir + '/trops.cfg'
            if os.path.isfile(self.conf_file):
                self.config.read(self.conf_file)

                if self.config.has_section(self.trops_env):
                    try:
                        self.git_dir = os.path.expandvars(
                            self.config[self.trops_env]['git_dir'])
                    except KeyError:
                        print('git_dir does not exist in your configuration file')
                        exit(1)
                    try:
                        self.work_tree = os.path.expandvars(
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

            os.makedirs(self.trops_dir + '/log', exist_ok=True)
            self.trops_logfile = self.trops_dir + '/log/trops.log'

            logging.basicConfig(format=f'%(asctime)s { self.username }@{ self.hostname } %(levelname)s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S',
                                filename=self.trops_logfile,
                                level=logging.DEBUG)
            self.logger = logging.getLogger()

    def git(self, args, other_args):
        """Git wrapper command"""

        if hasattr(args, 'env') and args.env:
            self.trops_env = args.env
            self.git_dir = os.path.expandvars(
                self.config[self.trops_env]['git_dir'])
            self.work_tree = os.path.expandvars(
                self.config[self.trops_env]['work_tree'])
            self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                            '--work-tree=' + self.work_tree]

        cmd = self.git_cmd + other_args
        subprocess.call(cmd)

    def show(self, args, other_args):
        """trops show hash[:path]"""

        if hasattr(args, 'env') and args.env:
            self.trops_env = args.env
            self.git_dir = os.path.expandvars(
                self.config[self.trops_env]['git_dir'])
            self.work_tree = os.path.expandvars(
                self.config[self.trops_env]['work_tree'])
            self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                            '--work-tree=' + self.work_tree]

        cmd = self.git_cmd + ['show', args.commit]
        subprocess.call(cmd)

    def _follow(self, file):

        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def log(self, args, other_args):

        log_file = self.trops_dir + '/log/trops.log'
        numlines = 15
        if args.tail and args.tail != None:
            numlines = args.tail

        if args.all:
            with open(log_file) as ff:
                for line in ff.readlines():
                    print(line, end='')
        else:
            with open(log_file) as ff:
                for line in ff.readlines()[-numlines:]:
                    print(line, end='')
        if args.follow:
            ff = open(log_file, "r")
            try:
                lines = self._follow(ff)
                for line in lines:
                    print(line, end='')
            except KeyboardInterrupt:
                print('\nClosing trops log...')

    def ll(self, args, other_args):
        """Shows the list of git-tracked files"""

        dirs = [args.dir] + other_args
        for dir in dirs:
            if os.path.isdir(dir):
                os.chdir(dir)
                cmd = self.git_cmd + ['ls-files']
                output = subprocess.check_output(cmd)
                for f in output.decode("utf-8").splitlines():
                    cmd = ['ls', '-al', f]
                    subprocess.call(cmd)

    def touch(self, args, other_args):

        for file_path in args.paths:

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

    def drop(self, args, other_args):

        for file_path in args.paths:

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
            message = f"Goodbye { file_path }"
            cmd = self.git_cmd + ['commit', '-m', message]
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

    def check(self, args, other_args):
        """Git wrapper command"""

        if hasattr(args, 'env') and args.env:
            self.trops_env = args.env
            self.git_dir = os.path.expandvars(
                self.config[self.trops_env]['git_dir'])
            self.work_tree = os.path.expandvars(
                self.config[self.trops_env]['work_tree'])
            self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                            '--work-tree=' + self.work_tree]

        cmd = self.git_cmd + ['status']
        subprocess.call(cmd)

    def main(self):
        """Get subcommand and arguments and pass them to the hander"""

        parser = argparse.ArgumentParser(
            description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        parser.add_argument('-v', '--version',
                            help="Print version", action='store_true')
        parser.add_argument('--dev',
                            help="Development mode", action='store_true')
        # Add trops init subparsers and arguments
        add_init_subparsers(subparsers)
        # Add trops env subparsers and arguments
        add_env_subparsers(subparsers)
        # Add trops file subparsers and arguments
        add_file_subparsers(subparsers)
        # Add trops koumyo arguments
        koumyo_subparsers(subparsers)
        # Add trops repo arguments
        add_repo_subparsers(subparsers)
        # trops git <file/dir>
        parser_git = subparsers.add_parser('git', help='git wrapper')
        parser_git.add_argument('-s', '--sudo', help="Use sudo",
                                action='store_true')
        parser_git.add_argument('-e', '--env', help="Set env")
        parser_git.set_defaults(handler=self.git)
        # trops show commit[:path]
        parser_show = subparsers.add_parser(
            'show', help='trops show commit[:path]')
        parser_show.add_argument('-e', '--env', help="Set env")
        parser_show.add_argument('commit', help='Set commit[:path]')
        parser_show.set_defaults(handler=self.show)
        # trops capture-cmd <ignore_fields> <return_code> <command>
        capture_cmd_subparsers(subparsers)
        # trops log
        parser_log = subparsers.add_parser('log', help='show log')
        parser_log.add_argument(
            '-t', '--tail', type=int, help='set number of lines to show')
        parser_log.add_argument(
            '-f', '--follow', action='store_true', help='follow log interactively')
        parser_log.add_argument(
            '-a', '--all', action='store_true', help='show all log')
        parser_log.set_defaults(handler=self.log)
        # trops ll
        parser_ll = subparsers.add_parser('ll', help="list files")
        parser_ll.add_argument(
            'dir', help='directory path', nargs='?', default=os.getcwd())
        parser_ll.add_argument(
            '-e', '--env', default='default', help='Set environment name')
        parser_ll.set_defaults(handler=self.ll)
        # trops touch <path>
        parser_touch = subparsers.add_parser(
            'touch', help="add/update file in the git repo")
        parser_touch.add_argument('paths', nargs='+', help='path of file')
        parser_touch.set_defaults(handler=self.touch)
        # trops drop <path>
        parser_drop = subparsers.add_parser(
            'drop', help="remove file from the git repo")
        parser_drop.add_argument('paths', nargs='+', help='path of file')
        parser_drop.set_defaults(handler=self.drop)
        # trops random-name
        parser_random_name = subparsers.add_parser(
            'random-name', help='generate random name')
        parser_random_name.set_defaults(handler=random_name)
        # trops gensid
        parser_gensid = subparsers.add_parser(
            'gensid', help='generate sid')
        parser_gensid.set_defaults(handler=generate_sid)
        # trops check
        parser_check = subparsers.add_parser('check', help='Check status')
        parser_check.add_argument('-s', '--sudo', help="Use sudo",
                                  action='store_true')
        parser_check.add_argument('-e', '--env', help="Set env")
        parser_check.set_defaults(handler=self.check)

        # Pass args and other args to the hander
        args, other_args = parser.parse_known_args()
        if args.version:
            print('trops', __version__)
            exit(0)
        if hasattr(args, 'handler'):
            args.handler(args, other_args)
        else:
            parser.print_help()
        # TODO: The other_args are only needed for trops git. Clean them
        #       where they're not needed


def main():

    tr = Trops()
    tr.main()


if __name__ == "__main__":
    main()
