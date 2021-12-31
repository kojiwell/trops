import os
import sys
import subprocess
import argparse
import distutils.util
from configparser import ConfigParser
from textwrap import dedent
from datetime import datetime


class Trops:
    """Trops Class"""

    def __init__(self):

        self.config = ConfigParser()
        self.trops_dir = os.path.expandvars('$TROPS_DIR')
        self.conf_file = self.trops_dir + '/trops.cfg'
        if os.path.isfile(self.conf_file):
            self.config.read(self.conf_file)
            try:
                self.git_dir = os.path.expandvars(
                    self.config['defaults']['git_dir'])
            except KeyError:
                print('git_dir does not exist in your configuration file')
                exit(1)
            try:
                self.work_tree = os.path.expandvars(
                    self.config['defaults']['work_tree'])
            except NoSectionError or NoOptionError:
                print('work_tree does not exist in your configuration file')
                exit(1)
            try:
                self.sudo = distutils.util.strtobool(
                    self.config['defaults']['sudo'])
            except NoSectionError or NoOptionError:
                pass
            self.git_cmd = ['git', '--git-dir=' + self.git_dir,
                            '--work-tree=' + self.work_tree]
            if self.sudo:
                self.git_cmd = ['sudo'] + self.git_cmd

    def initialize(self, args, unkown):
        """Setup trops project"""

        # TODO: Return error when trops init is executed
        # at an already initialized project directory
        # TODO: Decide how to handle history by default or
        # add option about history

        if not os.path.isdir(args.dir):
            print(f"{ args.dir } doe not exist")
            exit(1)

        # TODO: All or some of these variables should be
        # set in the __init__()
        trops_dir = args.dir + '/trops'
        trops_rcfile = trops_dir + '/tropsrc'
        trops_conf = trops_dir + '/trops.cfg'
        trops_git_dir = trops_dir + '/trops.git'

        # Create the directory if it doesn't exist
        if not os.path.isdir(trops_dir):
            os.mkdir(trops_dir)

        # Create TROPS_DIR/history
        history_dir = trops_dir + '/history'
        if not os.path.isdir(history_dir):
            os.mkdir(history_dir)

        # Create tropsrc file if it doesn't exist
        if not os.path.isfile(trops_rcfile):
            with open(trops_rcfile, mode='w') as f:
                default_rcfile = """\
                    export TROPS_DIR=$(dirname $(realpath $BASH_SOURCE))

                    shopt -s histappend
                    export HISTCONTROL=ignoreboth:erasedups
                    # export HISTFILE="$TROPS_DIR/history/${USER}@${HOSTNAME}"
                    PROMPT_COMMAND="history -a;$PROMPT_COMMAND"

                    alias tredit="trops edit"
                    alias trvim="trops edit --editor=vim"
                    alias trgit="trops git"
                    alias trlog="trops log"
                    alias trtouch="trops touch"
                    """
                f.write(dedent(default_rcfile))

        # TODO: Maybe "sudo = False" should be "sudo_git = False"?
        # Create trops.cfg file if it doesn't exists
        if not os.path.isfile(trops_conf):
            with open(trops_conf, mode='w') as f:
                default_conf = f"""\
                    [defaults]
                    git_dir = $TROPS_DIR/trops.git
                    sudo = False
                    work_tree = { args.work_tree }
                    """
                f.write(dedent(default_conf))

        # Create trops's bare git directory
        if not os.path.isdir(trops_git_dir):
            cmd = ['git', 'init', '--bare', trops_git_dir]
            subprocess.call(cmd)

        # Prepare for updating trops.git/config
        git_cmd = ['git', '--git-dir=' + trops_git_dir, 'config', '--local']
        git_conf = ConfigParser()
        git_conf.read(trops_git_dir + '/config')
        # Set "status.showUntrackedFiles no" locally
        if not git_conf.has_option('status', 'showUntrackedFiles'):
            cmd = git_cmd + ['status.showUntrackedFiles', 'no']
            subprocess.call(cmd)
        # Set $USER as user.name
        if not git_conf.has_option('user', 'name'):
            username = os.environ['USER']
            cmd = git_cmd + ['user.name', username]
            subprocess.call(cmd)
        # Set $USER@$HOSTNAME as user.email
        if not git_conf.has_option('user', 'email'):
            useremail = username + '@' + os.uname().nodename
            cmd = git_cmd + ['user.email', useremail]
            subprocess.call(cmd)

        # TODO: work-tree should become an option in the CLI. The default value is '/'
        # TODO: branch name should become an option, too
        # Set branch name as trops
        cmd = ['git', '--git-dir=' + trops_git_dir, 'branch', '--show-current']
        branch_name = subprocess.check_output(cmd).decode("utf-8")
        if 'trops' not in branch_name:
            cmd = ['git', '--git-dir=' + trops_git_dir, '--work-tree=/',
                   'checkout', '-b', 'trops']
            subprocess.call(cmd)

    def _check(self):
        """Checks TROPS_DIR"""

        if 'TROPS_DIR' not in os.environ:
            message = """\
                TROPS_DIR is not set

                    > source <project>/trops/tropsrc
                """
            print(dedent(message))
            exit(1)

    def git(self, args, other_args):
        """Git wrapper command"""

        self._check()

        cmd = self.git_cmd + other_args
        subprocess.call(cmd)

    def edit(self, args, other_args):
        """Wrapper of editor"""

        if 'TROPS_DIR' not in os.environ:
            print('TROPS_DIR is not defined')
            exit(1)

        for ff in other_args:
            # Check if the f is file
            if os.path.isfile(ff):
                cmd = self.git_cmd + ['ls-files', ff]
                output = subprocess.check_output(cmd).decode("utf-8")
                if ff in output:
                    git_msg = f"Update { ff }"
                else:
                    git_msg = f"Add { ff }"
                cmd = self.git_cmd + ['add', ff]
                subprocess.call(cmd)
                cmd = self.git_cmd + ['commit', '-m', git_msg, ff]
                subprocess.call(cmd)

        # TODO: When `-s` is in other_args, ignore or return error
        cmd = [args.editor]
        if args.sudo:
            cmd = ['sudo'] + cmd
        cmd = cmd + other_args
        subprocess.call(cmd)

        # Add and commmit after editing a file
        for f in other_args:
            if os.path.isfile(f):
                cmd = self.git_cmd + ['add', f]
                subprocess.call(cmd)
                cmd = self.git_cmd + ['commit', '-m', 'Update ' + f, f]
                subprocess.call(cmd)

    def _history(self):
        """Gets the history and return it as a list object"""

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
        """Get git log with the same date format as bash history
        and return it as a list
        """

        cmd = ['trops', 'git', 'log', '--oneline',
               '--pretty=format:%cd  trops git show %h #%d %s <%an>', '--date=format:%Y-%m-%d_%H:%M:%S']
        output = subprocess.check_output(cmd)
        return output.decode("utf-8").splitlines()

    def log(self, args, other_args):
        """Shows bash history and git log together in a timeline"""

        output = self._history() + self._gitlog()
        output.sort()

        # Just testing varbose output, not being used yet.
        # TODO: Add --verbose option to trops log
        verbose = False
        for l in output:
            print(l)
            if 'trops git show' in l and verbose:
                cmd = l.split()[1:4]
                subprocess.call(cmd)

    def ll(self, args, other_args):
        """Shows the list of git-tracked files"""

        dirs = [args.dir] + other_args
        for dir in dirs:
            if os.path.isdir(dir):
                os.chdir(dir)
                cmd = self.git_cmd + ['ls-files']
                output = subprocess.check_output(cmd)
                for f in output.decode("utf-8").splitlines():
                    cmd = ['ls', '-al', f]
                    subprocess.call(cmd)

    def touch(self, args, other_args):
        """Add a file or directory in the git repo"""

        # Check if the path exists
        if not os.path.exists(args.path):
            print(f"{ args.path } doesn't exists")
            exit(1)
        # TODO: Allow touch directory later
        if not os.path.isfile(args.path):
            message = f"""\
                Error: { args.path } is not a file
                Only file is allowed to be touched"""
            print(dedent(message))
            exit(1)

        # Check if the path is in the git repo
        cmd = self.git_cmd + ['ls-files', args.path]
        output = subprocess.check_output(cmd).decode("utf-8")
        # Set the message based on the output
        if output:
            git_msg = f"Update { args.path }"
        else:
            git_msg = f"Add { args.path }"
        # Add and commit
        cmd = self.git_cmd + ['add', args.path]
        subprocess.call(cmd)
        cmd = self.git_cmd + ['commit', '-m', git_msg, args.path]
        subprocess.call(cmd)

    def _update_pkg_list(self, args):

        # Update the pkg_List
        pkg_list_file = self.trops_dir + '/pkg_list'
        f = open(pkg_list_file, 'w')
        cmd = ['apt', 'list', '--installed']
        if args.sudo:
            cmd.insert(0, 'sudo')
        pkg_list = subprocess.check_output(cmd).decode('utf-8')
        f.write(pkg_list)
        f.close()
        # Commit the change if needed
        cmd = self.git_cmd + ['commit', '-m',
                              f'Update { pkg_list_file }', pkg_list_file]
        subprocess.call(cmd)

    def apt(self, args, other_args):
        """
        apt wrapper command to keep track of package list, which
        generates the package list and add to git repo
        before and after the package installation
        """

        self._update_pkg_list(args)
        # Run apt command
        cmd = ['apt'] + other_args
        if args.sudo:
            cmd.insert(0, 'sudo')
        subprocess.call(cmd)
        self._update_pkg_list(args)

    def container_create(self):
        """Creates a container with trops directory mounted"""
        # TODO: New feature
        pass

    def container_shell(self):
        """Enther the shell of the container"""
        # TODO: New feature
        pass

    def container_destroy(self):
        """Destroy the container"""
        # TODO: New feature
        pass

    def main(self):
        """Get subcommand and arguments and pass them to the hander"""

        parser = argparse.ArgumentParser(
            description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        # trops init <dir>
        parser_init = subparsers.add_parser('init', help='Initialize Trops')
        parser_init.add_argument(
            '-w', '--work-tree', default='/', help='Set work-tree')
        parser_init.set_defaults(handler=self.initialize)
        parser_init.add_argument('dir', help="Directory path")
        # trops edit <file>
        parser_edit = subparsers.add_parser('edit', help='see `edit -h`')
        parser_edit.add_argument('-s', '--sudo', help="Use sudo",
                                 action='store_true')
        parser_edit.add_argument(
            "-e", "--editor", default="vim", help="editor")
        parser_edit.set_defaults(handler=self.edit)
        # trops git <file/dir>
        parser_git = subparsers.add_parser('git', help='see `git -h`')
        parser_git.set_defaults(handler=self.git)
        parser_git.add_argument('-s', '--sudo', help="Use sudo",
                                action='store_true')
        # trops log
        parser_log = subparsers.add_parser('log', help='see `log -h`')
        parser_log.set_defaults(handler=self.log)
        # trops ll
        parser_ll = subparsers.add_parser('ll', help="List files")
        parser_ll.add_argument('dir', help='directory path',
                               nargs='?', default=os.getcwd())
        parser_ll.set_defaults(handler=self.ll)
        # trops touch
        parser_touch = subparsers.add_parser(
            'touch', help="Add file in git repo")
        parser_touch.add_argument('path', help='path of file or directory')
        parser_touch.set_defaults(handler=self.touch)
        # trops apt
        parser_apt = subparsers.add_parser('apt', help='Apt wrapper command')
        parser_apt.add_argument('-s', '--sudo', help="Use sudo",
                                action='store_true')
        parser_apt.set_defaults(handler=self.apt)

        # Pass args and other args to the hander
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
