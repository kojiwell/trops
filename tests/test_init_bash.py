import os
import shutil
import subprocess

import pytest

from trops.init import TropsInit


def _bash_init_script():
    ti = TropsInit.__new__(TropsInit)
    return ti._init_bash()


def test_init_bash_uses_debug_trap():
    script = _bash_init_script()
    assert 'trap "_trops_debug' in script
    assert '_trops_arm' in script
    assert 'declare -ft ontrops offtrops' in script
    # Captured command must not come from fc anymore
    assert 'fc -ln' not in script


def _run_interactive_bash(tmp_path, lines, histcontrol=''):
    init_file = tmp_path / 'init.bash'
    init_file.write_text(_bash_init_script())

    bindir = tmp_path / 'bin'
    bindir.mkdir()
    stub = bindir / 'trops'
    stub.write_text(
        '#!/bin/sh\n'
        '[ "$1" = gensid ] && { echo sid; exit 0; }\n'
        'printf "CALL:"; for a in "$@"; do printf " [%s]" "$a"; done; echo\n'
    )
    stub.chmod(0o755)

    env = {
        'HOME': str(tmp_path),
        'PATH': f'{bindir}:/usr/bin:/bin',
        'HISTFILE': str(tmp_path / 'hist'),
        'HISTCONTROL': histcontrol,
        'TERM': 'dumb',
    }
    script = [f'source {init_file}'] + lines
    proc = subprocess.run(
        [shutil.which('bash'), '--norc', '--noprofile', '-i'],
        input='\n'.join(script) + '\n',
        capture_output=True, text=True, env=env, timeout=30,
    )
    out = proc.stdout + proc.stderr
    calls = [ln[ln.index('CALL:'):] for ln in out.splitlines() if 'CALL:' in ln]
    return calls, out


needs_bash = pytest.mark.skipif(shutil.which('bash') is None, reason='bash not installed')


@needs_bash
def test_init_bash_hooks_capture_executed_commands(tmp_path):
    calls, _ = _run_interactive_bash(tmp_path, [
        "PROMPT_COMMAND='true; true'",
        'ontrops test',
        'echo hello world',
        '',              # empty Enter must not re-log the last command
        '',
        'false',
        ' echo spaced',  # not stored in history (HISTCONTROL=ignorespace)
        'echo a | cat',
        'offtrops',
        'echo after-off',
        'echo "PC=[$PROMPT_COMMAND]"',
    ], histcontrol='ignorespace')
    assert calls == [
        'CALL: [capture-cmd] [0] [echo] [hello] [world]',
        'CALL: [capture-cmd] [1] [false]',
        'CALL: [capture-cmd] [0] [echo] [spaced]',
        'CALL: [capture-cmd] [0] [echo] [a] [|] [cat]',
    ]


@needs_bash
def test_init_bash_restores_prompt_command_and_debug_trap(tmp_path):
    calls, out = _run_interactive_bash(tmp_path, [
        "PROMPT_COMMAND='true; true'",
        "trap 'N=$((N+1))' DEBUG",
        'ontrops test',
        'ontrops test',  # idempotent
        'N=0',
        'echo x',
        'echo "N=$N" >&2',
        'offtrops',
        'echo "PC=[$PROMPT_COMMAND]" >&2',
        'trap -p DEBUG >&2',
    ])
    assert 'CALL: [capture-cmd] [0] [echo] [x]' in calls
    # The pre-existing DEBUG trap kept running while trops was on
    n_lines = [ln for ln in out.splitlines() if ln.startswith('N=')]
    assert n_lines and int(n_lines[0][2:]) > 0
    # offtrops restores the original PROMPT_COMMAND and DEBUG trap
    assert 'PC=[true; true]' in out
    assert "trap -- 'N=$((N+1))' DEBUG" in out


@needs_bash
def test_init_bash_cleans_up_legacy_prompt_command(tmp_path):
    # PROMPT_COMMAND left by an older `trops init bash`
    calls, out = _run_interactive_bash(tmp_path, [
        "PROMPT_COMMAND='_trops_capcmd;'",
        'ontrops test',
        'echo x',
        'offtrops',
        'echo "PC=[$PROMPT_COMMAND]" >&2',
    ])
    assert calls == ['CALL: [capture-cmd] [0] [echo] [x]']
    assert 'PC=[]' in out
