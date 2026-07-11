import os
import re
import sys

from tabulate import tabulate
from textwrap import dedent

from .trops import TropsCLI, TropsError
from .utils import pick_out_repo_name_from_git_remote


class TropsTLDR(TropsCLI):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        self.args = args

        if other_args:
            msg = f"""\
                Unsupported argments: { ', '.join(other_args)}
                > trops tldr --help"""
            raise TropsError(dedent(msg))

        try:
            input = sys.stdin.read()
        except KeyboardInterrupt:
            msg = '''\

                Usage example of trops tldr:
                    > trops log | trops tldr
                    > trops log | trops tldr --only=%D,%T,%u,%c,%d,%x
                    
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
            raise TropsError(dedent(msg))

        self.logs = input.splitlines()
        if hasattr(args, 'only') and args.only != None:
            self.only_list = args.only.split(',')

    def _split_pipe_in_cmd(self, cmd):

        new_cmd = []
        for i in cmd:
            if '|' in i:
                new_cmd += re.split(r'(\|+)', i)
            elif '>' in i:
                new_cmd += re.split(r'(>+)', i)
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

    def _parse_tail_fields(self, tokens):
        """Parse trailing ``KEY=value`` tokens into a dict keyed by name.

        The ``#>`` note of a log line carries fields such as ``PWD``, ``EXIT``
        and the optional ``TROPS_SID`` / ``TROPS_ENV`` / ``TROPS_TAGS``. Their
        separators are inconsistent (``, `` after some, a bare space before
        ``TROPS_TAGS``), and the optional ones may be absent, so they can't be
        read positionally. Split each token on its first ``=`` after dropping a
        trailing comma; absent fields simply don't appear in the result.
        """
        fields = {}
        for tok in tokens:
            token = tok.rstrip(',')
            if '=' in token:
                key, value = token.split('=', 1)
                fields.setdefault(key, value)
        return fields

    def _format(self):

        formatted_logs = []

        for log in self.logs:
            # split log
            splitted_log = log.split()
            if 'CM' in splitted_log:
                cmd_start_idx = splitted_log.index('CM') + 1
                cmd_end_idx = splitted_log.index('#>')
                splitted_cmd = splitted_log[cmd_start_idx:cmd_end_idx]
                if not self.args.no_declutter and \
                        self._ignore_cmd(self._split_pipe_in_cmd(splitted_cmd)):
                    continue
                command_text = ' '.join(splitted_cmd)
                if self.args.markdown or self.args.save:
                    command_text = escape_special_characters(command_text)
                # prefix: Date, Time, User@host, Log level, Log type('CM')
                prefix = splitted_log[:cmd_start_idx]
                # Trailing PWD/EXIT/TROPS_* fields are optional and positionally
                # unstable, so key them by name rather than by index.
                fields = self._parse_tail_fields(splitted_log[cmd_end_idx + 1:])
                formatted_log = [
                    prefix[0], prefix[1], prefix[2], prefix[3], prefix[4],
                    command_text,
                    fields.get('PWD', '-'),          # %d Directory
                    fields.get('EXIT', '-'),         # %x Exit
                    fields.get('TROPS_SID', '-'),    # %i ID
                    fields.get('TROPS_ENV', '-'),    # %e Env
                    fields.get('TROPS_TAGS', '-'),   # %t Tags
                ]
            elif 'FL' in splitted_log:
                cmd_start_idx = splitted_log.index('FL') + 1
                cmd_end_idx = splitted_log.index('#>')
                command_text = ' '.join(splitted_log[cmd_start_idx:cmd_end_idx])
                # prefix: Date, Time, User@host, Log level, Log type('FL')
                prefix = splitted_log[:cmd_start_idx]
                tail = splitted_log[cmd_end_idx + 1:]  # note, O=,G=,M=, TROPS_*
                ogm = '-'
                for tok in tail:
                    if tok.startswith('O=') and ',G=' in tok and ',M=' in tok:
                        ogm = tok.rstrip(',')
                        break
                fields = self._parse_tail_fields(tail)
                formatted_log = [
                    prefix[0], prefix[1], prefix[2], prefix[3], prefix[4],
                    command_text,
                    ogm,                             # %d Directory/O,G,M
                    '-',                             # %x Exit (n/a for file logs)
                    fields.get('TROPS_SID', '-'),    # %i ID
                    fields.get('TROPS_ENV', '-'),    # %e Env
                    fields.get('TROPS_TAGS', '-'),   # %t Tags
                ]
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
            raise TropsError('TLDR(tldr) ignored everything in the output')
        elif self.args.save:
            self._save(tabulate(formatted_logs, headers, tablefmt="github"))
        elif self.args.markdown:
            print(tabulate(formatted_logs, headers, tablefmt="github"))
        elif self.args.html:
            print(tabulate(formatted_logs, headers, tablefmt="html"))
        else:
            print(tabulate(formatted_logs, headers))


    def _save(self, tablog_out):

        tablog_dir = self.trops_dir + '/tablog'

        if not os.path.isdir(tablog_dir):
            os.mkdir(tablog_dir)

        git_remote = getattr(self, 'git_remote', None)
        if git_remote:
            file_prefix = pick_out_repo_name_from_git_remote(git_remote) + '_' + self.trops_env
        else:
            file_prefix = self.trops_env

        if self.args.name:
            file_name = self.args.name.replace(' ', '_') + '.md'
        elif not self.trops_tags:
            raise TropsError("You don't have a tag. Please set --name <name> option")
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
                normalized = primary_tag.replace('#', '__i').replace('!', '__c')
                file_name = f"{file_prefix}_{normalized}.md"

        file_path = tablog_dir + '/' + file_name

        with open(file_path, mode='w') as f:
            f.write(tablog_out)

        self._touch_file(file_path)
        # If saved, push to remote when configured
        if getattr(self, 'git_remote', False):
            self._push_if_remote_set()

    def run(self):

        self._format()


def escape_special_characters(text):
    """Escape special characters for Markdown."""
    return text.replace('|', r'\|').replace('$', r'\$')


def run(args, other_args):

    tk = TropsTLDR(args, other_args)
    tk.run()


def add_tldr_subparsers(subparsers):

    # trops tldr
    parser_tldr = subparsers.add_parser(
        'tldr', help=dedent('tldr summarizes trops log'))
    parser_tldr.add_argument(
        '-o', '--only', default='%D,%T,%u,%c,%d,%x',
        help='list of items (default: %(default)s)')
    parser_tldr.add_argument(
        '-n', '--no-declutter', action='store_true',
        help='disable log-decluttering')
    parser_tldr.add_argument(
        '-a', '--all', action='store_true',
        help='all items in the log')
    parser_tldr.add_argument(
        '-s', '--save', action='store_true',
        help='save the tablog')
    parser_tldr.add_argument(
        '--name', help='with --save, you can specify the name')
    group = parser_tldr.add_mutually_exclusive_group()
    group.add_argument(
        '-m', '--markdown', action='store_true',
        help='markdown table format')
    group.add_argument(
        '--html', action='store_true',
        help='HTML table format')
    parser_tldr.set_defaults(handler=run)


