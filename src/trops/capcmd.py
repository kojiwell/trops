import os
import subprocess
import distutils.util
import logging

from configparser import ConfigParser
from getpass import getuser
from socket import gethostname
from pathlib import Path

from trops.utils import real_path


class TropsCapCmd:

    def __init__(self, args, other_args):

        # Set username and hostname
        self.username = getuser()
        self.hostname = gethostname().split('.')[0]

        # Set trops_dir
        if os.getenv('TROPS_DIR'):
            self.trops_dir = os.path.expandvars('$TROPS_DIR')
        else:
            self.trops_dir = False

        # Set trops_tags
        if os.getenv('TROPS_TAGS'):
            self.trops_tags = os.path.expandvars('$TROPS_TAGS')
        else:
            self.trops_tags = False

        # Set trops_sid
        if os.getenv('TROPS_SID'):
            self.trops_sid = os.path.expandvars('$TROPS_SID')
        else:
            self.trops_sid = False

        # return_code
        self.return_code = args.return_code
        self.ignore_fields = args.ignore_fields
        self.other_args = other_args

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

                if 'ignore_cmds' in self.config[self.trops_env]:
                    self.ignore_cmds = self.config[self.trops_env]['ignore_cmds'].split(
                        ',')
                else:
                    self.ignore_cmds = False

            os.makedirs(self.trops_dir + '/log', exist_ok=True)
            self.trops_logfile = self.trops_dir + '/log/trops.log'

            logging.basicConfig(format=f'%(asctime)s { self.username }@{ self.hostname } %(levelname)s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S',
                                filename=self.trops_logfile,
                                level=logging.DEBUG)
            self.logger = logging.getLogger()

    def capture_cmd(self):
        """\
        log executed command
        NOTE: You need to set PROMPT_COMMAND in bash as shown below:
        PROMPT_COMMAND='trops capture-cmd <ignore_field> <return code> $(history 1)'"""

        rc = self.return_code

        executed_cmd = self.other_args
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

        for n in range(self.ignore_fields):
            executed_cmd.pop(0)

        if self.ignore_cmds and executed_cmd[0] in self.ignore_cmds:
            exit(0)

        message = 'CM ' + ' '.join(executed_cmd) + \
            f"  #> PWD={ os.environ['PWD'] }, EXIT={ rc }"
        if 'TROPS_SID' in os.environ:
            message = message + ', TROPS_SID=' + os.environ['TROPS_SID']
        if 'TROPS_ENV' in os.environ:
            message = message + ', TROPS_ENV=' + os.environ['TROPS_ENV']
        if rc == 0:
            self.logger.info(message)
        else:
            self.logger.warning(message)
        self._yum_log(executed_cmd)
        self._apt_log(executed_cmd)
        self._update_files(executed_cmd)

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
            if self.trops_tags:
                git_msg = f"{ git_msg } ({ self.trops_tags })"
            # Add and commit
            cmd = self.git_cmd + ['add', pkg_list_file]
            subprocess.call(cmd)
            cmd = self.git_cmd + ['commit', '-m', git_msg, pkg_list_file]
            subprocess.call(cmd)

    def _apt_log(self, executed_cmd):

        if 'apt' in executed_cmd and ('upgrade' in executed_cmd
                                      or 'install' in executed_cmd
                                      or 'update' in executed_cmd
                                      or 'remove' in executed_cmd
                                      or 'autoremove' in executed_cmd):
            self._update_pkg_list(' '.join(executed_cmd))
        # TODO: Add log trops git show hex

    def _update_pkg_list(self, args):

        # Update the pkg_List
        apt_log_file = '/var/log/apt/history.log'
        cmd = self.git_cmd + ['ls-files', apt_log_file]
        result = subprocess.run(cmd, capture_output=True)
        if result.stdout.decode("utf-8"):
            git_msg = f"Update { apt_log_file }"
            log_note = 'UPDATE'
        else:
            git_msg = f"Add { apt_log_file }"
            log_note = 'ADD'
        if self.trops_tags:
            git_msg = f"{ git_msg } ({ self.trops_tags })"
        cmd = self.git_cmd + ['add', apt_log_file]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m',
                              git_msg, apt_log_file]
        # Commit the change if needed
        result = subprocess.run(cmd, capture_output=True)
        # If there's an update, log it in the log file
        if result.returncode == 0:
            msg = result.stdout.decode('utf-8').splitlines()[0]
            print(msg)
            cmd = self.git_cmd + \
                ['log', '--oneline', '-1', apt_log_file]
            output = subprocess.check_output(
                cmd).decode("utf-8").split()
            if apt_log_file in output:
                mode = oct(os.stat(apt_log_file).st_mode)[-4:]
                owner = Path(apt_log_file).owner()
                group = Path(apt_log_file).group()
                message = f"FL trops show -e { self.trops_env } { output[0] }:{ real_path(apt_log_file).lstrip(self.work_tree)}  #> { log_note } O={ owner },G={ group },M={ mode }"
                if self.trops_sid:
                    message = f"{ message } TROPS_SID={ self.trops_sid }"
                message = f"{ message } TROPS_ENV={ self.trops_env }"
                self.logger.info(message)
        else:
            print('No update')

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
                            f"FL Trops ignores { ii_path } -- The file is under a git repository")
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
                    if self.trops_tags:
                        git_msg = f"{ git_msg } ({ self.trops_tags })"
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
                            message = f"FL trops show -e { self.trops_env } { output[0] }:{ real_path(ii_path).lstrip(self.work_tree)}  #> { log_note }, O={ owner },G={ group },M={ mode }"
                            if self.trops_sid:
                                message = f"{ message } TROPS_SID={ self.trops_sid }"
                            message = f"{ message } TROPS_ENV={ self.trops_env }"
                            self.logger.info(message)
                    else:
                        print('No update')


def capture_cmd(args, other_args):

    tc = TropsCapCmd(args, other_args)
    tc.capture_cmd()


def capture_cmd_subparsers(subparsers):

    parser_capture_cmd = subparsers.add_parser(
        'capture-cmd', help='Capture command line strings', add_help=False)
    parser_capture_cmd.add_argument(
        'ignore_fields', type=int, help='number of fields to ignore')
    parser_capture_cmd.add_argument(
        'return_code', type=int, help='return code')
    parser_capture_cmd.set_defaults(handler=capture_cmd)
