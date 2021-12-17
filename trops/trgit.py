import os
import sys
import subprocess
import configparser
import distutils.util

def main():
    config = configparser.ConfigParser()
    conf_file = '$HOME/.config/trops/trops.cfg'
    config.read(os.path.expandvars(conf_file))

    sudo = distutils.util.strtobool(config['defaults']['sudo'])
    git_dir = os.path.expandvars(config['defaults']['git_dir'])
    work_tree = os.path.expandvars(config['defaults']['work_tree'])

    cmd = ['/usr/bin/git', '--git-dir=' + git_dir, '--work-tree=' + work_tree ]
    if sudo: cmd = ['sudo'] + cmd
    cmd = cmd + sys.argv[1:]
    subprocess.call(cmd)

if __name__ == "__main__":
    main()
