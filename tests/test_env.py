import argparse
import os
import pytest

from unittest.mock import patch

from trops.env import TropsEnv, add_env_subparsers


@pytest.fixture
def setup_env_args(monkeypatch, tmp_path):
  
    trops_dir = tmp_path / 'trops'
    monkeypatch.setenv("TROPS_DIR", str(trops_dir))
    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')

    with patch("sys.argv", ["trops", "env", "create", "testenv"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_env_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_env(monkeypatch, setup_env_args):
    args, other_args = setup_env_args

    te = TropsEnv(args, other_args)
    # Basic fields
    assert te.trops_env == 'testenv'
    assert te.trops_dir.endswith('/trops')
    assert te.trops_log_dir.endswith('/trops/log')
    assert te.trops_conf.endswith('/trops/trops.cfg')
    assert te.trops_git_dir.endswith('/trops/repo/testenv.git')
    assert te.trops_git_branch == 'trops/testenv'


def test_env_invalid_name_spaces(monkeypatch, tmp_path):
    monkeypatch.setenv("TROPS_DIR", str(tmp_path / 'trops'))
    with patch("sys.argv", ["trops", "env", "create", "bad env"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_env_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    with pytest.raises(SystemExit):
        _ = TropsEnv(args, other_args)


def test_env_git_branch_and_remote(monkeypatch, tmp_path):
    monkeypatch.setenv("TROPS_DIR", str(tmp_path / 'trops'))
    with patch("sys.argv", [
        "trops", "env", "create",
        "--git-branch", "feature/x",
        "--git-remote", "https://example.com/repo.git",
        "myenv",
    ]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_env_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    te = TropsEnv(args, other_args)
    assert te.trops_env == 'myenv'
    assert te.trops_git_branch == 'feature/x'
    assert te.trops_git_remote == 'https://example.com/repo.git'


def test_env_unsupported_other_args(monkeypatch, tmp_path):
    monkeypatch.setenv("TROPS_DIR", str(tmp_path / 'trops'))
    with patch("sys.argv", ["trops", "env", "create", "testenv", "oops"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_env_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    assert other_args == ["oops"]
    with pytest.raises(SystemExit):
        _ = TropsEnv(args, other_args)
