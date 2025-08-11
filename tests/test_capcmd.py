import argparse
import os
import pytest

from unittest.mock import patch

from trops.capcmd import TropsCapCmd, add_capture_cmd_subparsers


@pytest.fixture
def setup_capcmd_args(monkeypatch, tmp_path):
    # Ensure TROPS_DIR is set as capcmd strictly requires it
    monkeypatch.setenv("TROPS_DIR", str(tmp_path / 'trops'))
    with patch("sys.argv", ["trops", "capture-cmd", '0', "echo", "hello", "world"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_capcmd(monkeypatch, setup_capcmd_args):
    args, other_args = setup_capcmd_args

    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')

    tcc = TropsCapCmd(args, other_args)
    assert tcc.trops_header[3] == '#123,TEST'


def test_capcmd_header_positions(monkeypatch, setup_capcmd_args):
    args, other_args = setup_capcmd_args

    monkeypatch.setenv("TROPS_ENV", 'env1')
    monkeypatch.setenv("TROPS_SID", 'sid1')
    monkeypatch.setenv("TROPS_TAGS", '#123,TEST')

    tcc = TropsCapCmd(args, other_args)
    assert tcc.trops_header == ['trops', 'env1', 'sid1', '#123,TEST']


def test_capcmd_errors_when_trops_env_not_in_config(monkeypatch, tmp_path):
    # Set TROPS_DIR and create an empty trops.cfg without the env section
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = trops_dir / 'trops.cfg'
    cfg_path.write_text("", encoding='utf-8')

    monkeypatch.setenv("TROPS_DIR", str(trops_dir))
    monkeypatch.setenv("TROPS_ENV", "missingenv")

    # Build args for capture-cmd
    from unittest.mock import patch
    import argparse
    from trops.capcmd import add_capture_cmd_subparsers, capture_cmd
    with patch("sys.argv", ["trops", "capture-cmd", '0', "echo", "hello"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    import pytest
    with pytest.raises(SystemExit) as exc:
        capture_cmd(args, other_args)

    assert "TROPS_ENV 'missingenv' does not exist in your configuration" in str(exc.value)
