import os
import time

from configparser import ConfigParser
from textwrap import dedent

from .trops import TropsMain
from .utils import pick_out_repo_name_from_git_remote

class TropsLog(TropsMain):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        if 'TROPS_ENV' not in os.environ:
            msg = """\
                ERROR: TROPS_ENV has not been set
                    # List existing environments
                    $ trops env list
                    
                    # Create new environment
                    $ trops env create <envname>

                    # Turn on Trops
                    $ ontrops <envname>"""
            print(dedent(msg))
            exit(1)

    def _follow(self, file):

        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def log(self):
        """Print trops log"""

        input_log_file = self.trops_logfile

        with open(input_log_file) as ff:
            if self.args.tail:
                lines = ff.readlines()[-self.args.tail:]
            else:
                lines = ff.readlines()
            # strip \n in items
            lines = list(map(lambda x:x.strip(),lines))

            if self.args.all:
                target_lines = lines
            elif self.trops_tags:
                keyword = f'TROPS_TAGS={self.trops_tags}'
                target_lines = [line for line in lines if keyword in line]
            elif hasattr(self, 'trops_sid'):
                keyword = f'TROPS_SID={self.trops_sid}'
                target_lines = [line for line in lines if keyword in line]

        if self.args.save:
            self._save_log(target_lines)
        else:
            print(*target_lines, sep='\n')

        if self.args.follow:
            ff = open(input_log_file, "r")
            try:
                lines = self._follow(ff)
                for line in lines:
                    if self.args.all:
                        print(line, end='')
                    elif f'TROPS_TAGS={self.trops_tags}' in line:
                        print(line, end='')

            except KeyboardInterrupt:
                print('\nClosing trops log...')

    def _save_log(self, target_lines):
        '''Save log'''
        log_dir = self.trops_dir + '/log'

        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)

        if hasattr(self, 'git_remote'):
            file_prefix = pick_out_repo_name_from_git_remote(self.git_remote) + '_' + self.trops_env
        else:
            file_prefix = self.trops_env

        if self.args.name:
            file_name = self.args.name.replace(' ', '_') + '.log'
        elif not self.trops_tags:
            print("You don't have a tag. Please set a tag or add --name <name> option")
            exit(1)
        else:
            if ',' in self.trops_tags:
                primary_tag = self.trops_tags.split(',')[0]
            elif ';' in self.trops_tags:
                primary_tag = self.trops_tags.split(';')[0]
            else:
                primary_tag = self.trops_tags

            if primary_tag[0] == '#':
                file_name = file_prefix + primary_tag.replace('#', '__i') + '.log'
            elif primary_tag[0] == '!':
                file_name = file_prefix + primary_tag.replace('!', '__c') + '.log'
            else:
                file_name = primary_tag.replace(
                    '#', '__i').replace('!', '__c') + '.log'

        file_path = log_dir + '/' + file_name

        with open(file_path, mode='w') as f:
            f.writelines(s + '\n' for s in target_lines)

        self._touch_file(file_path)

def trops_log(args, other_args):

    trlog = TropsLog(args, other_args)
    trlog.log()


def add_log_subparsers(subparsers):

    parser_log = subparsers.add_parser('log', help='show log')
    parser_log.add_argument(
        '-s', '--save', action='store_true', help='save log')
    parser_log.add_argument(
    '--name', help='with --save, you can specify the name')
    parser_log.add_argument(
        '-t', '--tail', type=int, help='set number of lines to show')
    parser_log.add_argument(
        '-f', '--follow', action='store_true', help='follow log interactively')
    parser_log.add_argument(
        '-a', '--all', action='store_true', help='show all log')
    parser_log.set_defaults(handler=trops_log)
