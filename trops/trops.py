import os
import sys
import subprocess
import argparse
import configparser
import distutils.util

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

        cmd = ['/usr/bin/git', '--git-dir=' + git_dir, '--work-tree=' + work_tree ]
        if sudo: cmd = ['sudo'] + cmd
        cmd = cmd + unknown
        subprocess.call(cmd)

    def edit(self, args, edited_files):
        cmd = [args.editor]
        cmd = cmd + edited_files

        subprocess.call(cmd)
        for f in edited_files:
            if os.path.isfile(f):
                cmd = ['trops', 'git', 'add', f]
                subprocess.call(cmd)
                cmd = ['trops', 'git', 'commit', '-m', 'Update ' + f, f]
                subprocess.call(cmd)

    def main(self):

        parser = argparse.ArgumentParser(description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        parser_edit = subparsers.add_parser('edit', help='see `edit -h`')
        parser_edit.add_argument("-e", "--editor", default="vim", help="editor")
        parser_edit.set_defaults(handler=self.edit)
        parser_git = subparsers.add_parser('git', help='see `git -h`')
        parser_git.set_defaults(handler=self.git)

        args, unknown = parser.parse_known_args()
        #args.handler(args, unknown)
        #args = parser.parse_args()
        if hasattr(args, 'handler'):
            args.handler(args, unknown)
        else:
            parser.print_help()


def main():

    tr = Trops()
    tr.main()

if __name__ == "__main__":
    main()
