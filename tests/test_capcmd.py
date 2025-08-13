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


def test_capcmd_ignores_sudo_ttags(monkeypatch, tmp_path, capsys):
    # TROPS_DIR is required
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TROPS_DIR", str(trops_dir))

    from unittest.mock import patch
    import argparse
    from trops.capcmd import add_capture_cmd_subparsers, capture_cmd

    # Build args simulating: trops capture-cmd 0 sudo ttags
    with patch("sys.argv", ["trops", "capture-cmd", '0', "sudo", "ttags"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    import pytest
    with pytest.raises(SystemExit) as exc:
        capture_cmd(args, other_args)

    out = capsys.readouterr().out
    # Should exit with code 0 after printing header
    assert exc.value.code == 0
    assert "-= trops|||- =-" in out or "-= trops" in out


def test_capcmd_calls_track_editor_files_for_editors(monkeypatch, tmp_path):
    # Ensure TROPS_DIR
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TROPS_DIR", str(trops_dir))

    from unittest.mock import patch
    import argparse
    from trops.capcmd import add_capture_cmd_subparsers, capture_cmd, TropsCapCmd

    # Stub method to observe call
    called_with = {}
    def stub_track(self, executed_cmd):
        called_with['args'] = executed_cmd

    monkeypatch.setattr(TropsCapCmd, '_track_editor_files', stub_track, raising=True)

    # Simulate: trops capture-cmd 0 vim /tmp/file.txt
    with patch("sys.argv", ["trops", "capture-cmd", '0', "vim", "/tmp/file.txt"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    # Run; should not raise SystemExit here (not ignored)
    capture_cmd(args, other_args)

    assert called_with.get('args') == ["vim", "/tmp/file.txt"]


def test_file_is_in_git_repo_avoids_chdir(monkeypatch, tmp_path):
    import os as _os
    # Stub os.chdir to detect if it's called
    chdir_called = {"used": False}

    def fake_chdir(_):
        chdir_called["used"] = True

    monkeypatch.setattr(_os, 'chdir', fake_chdir, raising=True)

    # Create a dummy file path (not in a git repo)
    p = tmp_path / 'sub' / 'file.txt'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('x', encoding='utf-8')

    from trops.capcmd import file_is_in_a_git_repo
    _ = file_is_in_a_git_repo(str(p))

    # Ensure no chdir was used
    assert chdir_called["used"] is False


def test_capcmd_ignore_skips_side_effects(monkeypatch, tmp_path, capsys):
    # TROPS_DIR is required
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TROPS_DIR", str(trops_dir))

    from unittest.mock import patch
    import argparse
    from trops.capcmd import add_capture_cmd_subparsers, capture_cmd, TropsCapCmd

    called = {"track": False, "tee": False}

    def fake_track(self, executed_cmd):
        called["track"] = True

    def fake_tee(self, executed_cmd):
        called["tee"] = True
        return False

    monkeypatch.setattr(TropsCapCmd, '_track_editor_files', fake_track, raising=True)
    monkeypatch.setattr(TropsCapCmd, '_add_tee_output_file', fake_tee, raising=True)

    # Build args simulating: trops capture-cmd 0 ttags (ignored)
    with patch("sys.argv", ["trops", "capture-cmd", '0', "ttags"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    import pytest
    with pytest.raises(SystemExit) as exc:
        capture_cmd(args, other_args)

    assert exc.value.code == 0
    # Ensure side-effect methods were not called
    assert called["track"] is False
    assert called["tee"] is False


def test_ignore_cmds_is_set_for_fast_membership(monkeypatch, tmp_path):
    # TROPS_DIR is required
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TROPS_DIR", str(trops_dir))

    from unittest.mock import patch
    import argparse
    from trops.capcmd import add_capture_cmd_subparsers, TropsCapCmd

    with patch("sys.argv", ["trops", "capture-cmd", '0', "echo", "hi"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tcc = TropsCapCmd(args, other_args)
    assert isinstance(tcc.ignore_cmds, set)
    assert 'ttags' in tcc.ignore_cmds


def test_editor_file_log_is_deferred_until_after_command(monkeypatch, tmp_path, caplog):
    import logging
    import subprocess
    from trops.capcmd import add_capture_cmd_subparsers, capture_cmd

    # Prepare TROPS_DIR and config pointing to an external git_dir and a clean work_tree
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TROPS_DIR", str(trops_dir))
    monkeypatch.setenv("TROPS_ENV", "env1")

    repo_root = tmp_path / 'repo'
    work_tree = tmp_path / 'work_tree'
    repo_root.mkdir(parents=True, exist_ok=True)
    work_tree.mkdir(parents=True, exist_ok=True)

    # Initialize a git repository in repo_root (non-bare) and configure identity
    subprocess.run(['git', 'init', str(repo_root)], check=True, capture_output=True)
    git_dir = repo_root / '.git'
    subprocess.run(['git', f'--git-dir={git_dir}', 'config', 'user.email', 'test@example.com'], check=True)
    subprocess.run(['git', f'--git-dir={git_dir}', 'config', 'user.name', 'Test User'], check=True)

    # Write trops.cfg
    cfg = (trops_dir / 'trops.cfg')
    cfg.write_text(
        f"""
[env1]
git_dir = {git_dir}
work_tree = {work_tree}
disable_header = True
""".strip(),
        encoding='utf-8'
    )

    # Create a file to be edited under work_tree
    edited_file = work_tree / 'dir' / 'file.txt'
    edited_file.parent.mkdir(parents=True, exist_ok=True)
    edited_file.write_text('hello', encoding='utf-8')

    # Build args simulating: trops capture-cmd 0 vi <abs_path>
    from unittest.mock import patch
    import argparse
    with patch("sys.argv", ["trops", "capture-cmd", '0', "vi", str(edited_file)]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_capture_cmd_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    caplog.set_level(logging.INFO)

    # Execute capture
    capture_cmd(args, other_args)

    # Collect relevant log messages
    messages = [rec.getMessage() for rec in caplog.records]
    cm_indices = [i for i, m in enumerate(messages) if m.startswith('CM vi ')]
    fl_indices = [i for i, m in enumerate(messages) if m.startswith('FL trops show ')]

    # Ensure both logs are present
    assert cm_indices, f"No command log found in: {messages}"
    assert fl_indices, f"No file log found in: {messages}"

    # Verify ordering: command log should appear before file log
    assert cm_indices[0] < fl_indices[0], f"Expected CM before FL; got order: {[(i, messages[i]) for i in (cm_indices[0], fl_indices[0])]}"
