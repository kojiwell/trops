import io
import pytest
import argparse

from textwrap import dedent
from unittest.mock import patch

from trops.koumyo import TropsKoumyo, add_koumyo_subparsers

TEST_LOGS = """\
2023-04-21 14:27:59 user1@node01 WARNING CM ls -la  #> PWD=/home/user1, EXIT=0, TROPS_SID=hyn7224, TROPS_ENV=node01 TROPS_TAGS=#124,test
2023-04-21 14:27:59 user1@node01 WARNING CM ls -la  asdfasdf  #> PWD=/home/user1, EXIT=2, TROPS_SID=hyn7224, TROPS_ENV=node01 TROPS_TAGS=#124,test"""


@pytest.fixture
def setup_koumyo_args():
    with patch("sys.argv", ["trops", "km"]):
        parser = argparse.ArgumentParser(
            prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_koumyo_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_sys_stdin_read(monkeypatch, setup_koumyo_args):
    args, other_args = setup_koumyo_args

    list_test_logs = TEST_LOGS.splitlines()

    monkeypatch.setattr('sys.stdin', io.StringIO(TEST_LOGS))

    tk = TropsKoumyo(args, other_args)
    assert len(tk.logs) == len(list_test_logs)
    assert all([a == b for a, b in zip(tk.logs, list_test_logs)])


def test_ignore_empty_cmd(monkeypatch, setup_koumyo_args):
    args, other_args = setup_koumyo_args

    list_test_logs = TEST_LOGS.splitlines()

    monkeypatch.setattr('sys.stdin', io.StringIO(TEST_LOGS))

    tk = TropsKoumyo(args, other_args)
    tk._ignore_cmd([])


def test_km_save_filename_includes_repo_env_and_tag(monkeypatch, tmp_path):
    # Prepare minimal Trops env
    trops_dir = tmp_path / 'trops'
    trops_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('TROPS_DIR', str(trops_dir))
    monkeypatch.setenv('TROPS_ENV', 'myenv')
    monkeypatch.setenv('TROPS_TAGS', 'task-17')

    # Create minimal config with git_dir/work_tree and git_remote
    git_dir = tmp_path / 'repo' / '.git'
    work_tree = tmp_path / 'work'
    work_tree.mkdir(parents=True, exist_ok=True)
    git_dir.parent.mkdir(parents=True, exist_ok=True)
    (trops_dir / 'trops.cfg').write_text(
        dedent(f"""
        [myenv]
        git_dir = {git_dir}
        work_tree = {work_tree}
        git_remote = git@github.com:kojiwell/testmyenv.git
        disable_header = True
        """),
        encoding='utf-8'
    )

    # Provide stdin logs
    logs = "2025-08-13 00:00:00 u@h WARNING CM vi /etc/hosts  #> PWD=/, EXIT=0, TROPS_ENV=myenv TROPS_TAGS=task-17\n"
    monkeypatch.setattr('sys.stdin', io.StringIO(logs))

    # Stub git interactions used by _touch_file to avoid real git
    from trops.trops import TropsMain
    def fake_touch(self, file_path):
        pass
    monkeypatch.setattr(TropsMain, '_touch_file', fake_touch, raising=True)

    # Run with --save
    with patch("sys.argv", ["trops", "km", "-s"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_koumyo_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tk = TropsKoumyo(args, other_args)
    tk.run()

    expected = trops_dir / 'km' / 'testmyenv_myenv_task-17.md'
    assert expected.exists(), f"Expected file not found: {expected}"


def test_split_pipe_in_cmd_splits_pipes_and_redirects(monkeypatch, setup_koumyo_args):
    args, other_args = setup_koumyo_args
    # Provide stdin logs to satisfy constructor
    monkeypatch.setattr('sys.stdin', io.StringIO(TEST_LOGS))
    tk = TropsKoumyo(args, other_args)

    result = tk._split_pipe_in_cmd(['a|b', 'c>>d', 'e|f|g', 'h', 'nochange'])
    assert result == ['a', '|', 'b', 'c', '>>', 'd', 'e', '|', 'f', '|', 'g', 'h', 'nochange']


def test_markdown_escapes_special_characters_in_command(monkeypatch, capsys):
    # Build args with --markdown
    with patch("sys.argv", ["trops", "km", "-m"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_koumyo_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    # Command includes pipe and dollar; presence of '|' prevents declutter ignore
    log = "2025-08-13 00:00:00 u@h WARNING CM echo a|b$c  #> PWD=/, EXIT=0, TROPS_ENV=e TROPS_TAGS=x\n"
    monkeypatch.setattr('sys.stdin', io.StringIO(log))

    tk = TropsKoumyo(args, other_args)
    tk.run()

    out = capsys.readouterr().out
    # Ensure the command cell contains escaped special characters
    assert 'a\\|b\\$c' in out