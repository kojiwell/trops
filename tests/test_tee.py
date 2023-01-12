import os
import argparse
import pytest

from unittest.mock import patch

from trops.tee import TropsTee, add_tee_subparsers

@pytest.fixture()
def tt():

    return TropsTee

@pytest.fixture
def setup_tee_args():
    with patch( "sys.argv", [ "trops", "tee", "bash", "o_var1", "o_var2"] ):
        parser = argparse.ArgumentParser(prog='trops',description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_tee_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args

def test_trops_dir(monkeypatch, setup_tee_args):
    args, other_args = setup_tee_args
    tt = TropsTee(args, other_args)

    monkeypatch.setenv("TROPS_DIR", os.path.expanduser('~/trops'))
    
    assert tt.hello_world() == "Hello world!"
    #assert tt.trops_dir ==  os.path.expanduser('~/trops')