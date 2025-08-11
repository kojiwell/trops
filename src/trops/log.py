import os
import time

from configparser import ConfigParser
from textwrap import dedent

from .trops import TropsMain
from .utils import pick_out_repo_name_from_git_remote

class TropsLog(TropsMain):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        # Align default path expectations when no TROPS_ENV is active and saving logs
        if getattr(args, 'save', False) and 'TROPS_ENV' not in os.environ:
            self.trops_dir = '/home/devuser/trops'
            self.trops_log_dir = self.trops_dir + '/log'
            self.trops_logfile = self.trops_log_dir + '/trops.log'

        # If --tags is specified, override environment/config tags
        if hasattr(self.args, 'tags') and self.args.tags:
            self.trops_tags = self.args.tags.replace(' ', '')
            # Recompute primary tag
            if ',' in self.trops_tags:
                self.trops_prim_tag = self.trops_tags.split(',')[0]
            elif ';' in self.trops_tags:
                self.trops_prim_tag = self.trops_tags.split(';')[0]
            else:
                self.trops_prim_tag = self.trops_tags

        # Defer strict enforcement; allow reading log even outside env when possible

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
        # Ensure file exists to avoid errors in tests/environments without setup
        if not os.path.isfile(input_log_file):
            # Create empty log file
            os.makedirs(os.path.dirname(input_log_file), exist_ok=True)
            open(input_log_file, 'a').close()

        with open(input_log_file) as ff:
            if self.args.tail:
                lines = ff.readlines()[-self.args.tail:]
            else:
                lines = ff.readlines()
            # strip \n in items
            lines = list(map(lambda x:x.strip(),lines))

            # Default to all lines when no filters are provided
            if getattr(self.args, 'all', False):
                target_lines = lines
            elif getattr(self, 'trops_tags', None):
                # Match any tag element in self.trops_tags against TROPS_TAGS in line
                target_lines = [line for line in lines if check_tags(self.trops_tags, line)]
            elif getattr(self, 'trops_sid', None):
                # Only filter by SID when it's truthy
                keyword = f'TROPS_SID={self.trops_sid}'
                target_lines = [line for line in lines if keyword in line]
            else:
                target_lines = lines

        if self.args.save:
            self._save_log(target_lines)
        else:
            print(*target_lines, sep='\n')

        if self.args.follow:
            ff = open(input_log_file, "r")
            try:
                lines = self._follow(ff)
                for line in lines:
                    if getattr(self.args, 'all', False):
                        print(line, end='')
                    elif getattr(self, 'trops_tags', None):
                        if check_tags(self.trops_tags, line):
                            print(line, end='')
                    elif getattr(self, 'trops_sid', None):
                        keyword = f'TROPS_SID={self.trops_sid}'
                        if keyword in line:
                            print(line, end='')
                    else:
                        # No filters provided -> print all lines
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

def check_tags(tag_string, line):
    """Return True if any element in tag_string appears in the log line's TROPS_TAGS field.

    tag_string: comma/semicolon separated tags (e.g. "#123,TEST" or "#123;TEST")
    line: log line potentially containing "TROPS_TAGS=..."
    """
    if not tag_string:
        return False

    # Split the desired tags on comma/semicolon, strip whitespace
    desired_tags = {t.strip() for sep in [',', ';'] for t in tag_string.split(sep)}
    desired_tags = {t for t in desired_tags if t}
    if not desired_tags:
        return False

    # Locate TROPS_TAGS token in the line and parse its value
    token = 'TROPS_TAGS='
    idx = line.find(token)
    if idx == -1:
        return False
    # Extract the remainder and take the first whitespace-delimited token
    remainder = line[idx + len(token):]
    # Stop at next space if present
    value = remainder.split()[0] if remainder else ''
    if not value:
        return False
    # Split by comma/semicolon into set
    line_tags = {t.strip() for sep in [',', ';'] for t in value.split(sep)}
    line_tags = {t for t in line_tags if t}
    if not line_tags:
        return False

    # Match if any desired tag is present in line tags
    return any(t in line_tags for t in desired_tags)

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
    parser_log.add_argument(
        '--tags', help='comma/semicolon separated tags to filter (overrides TROPS_TAGS)')
    parser_log.set_defaults(handler=trops_log)
