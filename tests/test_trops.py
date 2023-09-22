import argparse
import os
import pytest

from unittest.mock import patch

from trops.trops import Trops, TropsMain
from trops.init import TropsInit, add_init_subparsers


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