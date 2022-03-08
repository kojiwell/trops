import sys
from tabulate import tabulate
# TODO: Use [python-tabulate](https://pypi.org/project/tabulate/)


class TropsKoumyo:

    def __init__(self, args, other_args):

        input = sys.stdin.read()
        self.logs = input.splitlines()
        self.markdown = args.markdown

    def _format(self):

        formatted_logs = []

        for log in self.logs:
            # split log
            splitted_log = log.split()
            if 'CM' in splitted_log:
                cmd_start_idx = splitted_log.index('CM') + 1
                cmd_end_idx = splitted_log.index('#>')
                formatted_log = splitted_log[:cmd_start_idx]
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
                        formatted_log[i] = n.replace('TROPS_SID=', '')
                formatted_logs.append(formatted_log)
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
                formatted_log.append('-')
                formatted_log.append('-')
                formatted_logs.append(formatted_log)
        headers = ['Date', 'Time', 'User',
                   'Level', 'Type', 'Command', 'Directory / Owner,Group,Mode', 'EXIT', 'TROPS_ID']
        print(tabulate(formatted_logs, headers))

    def run(self):

        self._format()


def run(args, other_args):

    tk = TropsKoumyo(args, other_args)
    tk.run()


def koumyo_subparsers(subparsers):

    # trops koumyo
    parser_koumyo = subparsers.add_parser(
        'km', help='(KM)Kou-Myo can make log be easier to read')
    parser_koumyo.add_argument(
        '-m', '--markdown', action='store_true', help='Markdown format')
    parser_koumyo.set_defaults(handler=run)
