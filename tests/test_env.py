import argparse
import os
import pytest

from unittest.mock import patch

from trops.env import TropsEnv, add_env_subparsers


@pytest.fixture
def setup_env_args(monkeypatch, tmp_path):
  
    trops_dir = tmp_path + '/trops'
    monkeypatch.setenv("TROPS_DIR", trops_dir)
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
