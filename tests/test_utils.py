import pytest

from trops.utils import (strtobool,
                         pick_out_repo_name_from_git_remote)

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

def test_pick_out_repo_name_from_git_remote():
    git_remote = "git@github.com/username/test.git_g.git"
    assert pick_out_repo_name_from_git_remote(git_remote) == "test.git_g"


def test_sid_seed_text_properties():
    from trops.utils import sid_seed_text
    s = sid_seed_text()
    assert isinstance(s, str) and len(s) > 0
    assert all(c.isalnum() for c in s)


def test_generate_sid_format(capsys):
    # generate_sid prints a 7-char string: 3 lowercase letters + 4 hex chars
    from trops.utils import generate_sid
    generate_sid(None, None)
    out = capsys.readouterr().out
    import re
    assert re.fullmatch(r"[a-z]{3}[0-9a-f]{4}\n", out) is not None