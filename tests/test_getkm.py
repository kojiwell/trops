import argparse
import os
from unittest.mock import patch

import pytest

from trops.getkm import add_getkm_subparsers, run as getkm_run


def _write_cfg(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def test_getkm_requires_flag_and_path(monkeypatch, tmp_path, capsys):
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[e1]\nkm_dir=/km1\n")

    with patch('sys.argv', ['trops', 'getkm']):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_getkm_subparsers(subparsers)
        with pytest.raises(SystemExit):
            _ = parser.parse_known_args()


def test_getkm_env_missing_in_config(monkeypatch, tmp_path, capsys):
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[e1]\nkm_dir=/km1\n")

    with patch('sys.argv', ['trops', 'getkm', '-e', 'nope', str(tmp_path / 'out')]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_getkm_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    with pytest.raises(SystemExit):
        getkm_run(args, other_args)


def test_getkm_invokes_git_with_temp_index_for_env(monkeypatch, tmp_path):
    # Setup TROPS_DIR and config
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[env1]\nkm_dir=/path/to/km\n")

    # Capture os.environ changes and TropsMain.git invocations
    from trops.trops import TropsMain
    calls = []

    # Bypass real TropsMain __init__ config loading and provide git_cmd
    def fake_init(self, a, b):
        self.args = a
        self.other_args = b
        self.git_cmd = ['echo', 'git']

    # Capture subprocess.run used by getkm
    import subprocess as _subprocess
    def fake_run(cmd, *args, **kwargs):
        # Ensure temp index env var is set and file does not exist on disk
        idx = os.environ.get('GIT_INDEX_FILE')
        assert idx and not os.path.exists(idx)
        calls.append(cmd)
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr('trops.trops.TropsMain.__init__', fake_init, raising=True)
    monkeypatch.setattr(_subprocess, 'run', fake_run, raising=True)

    # Build CLI args and run
    out_dir = tmp_path / 'out'
    with patch('sys.argv', ['trops', 'getkm', '-e', 'env1', str(out_dir)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_getkm_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    getkm_run(args, other_args)

    # Two calls: read-tree and checkout-index -a with work-tree override
    assert calls[0][0:3] == ['echo', 'git', 'read-tree']
    assert calls[0][3] == 'origin/trops/env1:path/to/km'
    assert calls[1][0:2] == ['echo', 'git']
    assert calls[1][2].startswith('--work-tree=')
    assert calls[1][3:] == ['checkout-index', '-a']

