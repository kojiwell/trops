import os
import sys
import subprocess
import argparse
import configparser
import distutils.util
from datetime import datetime

class Trops:

    def __init__(self):

        self.config = configparser.ConfigParser()
        self.conf_file = '$TROPS_DIR/trops.cfg'
        self.config.read(os.path.expandvars(self.conf_file))

    def _check(self):
    
        if 'TROPS_DIR' not in os.environ:
            messages = ['TROPS_DIR is not set',
                        '',
                        ' > source <project>/trops/tropsrc',
                        '']
            print('\n'.join(messages))
            exit(1)


    def git(self, args, unknown):

        self._check()
        sudo = distutils.util.strtobool(self.config['defaults']['sudo'])
        git_dir = os.path.expandvars(self.config['defaults']['git_dir'])
        work_tree = os.path.expandvars(self.config['defaults']['work_tree'])

        cmd = ['git', '--git-dir=' + git_dir, '--work-tree=' + work_tree ]
        if sudo: cmd = ['sudo'] + cmd
        cmd = cmd + unknown
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
                            aligned_line.append("{}  {}".format(timestamp, ' '.join(cmd)))
                        timestamp = datetime.fromtimestamp(int(items[0][1:])).strftime("%Y-%m-%d_%H:%M:%S")
                        cmd = []
                    else:
                        cmd += items
                line = f.readline()
        return aligned_line

    def _gitlog(self):
 
        cmd = ['trops', 'git', 'log', '--oneline', '--pretty=format:%cd  trgit show %h #%d %s <%an>', '--date=format:%Y-%m-%d_%H:%M:%S']
        output = subprocess.check_output(cmd)
        return output.decode("utf-8").splitlines()
    
    def log(self, args, unknown):
        output = self._history() + self._gitlog()
        output.sort()
        verbose = False
        for l in output:
            print(l)
            if 'trops git show' in l and verbose:
                cmd = l.split()[1:4]
                subprocess.call(cmd)

    def main(self):

        parser = argparse.ArgumentParser(description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        parser_edit = subparsers.add_parser('edit', help='see `edit -h`')
        parser_edit.add_argument("-e", "--editor", default="vim", help="editor")
        parser_edit.set_defaults(handler=self.edit)
        parser_git = subparsers.add_parser('git', help='see `git -h`')
        parser_git.set_defaults(handler=self.git)
        parser_log = subparsers.add_parser('log', help='see `log -h`')
        parser_log.set_defaults(handler=self.log)

        args, unknown = parser.parse_known_args()
        if hasattr(args, 'handler'):
            args.handler(args, unknown)
        else:
            parser.print_help()


def main():

    tr = Trops()
    tr.main()

if __name__ == "__main__":
    main()
