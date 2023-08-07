import io
import os
import argparse
import pytest

from unittest.mock import patch

from trops.tee import TropsTee, add_tee_subparsers


# Fixture of command line arguments
@pytest.fixture
def setup_tee_args():
    with patch("sys.argv", ["trops", "tee", "path/to/file"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_tee_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_trops_dir(monkeypatch, setup_tee_args):
    args, other_args = setup_tee_args

    # Test ~ (tilda) in TROPS_DIR
    monkeypatch.setenv("TROPS_DIR", '~/trops')
    tt1 = TropsTee(args, other_args)
    assert tt1.trops_dir == os.path.expanduser('~/trops')
    assert tt1.file_path == 'path/to/file'

    # Test an environment variable (e.g. HOME) in TROPS_DIR
    monkeypatch.setenv("TROPS_DIR", '$HOME/trops')
    tt2 = TropsTee(args, other_args)
    assert tt2.trops_dir == os.path.expanduser('~/trops')


def test_sys_stdin_read(monkeypatch, setup_tee_args):
    args, other_args = setup_tee_args

    monkeypatch.setattr('sys.stdin', io.StringIO('Test input'))

    tt = TropsTee(args, other_args)
    assert tt.read_output_via_pipe() == 'Test input'
