import argparse
import os
from unittest.mock import patch

import pytest

from trops.tablog import add_tablog_subparsers, run as tablog_get_run


def _write_cfg(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def test_tablog_get_requires_flag_and_path(monkeypatch, tmp_path, capsys):
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[e1]\nkm_dir=/km1\n")

    with patch('sys.argv', ['trops', 'tablog', 'get']):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        with pytest.raises(SystemExit):
            _ = parser.parse_known_args()


def test_tablog_get_env_missing_in_config(monkeypatch, tmp_path, capsys):
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[e1]\nkm_dir=/km1\n")

    with patch('sys.argv', ['trops', 'tablog', 'get', '-e', 'nope', str(tmp_path / 'out')]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    from trops.trops import TropsError
    with pytest.raises(TropsError):
        tablog_get_run(args, other_args)


def test_tablog_get_invokes_git_with_temp_index_for_env(monkeypatch, tmp_path):
    # Setup TROPS_DIR and config
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[env1]\nkm_dir=/path/to/km\n")

    # Capture os.environ changes and subprocess calls
    calls = []

    # Capture subprocess.run used by tablog get
    import subprocess as _subprocess
    def fake_run(cmd, *args, **kwargs):
        # Ensure temp index env var is set and file does not exist on disk
        idx = os.environ.get('GIT_INDEX_FILE')
        assert idx and not os.path.exists(idx)
        calls.append(cmd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(_subprocess, 'run', fake_run, raising=True)

    # Build CLI args and run
    out_dir = tmp_path / 'out'
    with patch('sys.argv', ['trops', 'tablog', 'get', '-e', 'env1', str(out_dir)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tablog_get_run(args, other_args)

    # Two calls: read-tree and checkout-index -a with work-tree override
    assert calls[0][0:2] == ['git', 'read-tree']
    assert calls[0][2] == 'origin/trops/env1:path/to/km'
    assert calls[1][0] == 'git'
    assert calls[1][1].startswith('--work-tree=')
    assert calls[1][2:] == ['checkout-index', '-a']


def test_tablog_get_overwrite_flag_adds_force(monkeypatch, tmp_path):
    # Setup TROPS_DIR and config
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[env1]\nkm_dir=/path/to/km\n")

    # Capture subprocess calls
    calls = []
    import subprocess as _subprocess
    def fake_run(cmd, *args, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(_subprocess, 'run', fake_run, raising=True)

    # Build CLI args with --overwrite and run
    out_dir = tmp_path / 'out'
    with patch('sys.argv', ['trops', 'tablog', 'get', '-e', 'env1', '-f', str(out_dir)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tablog_get_run(args, other_args)

    # Ensure -f is present in checkout-index command
    assert calls[1][0] == 'git'
    assert calls[1][2] == 'checkout-index'
    assert '-f' in calls[1]


def test_tablog_get_update_runs_fetch(monkeypatch, tmp_path):
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    _write_cfg(trops_dir / 'trops.cfg', "[env1]\nkm_dir=/km\n")

    # Record trops fetch and git calls
    run_calls = []
    import subprocess as _subprocess
    def fake_run(cmd, *args, **kwargs):
        run_calls.append(cmd)
        class R: returncode = 0
        return R()
    monkeypatch.setattr(_subprocess, 'run', fake_run, raising=True)

    out_dir = tmp_path / 'out'
    with patch('sys.argv', ['trops', 'tablog', 'get', '-e', 'env1', '-u', str(out_dir)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tablog_get_run(args, other_args)

    # First call should be trops fetch
    assert run_calls[0][0:2] == ['trops', 'fetch']


