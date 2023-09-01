import io
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


def test_sys_stdin_read(monkeypatch, setup_tee_args):
    args, other_args = setup_tee_args

    monkeypatch.setattr('sys.stdin', io.StringIO('Test input'))

    tt = TropsTee(args, other_args)
    assert tt.read_output_via_pipe() == 'Test input'
