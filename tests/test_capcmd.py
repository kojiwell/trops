import argparse
import os
import pytest

from unittest.mock import patch

from trops.capcmd import TropsCapCmd, add_capture_cmd_subparsers


@pytest.fixture
def setup_capcmd_args(monkeypatch):
    #monkeypatch.setenv("TROPS_DIR", '/tmp/trops')
    #monkeypatch.setenv("TROPS_ENV", 'test')
    #monkeypatch.setenv("TROPS_TAGS", '#123,TEST')
    with patch("sys.argv", ["trops", "capture-cmd", '0', "echo", "hello", "world"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_capcmd(monkeypatch, setup_capcmd_args):
    args, other_args = setup_capcmd_args

    tcc = TropsCapCmd(args, other_args)
    #assert tcc.trops_dir == '/tmp/trops'
    assert tcc.trops_header[3] == ''