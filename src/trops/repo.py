import os
import subprocess
import distutils.util
from configparser import ConfigParser

from trops.utils import real_path


class TropsRepo:

    def __init__(self, args, other_args):

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
            try:
                self.git_remote = self.config[self.trops_env]['git_remote']
            except KeyError:
                print('git_remote does not exist in your configuration file')
                exit(1)

            # trops file put <path> <dest>
            if hasattr(args, 'path'):
                self.path = args.path
            if hasattr(args, 'dest'):
                # Make sure destination(dest) is a directory
                if os.path.isdir(args.dest):
                    # Change work_tree from orginal to args.dest
                    self.work_tree = real_path(args.dest)
                else:
                    print(f"ERROR: '{ args.dest }' is not a directory")
                    exit(1)

            self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                            '--work-tree=' + self.work_tree]

            sudo_true = distutils.util.strtobool(
                self.config[self.trops_env]['sudo'])
            if sudo_true:
                self.git_cmd = ['sudo'] + self.git_cmd

    def push(self):

        git_conf = ConfigParser()
        git_conf.read(self.git_dir + '/config')
        if not git_conf.has_option('remote "origin"', 'url'):
            cmd = self.git_cmd + ['remote', 'add', 'origin', self.git_remote]
            subprocess.call(cmd)
        if not git_conf.has_option(f'branch "trops_{ self.trops_env }"', 'remote'):
            cmd = self.git_cmd + \
                ['push', '--set-upstream', 'origin',
                    f'trops_{ self.trops_env }']
        else:
            cmd = self.git_cmd + ['push']
        subprocess.call(cmd)

    def pull(self):
        """trops repo pull"""

        pull_work_tree = f'{self.trops_dir}/files/{self.trops_env}'
        if not os.path.isdir(pull_work_tree):
            os.makedirs(pull_work_tree, exist_ok=True)
        self.git_dir = os.path.expandvars(
            self.config[self.trops_env]['git_dir'])
        self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                        f'--work-tree={pull_work_tree}']

        os.chdir(pull_work_tree)
        cmd = self.git_cmd + ['pull']
        subprocess.call(cmd)

    def clone(self):

        clone_work_tree = f'{self.trops_dir}/files/{self.trops_env}'
        if not os.path.isdir(clone_work_tree):
            os.makedirs(clone_work_tree, exist_ok=True)
        self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                        f'--work-tree={clone_work_tree}']

        # git clone --bare -b <git_remote> <git_dir>
        cmd = ['git', 'clone', '--bare', '-b', f'trops_{ self.trops_env }',
               f'{self.git_remote}', self.git_dir]
        subprocess.call(cmd)

        os.chdir(clone_work_tree)
        cmd = self.git_cmd + ['checkout']
        subprocess.call(cmd)


def repo_push(args, other_args):

    tf = TropsRepo(args, other_args)
    tf.push()


def repo_pull(args, other_args):

    tf = TropsRepo(args, other_args)
    tf.pull()


def repo_clone(args, other_args):

    tf = TropsRepo(args, other_args)
    tf.clone()


def add_repo_subparsers(subparsers):

    # trops file
    parser_repo = subparsers.add_parser(
        'repo', help='track file operations')
    parser_repo.add_argument(
        '-e', '--env', help='Set environment name')
    repo_subparsers = parser_repo.add_subparsers()
    # trops repo push
    parser_repo_push = repo_subparsers.add_parser(
        'push', help='push repo')
    parser_repo_push.set_defaults(handler=repo_push)
    # trops repo pull
    parser_repo_pull = repo_subparsers.add_parser(
        'pull', help='pull repo')
    parser_repo_pull.set_defaults(handler=repo_pull)
    # trops file push
    parser_repo_clone = repo_subparsers.add_parser(
        'clone', help='clone repo')
    parser_repo_clone.set_defaults(handler=repo_clone)
