import os
import subprocess
import sys

from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from configparser import ConfigParser

from .trops import Trops
import re
from .utils import absolute_path


class TropsCapCmd(Trops):
    """Trops Capture Command class"""

    def __init__(self, args, other_args):
        # Enforce TROPS_DIR for capture-cmd only (per project requirement)
        if 'TROPS_DIR' not in os.environ:
            raise SystemExit('ERROR: The TROPS_DIR environment variable has not been set.')
        super().__init__(args, other_args)

        # If TROPS_ENV is specified but missing in config, error out early with a clear message
        conf_path = os.path.join(self.trops_dir, 'trops.cfg')
        if self.trops_env and os.path.isfile(conf_path):
            config = ConfigParser()
            config.read(conf_path)
            if not config.has_section(self.trops_env):
                raise SystemExit(f"ERROR: TROPS_ENV '{self.trops_env}' does not exist in your configuration at {conf_path}.")

        # Ensure attributes exist even when no config section is present
        # This avoids AttributeError later and provides sane defaults
        if not hasattr(self, 'ignore_cmds'):
            self.ignore_cmds = {'ttags'}
        if not hasattr(self, 'disable_header'):
            self.disable_header = False

        # Start setting the header with stable positions: trops|env|sid|tags
        header_env = getattr(self, 'trops_env', '') or ''
        header_sid = getattr(self, 'trops_sid', '') or ''
        header_tags = getattr(self, 'trops_tags', '') or ''
        self.trops_header = ['trops', header_env, header_sid, header_tags]
        # Defer FL logs until after command logging to preserve real-world order
        self._defer_file_logs = False
        self._deferred_file_logs = []

    def _flush_deferred_file_logs(self) -> None:
        """Flush and clear any deferred file logs."""
        if getattr(self, '_deferred_file_logs', None):
            for fl_message in self._deferred_file_logs:
                self.logger.info(fl_message)
        self._defer_file_logs = False
        self._deferred_file_logs = []

    def capture_cmd(self) -> None:
        """Capture and log the executed command"""

        return_code = self.args.return_code
        now_hm = datetime.now().strftime("%H-%M")

        # Enable deferring of file logs that may be produced by pre-processing
        self._defer_file_logs = True
        self._deferred_file_logs = []

        if not self.other_args:
            # No command to log; flush any deferred logs then exit
            self._flush_deferred_file_logs()
            self.print_header()
            sys.exit(0)

        executed_cmd = self.other_args
        time_and_cmd = f"{now_hm} {' '.join(executed_cmd)}"

        # Fast-path: skip early if command is in ignore list (performance)
        sanitized_for_ignore = self._sanitize_for_sudo(executed_cmd)
        if self.ignore_cmds and sanitized_for_ignore and sanitized_for_ignore[0] in self.ignore_cmds:
            # Ignored command; flush deferred logs to preserve previous behavior
            self._flush_deferred_file_logs()
            self.print_header()
            sys.exit(0)

        # Ensure tmp directory exists
        tmp_dir = Path(self.trops_dir) / 'tmp'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        last_cmd_path = tmp_dir / 'last_cmd'

        # Side-effect operations that should happen even if the command is repeated
        # 1) Track files edited by common editors
        self._track_editor_files(executed_cmd)
        # 2) Track files written via tee
        wrote_with_tee = self._add_tee_output_file(executed_cmd)
        # 3) Try pushing if remote is configured and we actually added/updated files
        if wrote_with_tee:
            self._push_if_remote_set()

        # Skip if repeated within the same minute (after performing file updates)
        if self._is_repeat_command(str(last_cmd_path), time_and_cmd):
            if not self.disable_header:
                # Repeated command; flush deferred logs to preserve previous behavior
                self._flush_deferred_file_logs()
                self.print_header()
            sys.exit(0)

        # Save last command signature
        self._save_last_command(str(last_cmd_path), time_and_cmd)

        # (kept for clarity; normally unreachable due to early fast-path above)
        sanitized_for_ignore = self._sanitize_for_sudo(executed_cmd)
        if self.ignore_cmds and sanitized_for_ignore and sanitized_for_ignore[0] in self.ignore_cmds:
            # Ignored command; flush deferred logs to preserve previous behavior
            self._flush_deferred_file_logs()
            self.print_header()
            sys.exit(0)

        # Log command message
        message = self._compose_capture_message(executed_cmd, return_code)
        if return_code == 0:
            self.logger.info(message)
        else:
            self.logger.warning(message)

        # Flush any deferred file logs after the command has been logged
        self._flush_deferred_file_logs()

        if not self.disable_header:
            self.print_header()

    def _compose_capture_message(self, executed_cmd: List[str], return_code: int) -> str:
        parts: List[str] = [
            f"CM {' '.join(executed_cmd)} #> PWD={os.getenv('PWD')}",
            f"EXIT={return_code}",
        ]
        if self.trops_sid:
            parts.append(f"TROPS_SID={self.trops_sid}")
        if self.trops_env:
            parts.append(f"TROPS_ENV={self.trops_env}")
        if self.trops_tags:
            parts.append(f"TROPS_TAGS={self.trops_tags}")
        return ', '.join(parts)

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

    def _yum_log(self, executed_cmd: List[str]) -> None:

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

    def _apt_log(self, executed_cmd: List[str]) -> None:
        if 'apt' in executed_cmd and any(x in executed_cmd for x in ['upgrade', 'install', 'update', 'remove', 'autoremove']):
            self._update_pkg_list(' '.join(executed_cmd))
        # TODO: Add log trops git show hex

    def _update_pkg_list(self, args: str) -> None:

        # Update the pkg_List
        cmd = ['apt', 'list', '--installed']
        result = subprocess.run(cmd, capture_output=True)
        pkg_list = result.stdout.decode('utf-8').splitlines()
        pkg_list.sort()

        pkg_list_file = self.trops_dir + \
            f'/log/apt_pkg_list.{ self.hostname }'
        with open(pkg_list_file, 'w') as f:
            f.write('\n'.join(pkg_list))

        self.add_and_commit_file(pkg_list_file)

    def _add_file_in_git_repo(self, executed_cmd: List[str], start_index: int, first_line_comment: str = None) -> None:
        for file_arg in executed_cmd[start_index:]:
            file_path = absolute_path(file_arg)
            if not os.path.isfile(file_path):
                continue
            # Optionally prepend a comment line describing the source command (for tee outputs)
            if first_line_comment:
                try:
                    with open(file_path, 'r+', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if not content.startswith(first_line_comment):
                            f.seek(0)
                            f.write(first_line_comment + "\n" + content)
                except Exception:
                    try:
                        with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                            f.write(first_line_comment + "\n")
                    except Exception:
                        pass
            # Ignore if path is already tracked in another repo
            if file_is_in_a_git_repo(file_path):
                self.logger.info(
                    f"FL {file_path} is under a git repository #> PWD=*, EXIT=*, TROPS_SID={self.trops_sid}, TROPS_ENV={self.trops_env}")
                sys.exit(0)
            git_msg, log_note = self._generate_git_msg_and_log_note(file_path)
            result = self._add_and_commit_file(file_path, git_msg)
            if result.returncode == 0:
                msg = result.stdout.decode('utf-8').splitlines()[0]
                print(msg)
                self._add_file_log(file_path, log_note)
                # Push immediately after a successful commit if remote is set
                self._push_if_remote_set()
            else:
                print('No update')

    def _add_file_log(self, file_path: str, log_note: str) -> None:
        """Add an FL log entry"""
        rel_path = os.path.relpath(os.path.realpath(absolute_path(file_path)), start=os.path.realpath(self.work_tree))
        cmd = self.git_cmd + ['log', '--oneline', '-1', rel_path]
        output = subprocess.check_output(
            cmd).decode("utf-8").split()
        if rel_path in output:
            mode = oct(os.stat(file_path).st_mode)[-4:]
            owner = Path(file_path).owner()
            group = Path(file_path).group()
            message = f"FL trops show { output[0] }:{ rel_path }  #> { log_note }, O={ owner },G={ group },M={ mode }"
            if self.trops_sid:
                message += f" TROPS_SID={ self.trops_sid }"
            message += f" TROPS_ENV={ self.trops_env }"
            if self.trops_tags:
                message += f" TROPS_TAGS={self.trops_tags}"
            # Defer logging if requested so that command log comes first
            if getattr(self, '_defer_file_logs', False):
                self._deferred_file_logs.append(message)
            else:
                self.logger.info(message)

    def _add_and_commit_file(self, file_path: str, git_msg: str) -> subprocess.CompletedProcess:
        """Add a file in the git repo and commit if changed"""
        rel_path = os.path.relpath(os.path.realpath(absolute_path(file_path)), start=os.path.realpath(self.work_tree))
        subprocess.run(self.git_cmd + ['add', rel_path], capture_output=True)
        return subprocess.run(self.git_cmd + ['commit', '-m', git_msg, rel_path], capture_output=True)

    def _generate_git_msg_and_log_note(self, file_path: str) -> Tuple[str, str]:
        """Generate the git commit message and log note"""
        rel_path = os.path.relpath(os.path.realpath(absolute_path(file_path)), start=os.path.realpath(self.work_tree))
        result = subprocess.run(self.git_cmd + ['ls-files', rel_path], capture_output=True)
        is_tracked = bool(result.stdout.decode('utf-8'))
        git_msg = f"{'Update' if is_tracked else 'Add'} {rel_path}"
        log_note = 'UPDATE' if is_tracked else 'ADD'
        if self.trops_tags:
            git_msg = f"{git_msg} ({self.trops_tags})"
        return git_msg, log_note

    def _track_editor_files(self, executed_cmd: List[str]) -> None:
        """Detect common editors and add the edited file(s) to the repo if present."""

        # Remove sudo from executed_cmd (basic case)
        executed_cmd = self._sanitize_for_sudo(executed_cmd)

        # Check if editor is launched
        editors = ['vim', 'vi', 'nvim', 'emacs', 'nano']
        if executed_cmd[0] in editors:
            # Add the edited file in trops git
            self._add_file_in_git_repo(executed_cmd, 1)

    def _add_tee_output_file(self, executed_cmd: List[str]) -> bool:
        """Detect tee after one or more pipes and add the target file(s).

        Supported forms:
          - cmd | tee path/to/file
          - cmd |tee path/to/file
          - cmd1 | cmd2 | ... | tee path/to/file
        """
        # First normalize tokens so that every '|' is its own token
        normalized: List[str] = []
        for tok in executed_cmd:
            if '|' in tok and tok != '|':
                parts = re.split(r'(\|)', tok)
                normalized.extend([p for p in parts if p])
            else:
                normalized.append(tok)

        # Scan for the last occurrence of '|' followed by 'tee'
        last_pipe_index = -1
        for i in range(len(normalized) - 1):
            if normalized[i] == '|' and normalized[i + 1] == 'tee':
                last_pipe_index = i  # index of '|' just before tee

        if last_pipe_index != -1:
            # Determine the left-hand command (before the last pipe that precedes tee)
            left_cmd_tokens = normalized[:last_pipe_index]
            left_cmd = ' '.join(left_cmd_tokens).strip()
            comment = f"# {left_cmd}" if left_cmd else None
            # Start collecting path arguments after 'tee'
            tee_index = last_pipe_index + 1  # 'tee'
            self._add_file_in_git_repo(normalized, tee_index + 1, first_line_comment=comment)
            return True
        return False

    def _sanitize_for_sudo(self, executed_cmd: List[str]) -> List[str]:
        """Remove leading sudo if present. TODO: handle sudo options."""
        if executed_cmd and executed_cmd[0] == 'sudo':
            return executed_cmd[1:]
        return executed_cmd

    def _push_if_remote_set(self) -> None:
        """Push current branch if a git remote is configured.

        This is a no-op when:
          - no git_remote is configured
          - git_dir is missing or not a valid directory
          - git config file does not exist
        """
        if not getattr(self, 'git_remote', False):
            return
        if not hasattr(self, 'git_dir') or not isinstance(self.git_dir, str):
            return
        if not os.path.isdir(self.git_dir):
            return
        git_config_path = os.path.join(self.git_dir, 'config')
        if not os.path.isfile(git_config_path):
            return

        # Determine current branch
        result = subprocess.run(self.git_cmd + ['branch', '--show-current'], capture_output=True)
        current_branch = result.stdout.decode('utf-8').strip() if result.returncode == 0 else ''
        if not current_branch:
            return

        git_conf = ConfigParser()
        git_conf.read(git_config_path)

        # Ensure origin exists
        if not git_conf.has_option('remote "origin"', 'url'):
            subprocess.call(self.git_cmd + ['remote', 'add', 'origin', self.git_remote])

        # Set upstream if missing, else regular push
        if not git_conf.has_option(f'branch "{current_branch}"', 'remote'):
            cmd = self.git_cmd + ['push', '--set-upstream', 'origin', current_branch]
        else:
            cmd = self.git_cmd + ['push']
        subprocess.call(cmd)

def capture_cmd(args, other_args):

    tc = TropsCapCmd(args, other_args)
    tc.capture_cmd()

def add_capture_cmd_subparsers(subparsers):

    parser_capture_cmd = subparsers.add_parser(
        'capture-cmd', help='Capture command line strings', add_help=False)
    parser_capture_cmd.add_argument(
        'return_code', type=int, help='return code')
    parser_capture_cmd.set_defaults(handler=capture_cmd)

def file_is_in_a_git_repo(file_path: str) -> bool:
    parent_dir = os.path.dirname(file_path) or '.'
    # Use git -C to avoid changing global working directory
    result = subprocess.run(['git', '-C', parent_dir, 'rev-parse', '--is-inside-work-tree'], capture_output=True)
    return result.returncode == 0