import argparse
import os
import pytest
from pathlib import Path

from unittest.mock import patch

from trops.trops import Trops, TropsMain
from trops.init import add_init_subparsers
from trops.exec import add_git_subparsers


@pytest.fixture
def setup_trops_args(monkeypatch):
    monkeypatch.setenv("TROPS_DIR", '/tmp/trops')
    monkeypatch.setenv("TROPS_ENV", 'test')
    with patch("sys.argv", ["trops", "init", "bash", "o_var1", "o_var2"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_trops_dir(monkeypatch, setup_trops_args):
    args, other_args = setup_trops_args

    # Test ~ (tilda) in TROPS_DIR
    monkeypatch.setenv("TROPS_DIR", '~/trops')
    tb1 = Trops(args, other_args)
    assert tb1.trops_dir == os.path.expanduser('~/trops')
    # Test an environment variable (e.g. HOME) in TROPS_DIR
    monkeypatch.setenv("TROPS_DIR", '$HOME/trops')
    tb2 = Trops(args, other_args)
    assert tb2.trops_dir == os.path.expanduser('~/trops')

def test_trops_vars(monkeypatch, setup_trops_args):
    args, other_args = setup_trops_args

    tm = TropsMain(args, other_args)

    assert tm.trops_dir == '/tmp/trops'
    assert tm.trops_env == 'test'


def test_trops_logfile_path(monkeypatch, tmp_path):
    # Use temp directory to avoid side effects
    trops_dir = tmp_path / 'tropsproj'
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    monkeypatch.setenv('TROPS_ENV', 'env1')

    with patch("sys.argv", ["trops", "init", "bash"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tm = TropsMain(args, other_args)

    assert tm.trops_log_dir == os.path.join(str(trops_dir), 'log')
    assert tm.trops_logfile == os.path.join(str(trops_dir), 'log', 'trops.log')
    # Directories should exist
    assert Path(tm.trops_log_dir).is_dir()


def test_trops_tags_and_primary(monkeypatch, tmp_path):
    trops_dir = tmp_path / 'tropsproj2'
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    monkeypatch.setenv('TROPS_ENV', 'env2')
    # Include spaces to ensure cleanup happens
    monkeypatch.setenv('TROPS_TAGS', ' #123 , TEST ')

    with patch("sys.argv", ["trops", "init", "bash"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tm = TropsMain(args, other_args)

    assert tm.trops_tags == '#123,TEST'
    assert tm.trops_prim_tag == '#123'


def test_git_wrapper_does_not_treat_flags_as_paths(monkeypatch, tmp_path, capsys):
    trops_dir = tmp_path / 'tropsproj3'
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    monkeypatch.setenv('TROPS_ENV', 'env3')

    # Create minimal config
    (trops_dir).mkdir(parents=True, exist_ok=True)
    cfg = trops_dir / 'trops.cfg'
    cfg.write_text(f"""
    [env3]
    git_dir = {tmp_path}/repo/.git
    work_tree = {tmp_path}/work
    disable_header = True
    """.strip(), encoding='utf-8')
    (tmp_path / 'work').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'repo' / '.git').mkdir(parents=True, exist_ok=True)

    # Stub subprocess.run to capture command
    import subprocess as _subprocess
    captured = {}
    def fake_run(cmd, *a, **kw):
        captured['cmd'] = cmd
        class R: returncode = 0
        return R()
    monkeypatch.setattr(_subprocess, 'run', fake_run, raising=True)

    with patch('sys.argv', ['trops', 'git', 'branch', '-ar']):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_git_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    from trops.trops import TropsMain
    tm = TropsMain(args, other_args)
    tm.git()

    # Ensure '-ar' stays as a flag and not rewritten as a path
    assert captured['cmd'][-2:] == ['branch', '-ar']