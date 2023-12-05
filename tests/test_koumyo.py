import io
import pytest
import argparse

from textwrap import dedent
from unittest.mock import patch

from trops.koumyo import TropsKoumyo, add_koumyo_subparsers

TEST_LOGS = """\
2023-04-21 14:27:59 user1@node01 WARNING CM ls -la  #> PWD=/home/user1, EXIT=0, TROPS_SID=hyn7224, TROPS_ENV=node01 TROPS_TAGS=#124,test
2023-04-21 14:27:59 user1@node01 WARNING CM ls -la  asdfasdf  #> PWD=/home/user1, EXIT=2, TROPS_SID=hyn7224, TROPS_ENV=node01 TROPS_TAGS=#124,test"""


@pytest.fixture
def setup_koumyo_args():
    with patch("sys.argv", ["trops", "km"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_koumyo_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_sys_stdin_read(monkeypatch, setup_koumyo_args):
    args, other_args = setup_koumyo_args

    list_test_logs = TEST_LOGS.splitlines()

    monkeypatch.setattr('sys.stdin', io.StringIO(TEST_LOGS))

    tk = TropsKoumyo(args, other_args)
    assert len(tk.logs) == len(list_test_logs)
    assert all([a == b for a, b in zip(tk.logs, list_test_logs)])


def test_ignore_empty_cmd(monkeypatch, setup_koumyo_args):
    args, other_args = setup_koumyo_args

    list_test_logs = TEST_LOGS.splitlines()

    monkeypatch.setattr('sys.stdin', io.StringIO(TEST_LOGS))

    tk = TropsKoumyo(args, other_args)
    tk._ignore_cmd([])