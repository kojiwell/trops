import pytest

from trops.utils import strtobool

@pytest.mark.parametrize('value', (
    'y', 'Y', 'yes', 't', 'True', 'ON', 1,
))
def test_should_return_true(value):
    assert strtobool(value) is True

@pytest.mark.parametrize('value', (
    'n', 'N', 'no', 'f', 'False', 'OFF', 0,
))
def test_should_return_false(value):
    assert strtobool(value) is False

def test_should_raise_value_error():
    with pytest.raises(ValueError):
        strtobool('Truee')