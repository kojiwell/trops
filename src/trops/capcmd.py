import os
import subprocess
import distutils.util
import logging

from time import time
from configparser import ConfigParser
from getpass import getuser
from socket import gethostname

from trops.utils import real_path


class TropsCapCmd:

    def __init__(self, args, other_args):

        self.return_code = args.return_code
        self.executed_cmd = other_args

        if os.getenv('TROPS_DIR'):
            self.trops_dir = os.getenv('TROPS_DIR')
            self.trops_conf = self.trops_dir + '/trops.cfg'
            self.trops_log_dir = self.trops_dir + '/log'
        else:
            print('TROPS_DIR is not set')
            exit(1)

        if hasattr(args, 'env') and args.env:
            self.trops_env = args.env
        elif os.getenv('TROPS_ENV'):
            self.trops_env = os.getenv('TROPS_ENV')
        else:
            print('TROPS_ENV is not set')

        self.config = ConfigParser()
        if os.path.isfile(self.trops_conf):
            self.config.read(self.trops_conf)

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

            sudo_true = distutils.util.strtobool(
                self.config[self.trops_env]['sudo'])
            if sudo_true:
                self.git_cmd = ['sudo'] + self.git_cmd

        self.username = getuser()
        self.hostname = gethostname()
        self.trops_logfile = self.trops_dir + '/log/trops.log'

        logging.basicConfig(format=f'%(asctime)s { self.username }@{ self.hostname } %(levelname)s  %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=self.trops_logfile,
                            level=logging.DEBUG)
        self.logger = logging.getLogger()

    def capture_cmd(self):
        """\
        log executed command
        NOTE: You need to set PROMPT_COMMAND in bash as shown below:
        PROMPT_COMMAND='trops capture-cmd $? !!'"""

        rc = self.return_code
        ec = self.executed_cmd
        # Create trops_dir/tmp directory
        tmp_dir = self.trops_dir + '/tmp'
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        # Compare the executed_cmd if last_cmd exists
        last_cmd = tmp_dir + '/last_cmd'
        if os.path.isfile(last_cmd):
            with open(last_cmd, mode='r') as f:
                if ' '.join(ec) in f.read():
                    exit(0)
        # Update last_cmd
        with open(last_cmd, mode='w') as f:
            f.write(str(time()) + ' ' + ' '.join(ec))

        ignored_cmds = ['trops', 'ls', 'top', 'cat']
        if ec[0] in ignored_cmds:
            exit(0)

        message = ' '.join(ec) + \
            f"  # PWD={ os.environ['PWD'] }, EXIT={ rc }"
        if 'TROPS_SID' in os.environ:
            message = message + ', TROPS_SID=' + os.environ['TROPS_SID']
        if rc == 0:
            self.logger.info(message)
        else:
            self.logger.warning(message)
        # self._yum_log(executed_cmd)
        # self._apt_log(executed_cmd)
        # self._update_files(executed_cmd)

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


def capture_cmd(args, other_args):

    tc = TropsCapCmd(args, other_args)
    tc.capture_cmd()


def capture_cmd_subparsers(subparsers):

    parser_capture_cmd = subparsers.add_parser(
        'capture-cmd2', help='Capture command line strings', add_help=False)
    parser_capture_cmd.add_argument(
        'return_code', type=int, help='return code')
    parser_capture_cmd.set_defaults(handler=capture_cmd)
