import os
import subprocess
import sys

from datetime import datetime
from pathlib import Path

from .trops import Trops
from .utils import absolute_path


class TropsCapCmd(Trops):
    """Trops Capture Command class"""

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        # Start setting the header
        attributes = ['trops_env', 'trops_sid', 'trops_tags']
        self.trops_header = ['trops'] + [getattr(self, attr) for attr in attributes if getattr(self, attr, None)]

    def capture_cmd(self):
        """Capture and log the executed command"""

        rc = self.args.return_code
        now = datetime.now().strftime("%H-%M")
        executed_cmd = self.other_args
        time_and_cmd = f"{now} {' '.join(executed_cmd)}"

        # Ensure tmp directory exists
        tmp_dir = os.path.join(self.trops_dir, 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)

        # Path to the file storing the last executed command
        last_cmd_path = os.path.join(tmp_dir, 'last_cmd')

        # Check if the current command matches the last executed command
        if self._is_repeat_command(last_cmd_path, time_and_cmd):
            if not self.disable_header:
                self.print_header()
            sys.exit(0)

        # Save the current command as the last executed command
        self._save_last_command(last_cmd_path, time_and_cmd)

        # Skip logging if the command is in the ignore list
        if executed_cmd[0] in self.ignore_cmds:
            self.print_header()
            sys.exit(0)

        message_parts = [
            f"CM {' '.join(executed_cmd)} #> PWD={os.getenv('PWD')}",
            f"EXIT={rc}",
            f"TROPS_SID={os.getenv('TROPS_SID')}" if os.getenv('TROPS_SID') else None,
            f"TROPS_ENV={os.getenv('TROPS_ENV')}" if os.getenv('TROPS_ENV') else None,
            f"TROPS_TAGS={self.trops_tags}" if self.trops_tags else None,
        ]
        message = ', '.join(part for part in message_parts if part is not None)

        if rc == 0:
            self.logger.info(message)
        else:
            self.logger.warning(message)

        self._yum_log(executed_cmd)
        self._apt_log(executed_cmd)
        self._update_files(executed_cmd)
        self._add_tee_output_file(executed_cmd)

        if not self.disable_header:
            self.print_header()

    def _is_repeat_command(self, last_cmd_path, time_and_cmd):
        """Check if the current command is a repeat of the last command"""
        if os.path.isfile(last_cmd_path):
            with open(last_cmd_path, 'r') as f:
                return time_and_cmd == f.read()
        return False

    def _save_last_command(self, last_cmd_path, time_and_cmd):
        """Save the current command as the last executed command"""
        with open(last_cmd_path, 'w') as f:
            f.write(time_and_cmd)

    def print_header(self):
        # Print -= trops|env|sid|tags =-
        print(f'\n-= {"|".join(self.trops_header)} =-')

    def _yum_log(self, executed_cmd):

        # Check if sudo is used
        executed_cmd = executed_cmd[1:] if executed_cmd[0] == 'sudo' else executed_cmd

        if executed_cmd[0] in ['yum', 'dnf'] and any(x in executed_cmd for x in ['install', 'update', 'remove']):
            cmd = ['rpm', '-qa']
            result = subprocess.run(cmd, capture_output=True, check=True)
            pkg_list = result.stdout.decode('utf-8').splitlines()
            pkg_list.sort()

            pkg_list_file = os.path.join(self.trops_dir, f'log/rpm_pkg_list.{self.hostname}')
            with open(pkg_list_file, 'w') as f:
                f.write('\n'.join(pkg_list))

            self.add_and_commit_file(pkg_list_file)

    def _apt_log(self, executed_cmd):
        if 'apt' in executed_cmd and any(x in executed_cmd for x in ['upgrade', 'install', 'update', 'remove', 'autoremove']):
            self._update_pkg_list(' '.join(executed_cmd))
        # TODO: Add log trops git show hex

    def _update_pkg_list(self, args):

        # Update the pkg_List
        cmd = ['apt', 'list', '--installed']
        result = subprocess.run(cmd, capture_output=True)
        pkg_list = result.stdout.decode('utf-8').splitlines()
        pkg_list.sort()

        pkg_list_file = self.trops_dir + \
            f'/log/apt_pkg_list.{ self.hostname }'
        f = open(pkg_list_file, 'w')
        f.write('\n'.join(pkg_list))
        f.close()

        self.add_and_commit_file(pkg_list_file)

    def _add_file_in_git_repo(self, executed_cmd, n):

            for file_arg in executed_cmd[n:]:
                file_path = absolute_path(file_arg)
                if os.path.isfile(file_path):
                    # Ignore the file if it is under a git repository
                    if file_is_in_a_git_repo(file_path):
                        self.logger.info(
                            f"FL { file_path } is under a git repository #> PWD=*, EXIT=*, TROPS_SID={ self.trops_sid }, TROPS_ENV={ self.trops_env }")
                        sys.exit(0)
                    git_msg, log_note = self._generate_git_msg_and_log_note(file_path)
                    result = self._add_and_commit_file(file_path, git_msg)
                    # If there's an update, log it in the log file
                    if result.returncode == 0:
                        msg = result.stdout.decode('utf-8').splitlines()[0]
                        print(msg)
                        self._add_file_log(file_path, log_note)
                    else:
                        print('No update')

    def _add_file_log(self, file_path, log_note):
        """Add an FL log entry"""
        cmd = self.git_cmd + \
            ['log', '--oneline', '-1', file_path]
        output = subprocess.check_output(
            cmd).decode("utf-8").split()
        if file_path in output:
            mode = oct(os.stat(file_path).st_mode)[-4:]
            owner = Path(file_path).owner()
            group = Path(file_path).group()
            message = f"FL trops show { output[0] }:{ absolute_path(file_path).lstrip(self.work_tree)}  #> { log_note }, O={ owner },G={ group },M={ mode }"
            if self.trops_sid:
                message += f" TROPS_SID={ self.trops_sid }"
            message += f" TROPS_ENV={ self.trops_env }"
            if self.trops_tags:
                message += f" TROPS_TAGS={self.trops_tags}"

            self.logger.info(message)

    def _add_and_commit_file(self, file_path, git_msg):
        """Add a file in the git repo"""
        # Add the file and commit
        cmd = self.git_cmd + ['add', file_path]
        _ = subprocess.run(cmd, capture_output=True)
        cmd = self.git_cmd + ['commit', '-m', git_msg, file_path]
        
        return subprocess.run(cmd, capture_output=True)

    def _generate_git_msg_and_log_note(self, file_path):
        """Generate the git commit message and log note"""
        # Check if the path is in the git repo
        cmd = self.git_cmd + ['ls-files', file_path]
        result = subprocess.run(cmd, capture_output=True)
        # Set the message based on the output
        if result.stdout.decode("utf-8"):
            git_msg = f"Update { file_path }"
            log_note = 'UPDATE'
        else:
            git_msg = f"Add { file_path }"
            log_note = 'ADD'
        if self.trops_tags:
            git_msg = f"{ git_msg } ({ self.trops_tags })"

        return git_msg, log_note

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
            self._add_file_in_git_repo(executed_cmd, 1)

    def _add_tee_output_file(self, executed_cmd):

        if '|' in executed_cmd:
            n = executed_cmd.index('|')
            if executed_cmd[n+1] == 'tee':
                n += 1
                self._add_file_in_git_repo(executed_cmd, n)
        elif '|tee' in executed_cmd:
            n = executed_cmd.index('|tee')
            self._add_file_in_git_repo(executed_cmd, n)

def capture_cmd(args, other_args):

    tc = TropsCapCmd(args, other_args)
    tc.capture_cmd()

def add_capture_cmd_subparsers(subparsers):

    parser_capture_cmd = subparsers.add_parser(
        'capture-cmd', help='Capture command line strings', add_help=False)
    parser_capture_cmd.add_argument(
        'return_code', type=int, help='return code')
    parser_capture_cmd.set_defaults(handler=capture_cmd)

def file_is_in_a_git_repo(file_path):

    parent_dir = os.path.dirname(file_path)
    if parent_dir != '':
        os.chdir(parent_dir)
    cmd = ['git', 'rev-parse', '--is-inside-work-tree']
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        return True
    else:
        return False