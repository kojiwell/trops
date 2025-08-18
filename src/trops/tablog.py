import os
import tempfile
from configparser import ConfigParser
from textwrap import dedent
from datetime import datetime

import subprocess


from .trops import TropsError
from .utils import absolute_path


class TropsTablogGet:
    def __init__(self, args, other_args):
        self.args = args
        self.other_args = other_args

        if other_args:
            msg = f"""\
                Unsupported argments: {', '.join(other_args)}
                > trops tablog get --help"""
            raise TropsError(dedent(msg))

        # Validate flags
        all_flag = getattr(args, 'all', False)
        env_flag = getattr(args, 'env', None)
        if (not all_flag and not env_flag) or (all_flag and env_flag):
            raise TropsError('ERROR: specify exactly one of -a/--all or -e/--env <env>')

        # Validate target path presence (existence is checked later)
        if not hasattr(args, 'path') or not args.path:
            raise TropsError('ERROR: target <path> is required')

        # Load config from $TROPS_DIR/trops.cfg
        trops_dir = os.getenv('TROPS_DIR')
        if not trops_dir:
            raise TropsError('ERROR: TROPS_DIR is not set')
        cfg_path = os.path.join(trops_dir, 'trops.cfg')
        if not os.path.isfile(cfg_path):
            raise TropsError(f"ERROR: config not found: {cfg_path}")

        self.config = ConfigParser()
        self.config.read(cfg_path)

        # Build list of environments to process
        if all_flag:
            self.envs = [s for s in self.config.sections()]
        else:
            if not self.config.has_section(env_flag):
                raise TropsError(f"ERROR: env '{env_flag}' not found in config")
            self.envs = [env_flag]

    def _git_for_env(self, env_name, args_list):
        # Call git directly; do not depend on TropsMain/git_dir/work_tree
        result = subprocess.run(['git'] + args_list)
        if result.returncode != 0:
            raise TropsError(f"git {' '.join(args_list[:2])} failed with code {result.returncode}")

    def run(self):
        # Resolve and prepare output directory now; create it if it does not exist
        from .utils import absolute_path as _abs
        self.target_prefix = _abs(self.args.path)
        os.makedirs(self.target_prefix, exist_ok=True)

        # Optionally update repository state via trops fetch before extraction
        if getattr(self.args, 'update', False):
            result = subprocess.run(['trops', 'fetch'])
            if result.returncode != 0:
                raise TropsError('trops fetch failed')

        # Create a temporary index path and ensure it does not exist on disk
        fd, tmp_index_path = tempfile.mkstemp(prefix='trops_idx_')
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            if os.path.exists(tmp_index_path):
                os.unlink(tmp_index_path)
        except Exception:
            pass

        # Preserve original env
        orig_index = os.environ.get('GIT_INDEX_FILE')
        try:
            os.environ['GIT_INDEX_FILE'] = tmp_index_path
            for env_name in self.envs:
                # Pull km_dir from config for each env
                try:
                    km_dir = self.config[env_name]['km_dir']
                except KeyError:
                    # Non-fatal: skip this env with a warning to stderr
                    print(f"WARNING: skipping env '{env_name}' due to missing km_dir", flush=True)
                    continue

                # If km_dir begins with '/', remove only the first '/' for the git ref
                km_dir_ref = km_dir[1:] if km_dir.startswith('/') else km_dir

                # 1) read-tree (no prefix; will override work-tree on checkout)
                read_tree_args = [
                    'read-tree', f'origin/trops/{env_name}:{km_dir_ref}'
                ]
                self._git_for_env(env_name, read_tree_args)

                # 2) checkout-index with overridden work-tree to target output directory
                checkout_args = [f'--work-tree={self.target_prefix}', 'checkout-index', '-a']
                if getattr(self.args, 'force', False):
                    checkout_args.append('-f')  # force overwrite
                self._git_for_env(env_name, checkout_args)
        finally:
            # Cleanup env var and temp file
            if orig_index is None:
                os.environ.pop('GIT_INDEX_FILE', None)
            else:
                os.environ['GIT_INDEX_FILE'] = orig_index
            try:
                if os.path.exists(tmp_index_path):
                    os.unlink(tmp_index_path)
            except Exception:
                pass


def run(args, other_args):
    tg = TropsTablogGet(args, other_args)
    tg.run()


# ===== tablog join =====

HEADERS = [
    'Date',
    'Time',
    'User@host',
    'Command',
    'Directory/O,G,M',
    'Exit'
]


class TropsTablogJoin:
    def __init__(self, args, other_args):
        self.args = args
        self.other_args = other_args

        if other_args:
            msg = f"""\
                Unsupported argments: {', '.join(other_args)}
                > trops tablog join --help"""
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


def run_join(args, other_args):
    tj = TropsTablogJoin(args, other_args)
    tj.run()


def _tablog_help(args, other_args):
    # Fallback handler when no subcommand is provided
    print(dedent('''\
        usage: trops tablog <command> [<args>]
        
        Commands:
          get     extract km files to a target path using a temporary index
          join    join multiple KM markdown tables into a single, time-sorted table
    '''))


def add_tablog_subparsers(subparsers):
    parser_tablog = subparsers.add_parser('tablog', help='table/log utilities')
    tablog_sub = parser_tablog.add_subparsers()

    # tablog get
    parser_get = tablog_sub.add_parser('get', help='extract km files to a target path using a temporary index')
    group = parser_get.add_mutually_exclusive_group(required=False)
    group.add_argument('-a', '--all', action='store_true', help='process all environments found in config')
    group.add_argument('-e', '--env', help='process a specific environment name')
    parser_get.add_argument('-f', '--force', action='store_true', help='overwrite existing files in the target directory')
    parser_get.add_argument('-u', '--update', action='store_true', help='run "trops fetch" before extracting')
    parser_get.add_argument('path', help='target directory path to extract files into (used as --prefix)')
    parser_get.set_defaults(handler=run)

    # tablog join
    parser_join = tablog_sub.add_parser('join', help='join multiple KM markdown tables into a single, time-sorted table')
    parser_join.add_argument('files', nargs='+', help='input markdown files to merge')
    parser_join.add_argument('-o', '--output', required=True, help='output file path')
    # support both --append and misspelled --apend for convenience
    parser_join.add_argument('-a', '--append', '--apend', dest='append', action='store_true', help='append to the output file instead of overwriting')
    parser_join.set_defaults(handler=run_join)

    # If no subcommand is given, show help
    parser_tablog.set_defaults(handler=_tablog_help)


