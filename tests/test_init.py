import pytest
import argparse
import os
import shutil
import subprocess

from unittest.mock import patch

from trops.init import TropsInit, add_init_subparsers


@pytest.fixture
def setup_init_args():
    with patch("sys.argv", ["trops", "init", "bash", "o_var1", "o_var2"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_init_args(setup_init_args):
    args, other_args = setup_init_args
    assert args.shell == 'bash'
    assert other_args == ['o_var1', 'o_var2']


def test_init_unsupported_args(setup_init_args):
    args, other_args = setup_init_args
    from trops.trops import TropsError
    with pytest.raises(TropsError):
        ti = TropsInit(args, other_args)


@pytest.mark.parametrize('var', ['bash', 'zsh'])
def test_init_shell_values(var):
    with patch("sys.argv", ["trops", "init", var]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_init_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
        ti = TropsInit(args, other_args)


def _zsh_init_script():
    ti = TropsInit.__new__(TropsInit)
    return ti._init_zsh()


def test_init_zsh_uses_preexec_hook():
    script = _zsh_init_script()
    assert 'add-zsh-hook preexec _tr_preexec' in script
    assert 'add-zsh-hook precmd _tr_capcmd' in script
    assert 'add-zsh-hook -D preexec _tr_preexec' in script
    assert 'add-zsh-hook -D precmd _tr_capcmd' in script
    # Captured command must not come from history anymore
    assert 'fc -ln' not in script


@pytest.mark.skipif(shutil.which('zsh') is None, reason='zsh not installed')
def test_init_zsh_hooks_capture_executed_commands(tmp_path):
    init_file = tmp_path / 'init.zsh'
    init_file.write_text(_zsh_init_script())

    bindir = tmp_path / 'bin'
    bindir.mkdir()
    stub = bindir / 'trops'
    stub.write_text(
        '#!/bin/sh\n'
        '[ "$1" = gensid ] && { echo sid; exit 0; }\n'
        'printf "CALL:"; for a in "$@"; do printf " [%s]" "$a"; done; echo\n'
    )
    stub.chmod(0o755)

    lines = [
        f'source {init_file}',
        'ontrops test',
        'echo hello world',
        '',              # empty Enter must not re-log the last command
        '',
        'false',
        ' echo spaced',  # not stored in history (HIST_IGNORE_SPACE)
        'offtrops',
        'echo after-off',
    ]
    env = dict(os.environ, PATH=f'{bindir}:{os.environ["PATH"]}')
    proc = subprocess.run(
        ['zsh', '-f', '-i', '-o', 'histignorespace'],
        input='\n'.join(lines) + '\n',
        capture_output=True, text=True, env=env, timeout=30,
    )
    calls = [ln[ln.index('CALL:'):] for ln in proc.stdout.replace('\r', '\n').splitlines()
             if 'CALL:' in ln]
    assert calls == [
        'CALL: [capture-cmd] [0] [echo] [hello] [world]',
        'CALL: [capture-cmd] [1] [false]',
        'CALL: [capture-cmd] [0] [echo] [spaced]',
    ]
