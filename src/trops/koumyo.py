import sys

from tabulate import tabulate
from textwrap import dedent


class TropsKoumyo:

    def __init__(self, args, other_args):

        self.markdown = args.markdown
        self.html = args.html

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

    def _format(self):

        formatted_logs = []

        for log in self.logs:
            # split log
            splitted_log = log.split()
            if 'CM' in splitted_log:
                cmd_start_idx = splitted_log.index('CM') + 1
                cmd_end_idx = splitted_log.index('#>')
                formatted_log = splitted_log[:cmd_start_idx]
                if self.markdown:
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
            if hasattr(self, 'only_list'):
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
        if self.markdown:
            print(tabulate(formatted_logs, headers, tablefmt="github"))
        elif self.html:
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
        '-o', '--only',
        help='list of items (e.g. --only=command,directory')
    group = parser_koumyo.add_mutually_exclusive_group()
    group.add_argument(
        '--markdown', action='store_true',
        help='markdown table format')
    group.add_argument(
        '--html', action='store_true',
        help='HTML table format')
    parser_koumyo.set_defaults(handler=run)
    # TODO: Add --output option to save the output in as a file
