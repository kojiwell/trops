import os
import sys
import subprocess
import argparse
import configparser
import distutils.util
from textwrap import dedent
from datetime import datetime


class Trops:

    def __init__(self):

        self.config = configparser.ConfigParser()
        self.conf_file = '$TROPS_DIR/trops.cfg'
        self.config.read(os.path.expandvars(self.conf_file))

    def initialize(self, args, unkown):

        if not os.path.isdir(args.dir):
            print(f"{ args.dir } doe not exist")
            exit(1)

        trops_dir = args.dir + '/trops'
        trops_rcfile = trops_dir + '/tropsrc'
        trops_conf = trops_dir + '/trops.cfg'
        trops_git_dir = trops_dir + '/trops.git'

        if not os.path.isdir(trops_dir):
            os.mkdir(trops_dir)

        if not os.path.isfile(trops_rcfile):
            with open(trops_rcfile, mode='w') as f:
                default_rcfile = """\
                    export TROPS_DIR=$(dirname $(realpath $BASH_SOURCE))
                    
                    shopt -s histappend
                    PROMPT_COMMAND="history -a;$PROMPT_COMMAND"
                    
                    alias tredit="trops edit"
                    alias trvim="trops edit --editor=vim"
                    alias trgit="trops git"
                    alias trlog="trops log"
                    """
                f.write(dedent(default_rcfile))
        if not os.path.isfile(trops_conf):
            with open(trops_conf, mode='w') as f:
                default_conf = """\
                    [defaults]
                    git_dir = $TROPS_DIR/trops.git
                    sudo = False
                    work_tree = /
                    """
                f.write(dedent(default_conf))
        if not os.path.isdir(trops_git_dir):
            cmd = ['git', 'init', '--bare', trops_git_dir]
            subprocess.call(cmd)

        with open(trops_git_dir + '/config', mode='r') as f:
            if 'showUntrackedFiles = no' not in f.read():
                cmd = ['git', '--git-dir=' + trops_git_dir, 'config',
                       '--local', 'status.showUntrackedFiles', 'no']
                subprocess.call(cmd)

        cmd = ['git', '--git-dir=' + trops_git_dir, 'branch', '--show-current']
        branch_name = subprocess.check_output(cmd).decode("utf-8")
        if 'trops' not in branch_name:
            cmd = ['git', '--git-dir=' + trops_git_dir, '--work-tree=/',
                   'checkout', '-b', 'trops']
            subprocess.call(cmd)

    def _check(self):

        if 'TROPS_DIR' not in os.environ:
            message = """\
                TROPS_DIR is not set

                    > source <project>/trops/tropsrc
                """
            print(dedent(message))
            exit(1)

    def git(self, args, other_args):

        self._check()
        sudo = distutils.util.strtobool(self.config['defaults']['sudo'])
        git_dir = os.path.expandvars(self.config['defaults']['git_dir'])
        work_tree = os.path.expandvars(self.config['defaults']['work_tree'])

        cmd = ['git', '--git-dir=' + git_dir, '--work-tree=' + work_tree]
        if sudo:
            cmd = ['sudo'] + cmd
        cmd = cmd + other_args
        subprocess.call(cmd)

    def edit(self, args, edited_files):

        cmd = [args.editor]
        cmd = cmd + edited_files

        subprocess.call(cmd)
        for f in edited_files:
            if os.path.isfile(f):
                git_vars = ['add', f]
                self.git(args, git_vars)
                git_vars = ['commit', '-m', 'Update ' + f, f]
                self.git(args, git_vars)

    def _history(self):

        if 'HISTFILE' in os.environ:
            filename = os.path.expandvars("$HISTFILE")
        else:
            filename = os.path.expandvars("$HOME/.bash_history")
        with open(filename) as f:
            line = f.readline()
            aligned_line = []
            timestamp = ''
            cmd = []
            while line:
                items = line.split()
                if items:
                    if items[0][0] == '#' and len(items[0]) == 11:
                        if timestamp and cmd:
                            aligned_line.append(
                                "{}  {}".format(timestamp, ' '.join(cmd)))
                        timestamp = datetime.fromtimestamp(
                            int(items[0][1:])).strftime("%Y-%m-%d_%H:%M:%S")
                        cmd = []
                    else:
                        cmd += items
                line = f.readline()
        return aligned_line

    def _gitlog(self):

        cmd = ['trops', 'git', 'log', '--oneline',
               '--pretty=format:%cd  trgit show %h #%d %s <%an>', '--date=format:%Y-%m-%d_%H:%M:%S']
        output = subprocess.check_output(cmd)
        return output.decode("utf-8").splitlines()

    def log(self, args, other_args):
        output = self._history() + self._gitlog()
        output.sort()
        verbose = False
        for l in output:
            print(l)
            if 'trops git show' in l and verbose:
                cmd = l.split()[1:4]
                subprocess.call(cmd)

    def main(self):

        parser = argparse.ArgumentParser(
            description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        parser_init = subparsers.add_parser('init', help='see `init -h`')
        parser_init.set_defaults(handler=self.initialize)
        parser_init.add_argument("dir", help="Initialize Trops")
        parser_edit = subparsers.add_parser('edit', help='see `edit -h`')
        parser_edit.add_argument(
            "-e", "--editor", default="vim", help="editor")
        parser_edit.set_defaults(handler=self.edit)
        parser_git = subparsers.add_parser('git', help='see `git -h`')
        parser_git.set_defaults(handler=self.git)
        parser_log = subparsers.add_parser('log', help='see `log -h`')
        parser_log.set_defaults(handler=self.log)

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
