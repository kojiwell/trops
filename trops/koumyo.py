import sys
# TODO: Use [python-tabulate](https://pypi.org/project/tabulate/)


class TropsKoumyo:

    def __init__(self, args, other_args):

        input = sys.stdin.read()
        self.logs = input.splitlines()
        self.markdown = args.markdown

    def _format(self):

        pass

    def run(self):

        print(self.markdown)
        print(self.logs)


def run(args, other_args):

    tk = TropsKoumyo(args, other_args)
    tk.run()


def koumyo_subparsers(subparsers):

    # trops koumyo
    parser_koumyo = subparsers.add_parser(
        'koumyo', help='track file operations')
    parser_koumyo.add_argument(
        '-m', '--markdown', action='store_true', help='Markdown format')
    parser_koumyo.set_defaults(handler=run)
