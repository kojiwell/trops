import pytest
import argparse

from unittest.mock import patch

from trops.koumyo import TropsKoumyo, add_koumyo_subparsers

def test_argparse():
    with patch( "sys.argv", [ "trops", "km" ] ):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_koumyo_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
        print(args)
