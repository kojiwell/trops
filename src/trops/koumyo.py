import re
import sys

from tabulate import tabulate
from textwrap import dedent


class TropsKoumyo:

    def __init__(self, args, other_args):

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
                    > trops log | trops km --only=user,command,directory'''
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
            'history'
        ]:
            return True
        # These trops commands should be ignored
        elif cmd[0] == 'trops':
            if 'log' in cmd \
                    or 'show' in cmd \
                    or 'list' in cmd \
                    or 'll' in cmd:
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
                if self.args.markdown:
                    formatted_log.append(
                        ' '.join(splitted_log[cmd_start_idx:cmd_end_idx]).replace('|', '\|'))
                else:
                    formatted_log.append(
                        ' '.join(splitted_log[cmd_start_idx:cmd_end_idx]))
                formatted_log = formatted_log + splitted_log[cmd_end_idx:]
                # formatted_log.remove('CM')
                formatted_log.remove('#>')
                for i, n in enumerate(formatted_log):
                    if 'PWD=' in n:
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
            headers = ['date', 'time', 'user',
                       'level', 'type', 'command', 'directory', 'exit', 'id', 'env', 'tags']
            # if --only is added, pick the only chosen elements
            if hasattr(self, 'only_list') and self.args.all != True:
                i = []
                selected_log = []
                selected_headers = []
                for item in self.only_list:
                    i.append(headers.index(item))
                for index in i:
                    selected_log.append(formatted_log[index])
                    selected_headers.append(headers[index])
                headers = selected_headers
                formatted_logs.append(selected_log)
            else:
                formatted_logs.append(formatted_log)
        if self.args.markdown:
            print(tabulate(formatted_logs, headers, tablefmt="github"))
        elif self.args.html:
            print(tabulate(formatted_logs, headers, tablefmt="html"))
        else:
            print(tabulate(formatted_logs, headers))

    def run(self):

        self._format()


def run(args, other_args):

    tk = TropsKoumyo(args, other_args)
    tk.run()


def add_koumyo_subparsers(subparsers):

    # trops koumyo
    parser_koumyo = subparsers.add_parser(
        'km', help='(KM)Kou-Myo sheds light on trops log')
    parser_koumyo.add_argument(
        '-o', '--only', default='date,time,user,command,directory',
        help='list of items (default: %(default)s)')
    parser_koumyo.add_argument(
        '--no-declutter', action='store_true',
        help='disable log-decluttering')
    parser_koumyo.add_argument(
        '-a', '--all', action='store_true',
        help='all items in the log')
    group = parser_koumyo.add_mutually_exclusive_group()
    group.add_argument(
        '-m', '--markdown', action='store_true',
        help='markdown table format')
    group.add_argument(
        '--html', action='store_true',
        help='HTML table format')
    parser_koumyo.set_defaults(handler=run)
    # TODO: Add --output option to save the output in as a file
