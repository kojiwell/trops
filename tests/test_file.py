import argparse
import os
import pytest

from unittest.mock import patch

from trops.file import TropsFile, add_file_subparsers


@pytest.fixture
def setup_file_args():
    with patch("sys.argv", ["trops", "file", "list"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_file_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_file(monkeypatch, setup_file_args):
    args, other_args = setup_file_args

    monkeypatch.setenv("TROPS_DIR", '/tmp/trops')
    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')
    tf = TropsFile(args, other_args)
