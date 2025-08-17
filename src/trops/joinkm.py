import os
from datetime import datetime
from textwrap import dedent

from .utils import absolute_path
from .trops import TropsError


HEADERS = [
    'Date',
    'Time',
    'User@host',
    'Command',
    'Directory/O,G,M',
    'Exit'
]


class TropsJoinKm:
    def __init__(self, args, other_args):
        self.args = args
        self.other_args = other_args

        if other_args:
            msg = f"""\
                Unsupported argments: {', '.join(other_args)}
                > trops joinkm --help"""
            raise TropsError(dedent(msg))

        # Validate inputs
        if not hasattr(args, 'files') or not args.files:
            raise TropsError('ERROR: at least one input file is required')

        if not hasattr(args, 'output') or not args.output:
            raise TropsError('ERROR: -o/--output is required')

        self.input_files = [absolute_path(p) for p in args.files]
        self.output_path = absolute_path(args.output)
        self.append = getattr(args, 'append', False)

        # Pre-validate input files exist
        missing = [p for p in self.input_files if not os.path.isfile(p)]
        if missing:
            raise TropsError('ERROR: input file not found: ' + ', '.join(missing))

    @staticmethod
    def _is_separator_line(line: str) -> bool:
        s = line.strip()
        if not (s.startswith('|') and s.endswith('|')):
            return False
        # Consider it a separator if it only consists of | - : and spaces
        body = s.replace('|', '').replace(' ', '')
        return all(c in '-:' for c in body) and len(body) > 0

    @staticmethod
    def _is_header_line(cells) -> bool:
        if len(cells) < len(HEADERS):
            return False
        # Compare prefix to allow extra columns gracefully, but expect exact order for the first 6
        for i, h in enumerate(HEADERS):
            if cells[i] != h:
                return False
        return True

    @staticmethod
    def _parse_row(line: str):
        parts = [p.strip() for p in line.strip().split('|')]
        if len(parts) < 3:
            return None
        # Drop leading and trailing empty parts due to leading and trailing '|'
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]
        return parts

    def _read_rows_from_file(self, file_path: str):
        rows = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for raw in f:
                # Only consider markdown table lines beginning with '|'
                if not raw.lstrip().startswith('|'):
                    continue
                if self._is_separator_line(raw):
                    continue
                cells = self._parse_row(raw)
                if not cells:
                    continue
                # Skip header lines matching expected headers
                if self._is_header_line(cells):
                    continue
                # Keep exactly the expected first 6 columns (ignore extras if any)
                cells = cells[:len(HEADERS)]
                if len(cells) != len(HEADERS):
                    # Skip malformed rows
                    continue
                rows.append(cells)
        return rows

    @staticmethod
    def _parse_dt(date_str: str, time_str: str) -> datetime:
        # Strict format as produced by trops logs
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

    def run(self):
        # Collect rows from all files
        all_rows = []
        for path in self.input_files:
            all_rows.extend(self._read_rows_from_file(path))

        # Sort by Date + Time ascending
        try:
            all_rows.sort(key=lambda r: self._parse_dt(r[0], r[1]))
        except Exception as e:
            raise TropsError(f"ERROR: failed to sort rows by datetime: {e}")

        # Ensure output directory exists
        out_dir = os.path.dirname(self.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # Write output markdown table
        mode = 'a' if self.append else 'w'
        with open(self.output_path, mode, encoding='utf-8') as out:
            header_line = '| ' + ' | '.join(HEADERS) + ' |\n'
            sep_line = '| ' + ' | '.join(['---'] * len(HEADERS)) + ' |\n'
            # Always write a header block for each write, including append mode
            out.write(header_line)
            out.write(sep_line)
            for cells in all_rows:
                out.write('| ' + ' | '.join(cells) + ' |\n')


def run(args, other_args):
    jk = TropsJoinKm(args, other_args)
    jk.run()


def add_joinkm_subparsers(subparsers):
    parser = subparsers.add_parser('joinkm', help='join multiple KM markdown tables into a single, time-sorted table')
    parser.add_argument('files', nargs='+', help='input markdown files to merge')
    parser.add_argument('-o', '--output', required=True, help='output file path')
    # support both --append and misspelled --apend for convenience
    parser.add_argument('-a', '--append', '--apend', dest='append', action='store_true', help='append to the output file instead of overwriting')
    parser.set_defaults(handler=run)


