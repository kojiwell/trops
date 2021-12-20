import os
import sys
import subprocess
import configparser
import distutils.util

class Trops:

    def __init__(self):

        self.config = configparser.ConfigParser()
        self.conf_file = '$TROPS_DIR/trops.cfg'
        self.config.read(os.path.expandvars(self.conf_file))

    def check(self):
    
        if 'TROPS_DIR' not in os.environ:
            messages = ['TROPS_DIR is not set',
                        '',
                        ' > source <project>/trops/tropsrc',
                        '']
            print('\n'.join(messages))
            exit(1)


    def trgit(self):

        self.check()
        sudo = distutils.util.strtobool(self.config['defaults']['sudo'])
        git_dir = os.path.expandvars(self.config['defaults']['git_dir'])
        work_tree = os.path.expandvars(self.config['defaults']['work_tree'])

        cmd = ['/usr/bin/git', '--git-dir=' + git_dir, '--work-tree=' + work_tree ]
        if sudo: cmd = ['sudo'] + cmd
        cmd = cmd + sys.argv[1:]
        subprocess.call(cmd)

    def tredit(self):
        cmd = ['vim']
        cmd = cmd + sys.argv[1:]

        subprocess.call(cmd)
        for f in sys.argv[1:]:
            if os.path.isfile(f):
                cmd = ['trgit', 'add', f]
                subprocess.call(cmd)
                cmd = ['trgit', 'commit', '-m', 'Update ' + f, f]
                subprocess.call(cmd)


def trgit():

    tr = Trops()
    tr.trgit()

def tredit():

    tr = Trops()
    tr.tredit()

def main():

    print("This is trops main function")

if __name__ == "__main__":
    main()
