import pytest
import argparse

from unittest.mock import patch

from trops.init import TropsInit, add_init_subparsers

@pytest.fixture
def setup_args():
    with patch( "sys.argv", [ "trops", "init", "bash", "o_var1", "o_var2"] ):
        parser = argparse.ArgumentParser(prog='trops',description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args

def test_args(setup_args):
    args, other_args = setup_args
    assert args.shell == 'bash'
    assert other_args == ['o_var1', 'o_var2']

def test_unsupported_args(setup_args):
    args, other_args = setup_args
    with pytest.raises(SystemExit):
        ti = TropsInit(args, other_args)

@pytest.mark.parametrize('var', ['bash', 'zsh'])
def test_shell_values(var):
    with patch( "sys.argv", [ "trops", "init", var] ):
        parser = argparse.ArgumentParser(prog='trops',description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
        ti = TropsInit(args, other_args)