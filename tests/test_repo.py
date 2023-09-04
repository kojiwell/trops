import argparse
import pytest

from unittest.mock import patch

from trops.repo import TropsRepo, add_repo_subparsers


@pytest.fixture
def setup_repo_args():
    with patch("sys.argv", ["trops", "repo"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_repo_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_repo(monkeypatch, setup_repo_args):
    args, other_args = setup_repo_args

    monkeypatch.setenv("TROPS_DIR", '/tmp/trops')
    monkeypatch.setenv("TROPS_ENV", 'testenv')
    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')
    tr = TropsRepo(args, other_args)
