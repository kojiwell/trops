import os
import tempfile
from configparser import ConfigParser
from textwrap import dedent

import subprocess


from .trops import TropsError


class TropsGetKm:
    def __init__(self, args, other_args):
        self.args = args
        self.other_args = other_args

        if other_args:
            msg = f"""\
                Unsupported argments: {', '.join(other_args)}
                > trops getkm --help"""
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
    gk = TropsGetKm(args, other_args)
    gk.run()


def add_getkm_subparsers(subparsers):
    parser_getkm = subparsers.add_parser('getkm', help='extract km files to a target path using a temporary index')
    group = parser_getkm.add_mutually_exclusive_group(required=False)
    group.add_argument('-a', '--all', action='store_true', help='process all environments found in config')
    group.add_argument('-e', '--env', help='process a specific environment name')
    parser_getkm.add_argument('-f', '--force', action='store_true', help='overwrite existing files in the target directory')
    parser_getkm.add_argument('-u', '--update', action='store_true', help='run "trops fetch" before extracting')
    parser_getkm.add_argument('path', help='target directory path to extract files into (used as --prefix)')
    parser_getkm.set_defaults(handler=run)


