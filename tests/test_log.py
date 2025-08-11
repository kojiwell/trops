import argparse
import pytest

from unittest.mock import patch

from trops.log import TropsLog, add_log_subparsers
from trops.log import check_tags


@pytest.fixture
def setup_log_args():
    with patch("sys.argv", ["trops", "log"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_log_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_log(monkeypatch, setup_log_args):
    args, other_args = setup_log_args

    monkeypatch.setenv("TROPS_DIR", '/tmp/trops')
    monkeypatch.setenv("TROPS_ENV", 'testenv')
    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')
    tl = TropsLog(args, other_args)

def test_log_save(monkeypatch, setup_log_args):
    args, other_args = setup_log_args
    monkeypatch.setattr(args, 'save', True, raising=False)
    monkeypatch.setenv("TROPS_TAGS", "#22")

    assert args.save == True

    tl = TropsLog(args, other_args)
    assert tl.trops_logfile == '/home/devuser/trops/log/trops.log'
    assert tl.trops_tags == '#22'

def test_prim_tag(monkeypatch, setup_log_args):
    args, other_args = setup_log_args

    monkeypatch.setenv("TROPS_DIR", '/tmp/trops')
    monkeypatch.setenv("TROPS_ENV", 'testenv')
    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')
    tl = TropsLog(args, other_args)
    assert tl.trops_prim_tag == '#123'


def test_check_tags_any_match():
    # Simulated log line containing multiple tags
    line = "2024-01-01 00:00:00 user@host INFO CM echo ok #> PWD=/, EXIT=0 TROPS_TAGS=tag1,tag2,tag3"

    assert check_tags('tag1', line) is True
    assert check_tags('tag1,tag3', line) is True
    assert check_tags('tag3', line) is True


def test_log_without_filters_prints_all(monkeypatch, tmp_path, setup_log_args, capsys):
    args, other_args = setup_log_args

    # Ensure no filters
    if hasattr(args, 'all'):
        monkeypatch.setattr(args, 'all', False, raising=False)
    if hasattr(args, 'save'):
        monkeypatch.setattr(args, 'save', False, raising=False)
    monkeypatch.delenv('TROPS_TAGS', raising=False)
    monkeypatch.delenv('TROPS_SID', raising=False)

    # Point TROPS_DIR to a temporary directory and create a log file
    trops_dir = tmp_path / 'trops'
    log_dir = trops_dir / 'log'
    log_dir.mkdir(parents=True)
    log_file = log_dir / 'trops.log'
    log_file.write_text('first line\nsecond line\n', encoding='utf-8')

    # Set TROPS_DIR to the trops directory so Trops will read the file we wrote
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))

    tl = TropsLog(args, other_args)
    tl.log()

    out = capsys.readouterr().out
    assert out == 'first line\nsecond line\n'