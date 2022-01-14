import os
import sys
import subprocess
import argparse
import logging
import distutils.util
from configparser import ConfigParser, NoSectionError, NoOptionError
from textwrap import dedent
from datetime import datetime
from pathlib import Path
from getpass import getuser
from socket import gethostname

from trops.utils import real_path, random_name
from trops.env import TropsEnv


class Trops:
    """Trops Class"""

    def __init__(self):

        self.config = ConfigParser()
        # Set trops_dir
        if 'TROPS_DIR' in os.environ:
            self.trops_dir = os.path.expandvars('$TROPS_DIR')
        else:
            self.trops_dir = os.path.expandvars('$HOME/.trops')
        # Set trops_env
        if 'TROPS_ENV' in os.environ:
            self.trops_env = os.environ['TROPS_ENV']
        else:
            self.trops_env = 'default'

        self.conf_file = self.trops_dir + '/trops.cfg'
        if os.path.isfile(self.conf_file):
            self.config.read(self.conf_file)
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
            try:
                self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                                '--work-tree=' + self.work_tree]
            except KeyError:
                pass
            try:
                self.sudo = distutils.util.strtobool(
                    self.config[self.trops_env]['sudo'])
                if self.sudo:
                    self.git_cmd = ['sudo'] + self.git_cmd
            except KeyError:
                pass

        self.username = getuser()
        self.hostname = gethostname()

        logging.basicConfig(format=f'%(asctime)s { self.username }@{ self.hostname } %(levelname)s  %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=self.trops_dir + '/log/trops.log',
                            level=logging.DEBUG)
        self.logger = logging.getLogger()

    def env_init(self, args, other_args):
        """Setup trops project"""

        trenv = TropsEnv(args, other_args)
        trenv.initialize()

    def env_show(self, args, other_args):

        trenv = TropsEnv(args, other_args)
        trenv.show()

    def env_update(self, args, other_args):

        trenv = TropsEnv(args, other_args)
        trenv.update()

    def git(self, args, other_args):
        """Git wrapper command"""

        cmd = self.git_cmd + other_args
        subprocess.call(cmd)

    def capture_cmd(self, args, other_args):
        """\
        log executed command
        NOTE: You need to set PROMPT_COMMAND in bash as shown below:
        PROMPT_COMMAND='trops capture-cmd <ignore> $(history 1)'"""

        # TODO: Rename fuction something else (maybe capture-cls) because it
        # is confused with trops show-log.

        rc = args.return_code

        executed_cmd = other_args
        # Create trops_dir/tmp directory
        tmp_dir = self.trops_dir + '/tmp'
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        # Compare the executed_cmd if last_cmd exists
        last_cmd = tmp_dir + '/last_cmd'
        if os.path.isfile(last_cmd):
            with open(last_cmd, mode='r') as f:
                if ' '.join(executed_cmd) in f.read():
                    exit(0)
        with open(last_cmd, mode='w') as f:
            f.write(' '.join(executed_cmd))

        for n in range(args.ignore_fields):
            executed_cmd.pop(0)

        ignored_cmds = ['trops', 'ls', 'top', 'cat']
        if executed_cmd[0] in ignored_cmds:
            exit(0)

        message = ' '.join(executed_cmd) + \
            f"  # PWD={ os.environ['PWD'] }, EXIT={ rc }"
        if 'TROPS_SID' in os.environ:
            message = message + ', TROPS_SID=' + os.environ['TROPS_SID']
        if rc == 0:
            self.logger.info(message)
        else:
            self.logger.warning(message)
        self._yum_log(executed_cmd)
        self._apt_log(executed_cmd)
        self._update_files(executed_cmd)
        # TODO: Catch chmod and chown and log owner and permission
        # TODO: Show username and hostname in the log

    def _yum_log(self, executed_cmd):

        # Check if sudo is used
        if 'sudo' == executed_cmd[0]:
            executed_cmd.pop(0)

        if executed_cmd[0] in ['yum', 'dnf'] and ('install' in executed_cmd
                                                  or 'update' in executed_cmd
                                                  or 'remove' in executed_cmd):
            cmd = ['rpm', '-qa']
            result = subprocess.run(cmd, capture_output=True)
            pkg_list = result.stdout.decode('utf-8').splitlines()
            pkg_list.sort()

            pkg_list_file = self.trops_dir + \
                f'/log/rpm_pkg_list.{ self.hostname }'
            f = open(pkg_list_file, 'w')
            f.write('\n'.join(pkg_list))
            f.close()

            # Check if the path is in the git repo
            cmd = self.git_cmd + ['ls-files', pkg_list_file]
            output = subprocess.check_output(cmd).decode("utf-8")
            # Set the message based on the output
            if output:
                git_msg = f"Update { pkg_list_file }"
            else:
                git_msg = f"Add { pkg_list_file }"
            # Add and commit
            cmd = self.git_cmd + ['add', pkg_list_file]
            subprocess.call(cmd)
            cmd = self.git_cmd + ['commit', '-m', git_msg, pkg_list_file]
            subprocess.call(cmd)

    def _apt_log(self, executed_cmd):

        if 'apt' in executed_cmd and ('upgrade' in executed_cmd
                                      or 'install' in executed_cmd
                                      or 'remove' in executed_cmd
                                      or 'autoremove' in executed_cmd):
            self._update_pkg_list(' '.join(executed_cmd))
        # TODO: Add log trops git show hex

    def _update_files(self, executed_cmd):
        """Add a file or directory in the git repo"""

        # Remove sudo from executed_cmd
        if 'sudo' == executed_cmd[0]:
            executed_cmd.pop(0)
        # TODO: Pop Sudo options such as -u and -E

        # Check if editor is launched
        editors = ['vim', 'vi', 'emacs', 'nano']
        if executed_cmd[0] in editors:
            # Add the edited file in trops git
            for ii in executed_cmd[1:]:
                ii_path = real_path(ii)
                if os.path.isfile(ii_path):
                    # Ignore the file if it is under a git repository
                    ii_parent_dir = os.path.dirname(ii_path)
                    os.chdir(ii_parent_dir)
                    cmd = ['git', 'rev-parse', '--is-inside-work-tree']
                    result = subprocess.run(cmd, capture_output=True)
                    if result.returncode == 0:
                        self.logger.info(
                            f"TROPS IGNORE { ii_path } -- The file is under a git repository")
                        exit(0)
                    # Check if the path is in the git repo
                    cmd = self.git_cmd + ['ls-files', ii_path]
                    result = subprocess.run(cmd, capture_output=True)
                    # Set the message based on the output
                    if result.stdout.decode("utf-8"):
                        git_msg = f"Update { ii_path }"
                        log_note = 'UPDATE'
                    else:
                        git_msg = f"Add { ii_path }"
                        log_note = 'ADD'
                    # Add the file and commit
                    cmd = self.git_cmd + ['add', ii_path]
                    result = subprocess.run(cmd, capture_output=True)
                    cmd = self.git_cmd + ['commit', '-m', git_msg, ii_path]
                    result = subprocess.run(cmd, capture_output=True)
                    # If there's an update, log it in the log file
                    if result.returncode == 0:
                        msg = result.stdout.decode('utf-8').splitlines()[0]
                        print(msg)
                        cmd = self.git_cmd + \
                            ['log', '--oneline', '-1', ii_path]
                        output = subprocess.check_output(
                            cmd).decode("utf-8").split()
                        if ii_path in output:
                            mode = oct(os.stat(ii_path).st_mode)[-4:]
                            owner = Path(ii_path).owner()
                            group = Path(ii_path).group()
                            self.logger.info(
                                f"trops git show { output[0] }:{ real_path(ii_path).lstrip('/')}  # { log_note }, O={ owner },G={ group },M={ mode }")
                    else:
                        print('No update')

    def log(self, args, other_args):

        log_file = self.trops_dir + '/log/trops.log'

        if args.follow:
            cmd = ['tail', '-f', log_file]
        elif args.tail:
            cmd = ['tail', f'-{ args.tail }', log_file]
        elif args.all:
            cmd = ['cat', log_file]
        else:
            cmd = ['tail', '-15', log_file]
        try:
            subprocess.call(cmd)
        except KeyboardInterrupt:
            print('\nClosing trops show-log...')

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
        output = subprocess.check_output(cmd).decode("utf-8")
        # Set the message based on the output
        if output:
            git_msg = f"Update { file_path }"
            log_note = "UPDATE"
        else:
            git_msg = f"Add { file_path }"
            log_note = "ADD"
        # Add and commit
        cmd = self.git_cmd + ['add', file_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m', git_msg, file_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['log', '--oneline', '-1', file_path]
        output = subprocess.check_output(
            cmd).decode("utf-8").split()
        if file_path in output:
            mode = oct(os.stat(file_path).st_mode)[-4:]
            owner = Path(file_path).owner()
            group = Path(file_path).group()
            self.logger.info(
                f"trops git show { output[0] }:{ real_path(file_path).lstrip('/')}  # { log_note } O={ owner },G={ group },M={ mode }")

    def bye(self, args, other_args):

        for file_path in args.paths:

            self._bye_file(file_path)

    def _bye_file(self, file_path):
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
        self.logger.info(
            f"trops git show { output[0] }:{ real_path(file_path).lstrip('/')}  # BYE")

    def _update_pkg_list(self, args):

        # Update the pkg_List
        pkg_list_file = self.trops_dir + f'/log/apt_pkg_list_{ self.hostname }'
        f = open(pkg_list_file, 'w')
        cmd = ['apt', 'list', '--installed']
        if self.sudo:
            cmd.insert(0, 'sudo')
        pkg_list = subprocess.check_output(cmd).decode('utf-8')
        f.write(pkg_list)
        f.close()
        # Commit the change if needed
        cmd = self.git_cmd + ['add', pkg_list_file]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m',
                              f'Update { pkg_list_file }', pkg_list_file]
        subprocess.call(cmd)

    def main(self):
        """Get subcommand and arguments and pass them to the hander"""

        parser = argparse.ArgumentParser(
            description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        # trops env
        parser_env = subparsers.add_parser('env', help='initialize trops')
        env_subparsers = parser_env.add_subparsers()
        perser_env_show = env_subparsers.add_parser(
            'show', help='show the current environment')
        perser_env_show.set_defaults(handler=self.env_show)
        # trops env init <dir>
        parser_env_init = env_subparsers.add_parser(
            'init', help='initialize trops environment')
        parser_env_init.add_argument(
            'dir', help='trops directory')
        parser_env_init.add_argument(
            '-w', '--work-tree', default='/', help='Set work-tree (default: %(default)s)')
        parser_env_init.add_argument(
            '-e', '--env', default='default', help='Set environment name (default: %(default)s)')
        parser_env_init.set_defaults(handler=self.env_init)
        # trops env update <dir>
        parser_env_update = env_subparsers.add_parser(
            'update', help='update trops environment')
        parser_env_update.add_argument(
            '-w', '--work-tree', help='work-tree')
        parser_env_update.add_argument(
            '-g', '--git-dir', help='git-dir')
        parser_env_update.add_argument(
            '-e', '--env', default='default', help='Set environment name')
        parser_env_update.set_defaults(handler=self.env_update)
        # trops git <file/dir>
        parser_git = subparsers.add_parser('git', help='git wrapper')
        parser_git.add_argument('-s', '--sudo', help="Use sudo",
                                action='store_true')
        parser_git.set_defaults(handler=self.git)
        # trops capture-cmd <ignore_fields> <return_code> <command>
        parser_capture_cmd = subparsers.add_parser(
            'capture-cmd', help='Capture command line strings', add_help=False)
        parser_capture_cmd.add_argument('ignore_fields', type=int,
                                        default=1, help='set number of fields to ingore')
        parser_capture_cmd.add_argument('return_code', type=int,
                                        default=0, help='set return code')
        parser_capture_cmd.set_defaults(handler=self.capture_cmd)
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
        parser_ll.set_defaults(handler=self.ll)
        # trops touch
        parser_touch = subparsers.add_parser(
            'touch', help="add/update file in the git repo")
        parser_touch.add_argument('paths', nargs='+', help='path of file')
        parser_touch.set_defaults(handler=self.touch)
        # trops bye
        parser_bye = subparsers.add_parser(
            'bye', help="remove file from the git repo")
        parser_bye.add_argument('paths', nargs='+', help='path of file')
        parser_bye.set_defaults(handler=self.bye)
        # trops random-name
        parser_random_name = subparsers.add_parser(
            'random-name', help='generate random name')
        parser_random_name.set_defaults(handler=random_name)

        # Pass args and other args to the hander
        args, other_args = parser.parse_known_args()
        if hasattr(args, 'handler'):
            args.handler(args, other_args)
        else:
            parser.print_help()


def main():

    tr = Trops()
    tr.main()


if __name__ == "__main__":
    main()
