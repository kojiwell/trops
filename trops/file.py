import os
import subprocess
import distutils.util
from configparser import ConfigParser

from trops.utils import real_path


class TropsFile:

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

            if 'git_remote' in self.config[self.trops_env]:
                self.git_remote = self.config[self.trops_env]['git_remote']

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

    def list(self):

        os.chdir(self.work_tree)
        cmd = self.git_cmd + ['ls-files']
        subprocess.call(cmd)

    def put(self):

        cmd = self.git_cmd + ['checkout', self.path]
        subprocess.call(cmd)


def file_list(args, other_args):

    tf = TropsFile(args, other_args)
    tf.list()


def file_put(args, other_args):

    tf = TropsFile(args, other_args)
    tf.put()


def add_file_subparsers(subparsers):

    # trops file
    parser_file = subparsers.add_parser(
        'file', help='track file operations')
    parser_file.add_argument(
        '-e', '--env', help='Set environment name')
    file_subparsers = parser_file.add_subparsers()
    # trops file list
    parser_file_list = file_subparsers.add_parser(
        'list', help='list files')
    parser_file_list.set_defaults(handler=file_list)
    # trops file put
    parser_file_put = file_subparsers.add_parser(
        'put', help='put file')
    parser_file_put.add_argument(
        'path', help='file/dir path')
    parser_file_put.add_argument(
        'dest', help='dest path where you put the file/dir')
    parser_file_put.set_defaults(handler=file_put)
