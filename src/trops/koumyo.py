import os
import re
import sys

from tabulate import tabulate
from textwrap import dedent

from .trops import TropsMain
from .utils import pick_out_repo_name_from_git_remote

class TropsKoumyo(TropsMain):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        self.args = args

        if other_args:
            msg = f"""\
                Unsupported argments: { ', '.join(other_args)}
                > trops km --help"""
            print(dedent(msg))
            exit(1)

        try:
            input = sys.stdin.read()
        except KeyboardInterrupt:
            msg = '''\

                Usage example of trops km:
                    > trops log | trops km
                    > trops log | trops km --only=%D,%T,%u,%c,%d,%x
                    
                    %D: Date
                    %T: Time
                    %u: User@host
                    %ll: Log level
                    %lt: Log type
                    %c: Command
                    %d: Directory/O,G,M
                    %x: Exit Code
                    %i: ID
                    %e: Env
                    %t: Tags'''
            print(dedent(msg))
            exit(1)

        self.logs = input.splitlines()
        if hasattr(args, 'only') and args.only != None:
            self.only_list = args.only.split(',')

    def _split_pipe_in_cmd(self, cmd):

        new_cmd = []
        for i in cmd:
            if '|' in i:
                new_cmd += re.split('(\|+)', i)
            elif '>' in i:
                new_cmd += re.split('(\>+)', i)
            else:
                new_cmd += [i]
        return new_cmd

    def _ignore_cmd(self, cmd):
        """Return True when the command(cmd) should be ignored"""

        # Ingore if cmd is empty
        if not cmd:
            return True

        # If any of '|', '>', and '<' is in the command,
        # it shouldn't be ignored, except `trops log` and `history`.
        if (cmd[0:2] != ['trops', 'log'] and cmd[0] != 'history') and \
                ('|' in cmd or '>' in cmd or '<' in cmd):
            return False
        # These commands should be ignored
        elif cmd[0] in [
            'ls',
            'll',
            'cat',
            'echo',
            'sl',
            'cd',
            'history',
            'ttags'
        ]:
            return True
        # These trops commands should be ignored
        elif cmd[0] == 'trops':
            check_list = ['log', 'show', 'list', 'll']
            if any(w in cmd for w in check_list):
                return True
        # The other commands shouldn't be ignored
        else:
            return False

    def _format(self):

        formatted_logs = []

        for log in self.logs:
            # split log
            splitted_log = log.split()
            if 'CM' in splitted_log:
                cmd_start_idx = splitted_log.index('CM') + 1
                cmd_end_idx = splitted_log.index('#>')
                formatted_log = splitted_log[:cmd_start_idx]
                splitted_cmd = splitted_log[cmd_start_idx:cmd_end_idx]
                if not self.args.no_declutter and \
                        self._ignore_cmd(self._split_pipe_in_cmd(splitted_cmd)):
                    continue
                if self.args.markdown or self.args.save:
                    command_text = ' '.join(splitted_log[cmd_start_idx:cmd_end_idx])
                    formatted_log.append(escape_special_characters(command_text))
                else:
                    formatted_log.append(
                        ' '.join(splitted_log[cmd_start_idx:cmd_end_idx]))
                formatted_log = formatted_log + splitted_log[cmd_end_idx:]
                # formatted_log.remove('CM')
                formatted_log.remove('#>')
                for i, n in enumerate(formatted_log):
                    # Skip until after the command(0~5)
                    if i < 6:
                        continue
                    elif 'PWD=' in n:
                        formatted_log[i] = n.replace('PWD=', '').rstrip(',')
                    elif 'EXIT=' in n:
                        formatted_log[i] = n.replace('EXIT=', '').rstrip(',')
                    elif 'TROPS_SID=' in n:
                        formatted_log[i] = n.replace(
                            'TROPS_SID=', '').rstrip(',')
                    elif 'TROPS_ENV=' in n:
                        formatted_log[i] = n.replace(
                            'TROPS_ENV=', '').rstrip(',')
                    elif 'TROPS_TAGS=' in n:
                        formatted_log[i] = n.replace(
                            'TROPS_TAGS=', '').rstrip(',')

                while len(formatted_log) < 10:
                    formatted_log.append('-')
            elif 'FL' in splitted_log:
                cmd_start_idx = splitted_log.index('FL') + 1
                cmd_end_idx = splitted_log.index('#>')
                formatted_log = splitted_log[:cmd_start_idx]
                formatted_log.append(
                    ' '.join(splitted_log[cmd_start_idx:cmd_end_idx]))
                formatted_log = formatted_log + splitted_log[cmd_end_idx:]
                # formatted_log.remove('FL')
                formatted_log.remove('#>')
                formatted_log.pop(6)
                formatted_log.insert(7, '-')
                for i, n in enumerate(formatted_log):
                    if 'TROPS_SID=' in n:
                        formatted_log[i] = n.replace(
                            'TROPS_SID=', '').rstrip(',')
                    elif 'TROPS_ENV=' in n:
                        formatted_log[i] = n.replace(
                            'TROPS_ENV=', '').rstrip(',')
                    elif 'TROPS_TAGS=' in n:
                        formatted_log[i] = n.replace(
                            'TROPS_TAGS=', '').rstrip(',')
                while len(formatted_log) < 10:
                    formatted_log.append('-')
            dict_headers = {
                '%D': 'Date',
                '%T': 'Time',
                '%u': 'User@host',
                '%ll': 'Log level',
                '%lt': 'Log type',
                '%c': 'Command',
                '%d': 'Directory/O,G,M',
                '%x': 'Exit',
                '%i': 'ID',
                '%e': 'Env',
                '%t': 'Tags'}
            headers = []
            for k, v in dict_headers.items():
                headers.append(f'{v}[{k}]')
            # if --only is added, pick the only chosen elements
            if hasattr(self, 'only_list') and self.args.all != True:
                i = []
                selected_log = []
                selected_headers = []
                for item in self.only_list:
                    i.append(list(dict_headers.keys()).index(item))
                for index in i:
                    selected_log.append(formatted_log[index])
                    selected_headers.append(list(dict_headers.values())[index])
                headers = selected_headers
                formatted_logs.append(selected_log)
            else:
                formatted_logs.append(formatted_log)

        if 'headers' not in locals():
            print('Koumyo(km) ignored everything in the output')
            exit(1)
        elif self.args.save:
            self._save(tabulate(formatted_logs, headers, tablefmt="github"))
        elif self.args.markdown:
            print(tabulate(formatted_logs, headers, tablefmt="github"))
        elif self.args.html:
            print(tabulate(formatted_logs, headers, tablefmt="html"))
        else:
            print(tabulate(formatted_logs, headers))


    def _save(self, kmout):

        km_dir = self.trops_dir + '/km'

        if not os.path.isdir(km_dir):
            os.mkdir(km_dir)

        if hasattr(self, 'git_remote'):
            file_prefix = pick_out_repo_name_from_git_remote(self.git_remote) + '_' + self.trops_env
        else:
            file_prefix = self.trops_env

        if self.args.name:
            file_name = self.args.name.replace(' ', '_') + '.md'
        elif not self.trops_tags:
            print("You don't have a tag. Please set --name <name> option")
            exit(1)
        else:
            check_list = [',', ';']
            if ',' in self.trops_tags:
                primary_tag = self.trops_tags.split(',')[0]
            elif ';' in self.trops_tags:
                primary_tag = self.trops_tags.split(';')[0]
            else:
                primary_tag = self.trops_tags

            if primary_tag[0] == '#':
                file_name = file_prefix + primary_tag.replace('#', '__i') + '.md'
            elif primary_tag[0] == '!':
                file_name = file_prefix + primary_tag.replace('!', '__c') + '.md'
            else:
                file_name = primary_tag.replace(
                    '#', '__i').replace('!', '__c') + '.md'

        file_path = km_dir + '/' + file_name

        with open(file_path, mode='w') as f:
            f.write(kmout)

        self._touch_file(file_path)

    def run(self):

        self._format()

def escape_special_characters(text):
    """Escape special characters for Markdown."""
    return text.replace('|', r'\|').replace('$', r'\$')

def run(args, other_args):

    tk = TropsKoumyo(args, other_args)
    tk.run()


def add_koumyo_subparsers(subparsers):

    # trops koumyo
    parser_koumyo = subparsers.add_parser(
        'km', help=dedent('kou-myo(km) sheds light on trops log'))
    parser_koumyo.add_argument(
        '-o', '--only', default='%D,%T,%u,%c,%d,%x',
        help='list of items (default: %(default)s)')
    parser_koumyo.add_argument(
        '-n', '--no-declutter', action='store_true',
        help='disable log-decluttering')
    parser_koumyo.add_argument(
        '-a', '--all', action='store_true',
        help='all items in the log')
    parser_koumyo.add_argument(
        '-s', '--save', action='store_true',
        help='save the km log')
    parser_koumyo.add_argument(
        '--name', help='with --save, you can specify the name')
    group = parser_koumyo.add_mutually_exclusive_group()
    group.add_argument(
        '-m', '--markdown', action='store_true',
        help='markdown table format')
    group.add_argument(
        '--html', action='store_true',
        help='HTML table format')
    parser_koumyo.set_defaults(handler=run)
