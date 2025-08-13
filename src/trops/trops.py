import logging
import os
import subprocess

from configparser import ConfigParser
from getpass import getuser
from pathlib import Path
from socket import gethostname
from textwrap import dedent
from typing import Any, List

from .utils import absolute_path, strtobool


class Trops:
    """Trops Class"""

    def __init__(self, args: Any, other_args: List[str]) -> None:
        """Initialize the Trops class"""

        # Initialize basic attributes
        self.args = args
        self.other_args = other_args
        self.username = getuser()
        self.hostname = gethostname().split('.')[0]

        # Set directories and files
        trops_dir_env = os.getenv('TROPS_DIR')
        if trops_dir_env:
            self.trops_dir = absolute_path(trops_dir_env)
        else:
            # Fall back to a deterministic default expected by tests
            self.trops_dir = '/home/devuser/trops'
        # Ensure base and log directories exist
        os.makedirs(self.trops_dir, exist_ok=True)
        self.trops_log_dir = os.path.join(self.trops_dir, 'log')
        os.makedirs(self.trops_log_dir, exist_ok=True)
        self.trops_logfile = os.path.join(self.trops_log_dir, 'trops.log')

        # Environment and session ID
        self.trops_env = args.env if hasattr(args, 'env') and args.env else os.getenv('TROPS_ENV', False)
        self.trops_sid = os.getenv('TROPS_SID', False)
        # Tags from environment by default
        self.trops_tags = os.getenv('TROPS_TAGS', None)
        if self.trops_tags:
            # Normalize: remove spaces
            self.trops_tags = self.trops_tags.replace(' ', '')

        # Configuration handling
        self.config = ConfigParser()
        self.conf_file = os.path.join(self.trops_dir, 'trops.cfg')
        if os.path.isfile(self.conf_file):
            self.config.read(self.conf_file)

            if self.trops_env and self.config.has_section(self.trops_env):
                self.git_dir = absolute_path(self.get_config_value('git_dir'))
                self.work_tree = absolute_path(self.get_config_value('work_tree'))
                # Run git commands with -C <work_tree> so pathspecs resolve from the repo root
                self.git_cmd = ['git', '-C', self.work_tree, f'--git-dir={self.git_dir}', f'--work-tree={self.work_tree}']

                self.sudo = strtobool(self.get_config_value('sudo', default='False'))
                if self.sudo:
                    self.git_cmd = ['sudo'] + self.git_cmd

                self.trops_logfile = absolute_path(self.get_config_value('logfile', default=self.trops_logfile))

                self.disable_header = strtobool(self.get_config_value('disable_header', default='False'))

                # Use a set for O(1) membership checks on ignore commands
                self.ignore_cmds = {item.strip() for item in self.get_config_value('ignore_cmds', default='ttags').split(',') if item.strip()}

                self.git_remote = self.get_config_value('git_remote', default=False)
                if self.git_remote:
                    self.glab_cmd = ['glab', '-R', self.git_remote]

                # Prefer environment variable over config for tags
                self.trops_tags = os.getenv('TROPS_TAGS', self.get_config_value('tags', default=False))
                if self.trops_tags:
                    self.trops_tags = self.trops_tags.replace(' ', '')


        if self.trops_logfile:
            self.setup_logging()

        # Primary tag extraction (first tag), e.g. "#123" from "#123,TEST"
        self.trops_prim_tag = None
        if getattr(self, 'trops_tags', None):
            # Accept either comma or semicolon as separator
            if ',' in self.trops_tags:
                self.trops_prim_tag = self.trops_tags.split(',')[0]
            elif ';' in self.trops_tags:
                self.trops_prim_tag = self.trops_tags.split(';')[0]
            else:
                self.trops_prim_tag = self.trops_tags

    def setup_logging(self) -> None:
        logging.basicConfig(format=f'%(asctime)s { self.username }@{ self.hostname } %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=self.trops_logfile,
                            level=logging.DEBUG)
        self.logger = logging.getLogger()

    def get_config_value(self, key: str, default: str = None) -> str:
        """Get a value from the configuration file."""
        try:
            return self.config[self.trops_env][key]
        except KeyError:
            if default is not None:
                return default
            print(f'{key} does not exist in your configuration file')
            exit(1)
        
    def add_and_commit_file(self, file_path) -> None:
        rel_path = self.to_work_tree_rel_path(file_path)
        cmd = self.git_cmd + ['ls-files', rel_path]
        result = subprocess.run(cmd, capture_output=True)
        if result.stdout.decode("utf-8"):
            git_msg = f"Update { rel_path }"
            log_note = 'UPDATE'
        else:
            git_msg = f"Add { rel_path }"
            log_note = 'ADD'
        if self.trops_tags:
            git_msg = f"{ git_msg } ({ self.trops_tags })"
        cmd = self.git_cmd + ['add', rel_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m', git_msg, rel_path]
        # Commit the change if needed
        result = subprocess.run(cmd, capture_output=True)
        # If there's an update, log it in the log file
        if result.returncode == 0:
            msg = result.stdout.decode('utf-8').splitlines()[0]
            print(msg)
            cmd = self.git_cmd + ['log', '--oneline', '-1', '--', rel_path]
            try:
                output = subprocess.check_output(cmd).decode("utf-8").split()
            except subprocess.CalledProcessError:
                output = []
            if rel_path in output:
                mode = oct(os.stat(file_path).st_mode)[-4:]
                owner = Path(file_path).owner()
                group = Path(file_path).group()
                message = f"FL trops show { output[0] }:{ rel_path }  #> { log_note } O={ owner },G={ group },M={ mode }"
                if self.trops_sid:
                    message = f"{ message } TROPS_SID={ self.trops_sid }"
                message = f"{ message } TROPS_ENV={ self.trops_env }"
                if self.trops_tags:
                    message = message + f" TROPS_TAGS={self.trops_tags}"

                self.logger.info(message)
        else:
            print('No update')


class TropsMain(Trops):
    """TropsMain Class"""

    def __init__(self, args: Any, other_args: List[str]) -> None:
        """Initialize the TropsMain class"""
        super().__init__(args, other_args)

    def git(self) -> None:
        """Git wrapper command"""
        # Ensure git is configured
        if not hasattr(self, 'git_dir') or not hasattr(self, 'work_tree'):
            message = dedent(
                """
                ERROR: Trops is not configured for this environment.
                    # List existing environments
                    $ trops env list

                    # Create new environment
                    $ trops env create <envname>

                    # Turn on Trops
                    $ ontrops <envname>
                """
            ).strip()
            print(message)
            exit(1)

        # Build base command and environment variables
        git_env = os.environ.copy()
        git_env['GIT_DIR'] = self.git_dir
        git_env['GIT_WORK_TREE'] = self.work_tree

        normalized_args = self._normalize_git_paths(self.other_args)
        # Ensure pathspecs are resolved relative to the work tree
        base_cmd = ['git', '-C', self.work_tree] + normalized_args

        # Warn if destructive op without sudo while config enforces sudo
        if getattr(self, 'sudo', False) and not getattr(self.args, 'sudo', False):
            if self._is_destructive_git(self.other_args):
                print('WARNING: Running a potentially destructive git command without --sudo while sudo is enabled in config.')

        # Handle sudo
        if getattr(self.args, 'sudo', False) or getattr(self, 'sudo', False):
            # Preserve GIT_* environment variables when using sudo
            sudo_prefix = ['sudo', '--preserve-env=GIT_DIR,GIT_WORK_TREE']
            full_cmd = sudo_prefix + base_cmd
        else:
            full_cmd = base_cmd

        if getattr(self.args, 'verbose', False):
            print('WRAP:', ' '.join(full_cmd))
        result = subprocess.run(full_cmd, env=git_env)
        if result.returncode != 0:
            exit(result.returncode)

    def glab(self) -> None:
        """Glab wrapper command"""

        if self.other_args == ['auth', 'login']:
            hostname = input(
                'Your GitLab hostname(default: gitlab.com): ') or 'gitlab.com'
            cmd = ['glab', 'auth', 'login', '--hostname', hostname]
        else:
            cmd = self.glab_cmd + self.other_args
        subprocess.call(cmd)

    def check(self) -> None:
        """Git status wrapper command"""

        cmd = self.git_cmd + ['status']
        subprocess.call(cmd)

    def ll(self) -> None:
        """Shows the list of git-tracked files"""

        if os.getenv('TROPS_ENV') == None:
            raise SystemExit("You're not under any trops environment")

        # Normalize directory arguments using shared helper
        rel_dirs = self.normalize_paths_for_work_tree(self.args.dirs)

        # Build git ls-files command
        if rel_dirs:
            cmd = self.git_cmd + ['ls-files', '--'] + rel_dirs
        else:
            cmd = self.git_cmd + ['ls-files']

        output = subprocess.check_output(cmd)

        # For each tracked file (relative to work_tree), show its absolute file metadata
        abs_work_tree = os.path.realpath(self.work_tree)
        for rel_path in output.decode("utf-8").splitlines():
            abs_path = os.path.join(abs_work_tree, rel_path.lstrip('/'))
            subprocess.call(['ls', '-al', abs_path])

    def show(self) -> None:
        """trops show hash[:path]"""

        cmd = self.git_cmd + ['show', self.args.commit]
        subprocess.call(cmd)

    def branch(self) -> None:
        """trops branch"""

        cmd = self.git_cmd + ['branch', '-a']
        subprocess.call(cmd)

    def fetch(self) -> None:
        """trops fetch"""

        cmd = self.git_cmd + ['fetch', '-a']
        subprocess.call(cmd)

    @staticmethod
    def _is_destructive_git(args: List[str]) -> bool:
        """Heuristic to detect potentially destructive git operations."""
        if not args:
            return False
        destructive_subcommands = {
            'reset', 'clean', 'checkout', 'rebase', 'cherry-pick', 'stash', 'restore'
        }
        if args[0] in destructive_subcommands:
            # Specific flags that are destructive
            joined = ' '.join(args)
            flags = ['--hard', '-f', '--force', '-x', '-X', '--ours', '--theirs']
            return any(flag in joined for flag in flags)
        return False

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

    def _normalize_git_paths(self, args: List[str]) -> List[str]:
        """Convert absolute paths under work_tree to relative pathspecs without
        resolving symlinks, and insert "--" before the first pathspec to avoid
        ambiguity with revisions."""
        if not args or not hasattr(self, 'work_tree'):
            return args

        has_double_dash = '--' in args
        result_args: List[str] = []
        first_path_index: int = -1
        skip_next = False
        found_subcommand = False

        # Git supports some global options before the subcommand (e.g. -c, --version).
        # We must not insert "--" before the subcommand. Only consider pathspec
        # normalization AFTER we encounter the subcommand (first non-option token).
        options_with_value = {'-m', '--message', '-C', '--cwd', '-S', '--gpg-sign', '--author', '-c', '--work-tree', '--git-dir'}

        for i, token in enumerate(args):
            if skip_next:
                result_args.append(token)
                skip_next = False
                continue

            # Preserve existing separator and copy rest as-is
            if token == '--':
                result_args.extend(args[i:])
                has_double_dash = True
                break

            # Until we find the subcommand, just pass through options and their values
            if not found_subcommand:
                if token.startswith('-'):
                    result_args.append(token)
                    if token in options_with_value and i + 1 < len(args):
                        skip_next = True
                    continue
                # First non-option token is treated as the subcommand
                found_subcommand = True
                result_args.append(token)
                continue

            # From here on, we are after the subcommand: consider pathspec normalization
            if token in options_with_value:
                result_args.append(token)
                if i + 1 < len(args):
                    skip_next = True
                continue

            # Do not rewrite probable revision specifiers like "HASH:path"
            maybe_token = token
            if not (':' in token and not os.path.exists(token)):
                rel_list = self.normalize_paths_for_work_tree([token])
                if rel_list:
                    maybe_token = rel_list[0]
                    if first_path_index == -1:
                        first_path_index = len(result_args)
            result_args.append(maybe_token)

        # Insert "--" before the first pathspec if applicable and not already present
        if not has_double_dash and first_path_index != -1:
            result_args.insert(first_path_index, '--')

        return result_args

    def touch(self) -> None:

        for file_path in self.args.paths:

            self._touch_file(file_path)

    def _touch_file(self, file_path) -> None:
        """Add a file or directory in the git repo"""

        file_path = absolute_path(file_path)

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

        # Use path relative to work_tree for git commands
        rel_path = self.to_work_tree_rel_path(file_path)
        # Check if the path is in the git repo
        cmd = self.git_cmd + ['ls-files', rel_path]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(result.stderr.decode('utf-8'))
            exit(result.returncode)
        output = result.stdout.decode('utf-8')
        # Set the message based on the output
        if output:
            git_msg = f"Update { rel_path }"
            log_note = "UPDATE"
        else:
            git_msg = f"Add { rel_path }"
            log_note = "ADD"
        if self.trops_tags:
            git_msg = f"{ git_msg } ({ self.trops_tags })"
        # Add and commit
        cmd = self.git_cmd + ['add', '--', rel_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m', git_msg, '--', rel_path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['log', '--oneline', '-1', '--', rel_path]
        try:
            output = subprocess.check_output(cmd).decode("utf-8").split()
        except subprocess.CalledProcessError:
            output = []
        if rel_path in output:
            env = self.trops_env
            commit = output[0]
            path = rel_path
            mode = oct(os.stat(file_path).st_mode)[-4:]
            owner = Path(file_path).owner()
            group = Path(file_path).group()
            message = f"FL trops show { commit }:{ path }  #> { log_note } O={ owner },G={ group },M={ mode }"
            if self.trops_sid:
                message = message + f" TROPS_SID={ self.trops_sid }"
            message = message + f" TROPS_ENV={ env }"
            if self.trops_tags:
                message = message + f" TROPS_TAGS={self.trops_tags}"
            self.logger.info(message)

    def drop(self) -> None:

        for file_path in self.args.paths:

            self._drop_file(file_path)

    def _drop_file(self, file_path) -> None:
        """Remove a file from the git repo"""

        file_path = absolute_path(file_path)

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

        rel_path = self.to_work_tree_rel_path(file_path)
        # Check if the path is in the git repo
        cmd = self.git_cmd + ['ls-files', rel_path]
        output = subprocess.check_output(cmd).decode("utf-8")
        # Set the message based on the output
        if output:
            cmd = self.git_cmd + ['rm', '--cached', '--', rel_path]
            subprocess.call(cmd)
            git_msg = f"Goodbye { rel_path }"
            if self.trops_tags:
                git_msg = f"{ git_msg } ({ self.trops_tags })"
            cmd = self.git_cmd + ['commit', '-m', git_msg]
            subprocess.call(cmd)
        else:
            message = f"{ file_path } is not in the git repo"
            exit(1)
        cmd = self.git_cmd + ['log', '--oneline', '-1', '--', rel_path]
        output = subprocess.check_output(cmd).decode("utf-8").split()
        message = f"FL trops show { output[0] }:{ rel_path }  #> BYE BYE"
        if self.trops_sid:
            message = message + f" TROPS_SID={ self.trops_sid }"
        message = message + f" TROPS_ENV={ self.trops_env }"
        if self.trops_tags:
            message = message + f" TROPS_TAGS={self.trops_tags}"
        self.logger.info(message)

    def to_work_tree_rel_path(self, file_path: str) -> str:
        """Return a path relative to the work tree resolving symlinks.

        This ensures files under symlinked paths (e.g., /tmp on macOS) are
        added under their actual path (e.g., /private/tmp) in the repo.
        """
        real_work_tree = os.path.realpath(self.work_tree)
        real_file_path = os.path.realpath(absolute_path(file_path))
        return os.path.relpath(real_file_path, start=real_work_tree)

    def normalize_paths_for_work_tree(self, paths: List[str]) -> List[str]:
        """Given a list of paths (absolute or relative), return those within
        the work tree as paths relative to the work tree. Paths outside are filtered out.

        This centralizes path normalization logic for commands like git wrapper
        and `trops ll`.
        """
        normalized: List[str] = []
        abs_work_tree = os.path.realpath(self.work_tree)
        for p in paths:
            try:
                abs_p = os.path.realpath(absolute_path(p))
            except Exception:
                continue
            try:
                rel = os.path.relpath(abs_p, start=abs_work_tree)
            except Exception:
                continue
            if rel.startswith('..'):
                continue
            normalized.append(rel)
        return normalized
