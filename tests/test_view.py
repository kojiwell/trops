import argparse
import pytest

from unittest.mock import patch

from trops.view import TropsView, add_view_subparsers


@pytest.fixture
def setup_view_args():
    with patch("sys.argv", ["trops", "view", "/tmp/test"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_view_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    return args, other_args


def test_view_invokes_git_show(monkeypatch, setup_view_args):
    args, other_args = setup_view_args

    # Monkeypatch TropsMain.__init__ to avoid reading real config
    def fake_init(self, a, b):
        self.args = a
        self.other_args = b
        self.work_tree = '/'
        self.git_cmd = ['echo', 'git']
    monkeypatch.setattr('trops.view.TropsMain.__init__', fake_init)

    called = {}
    def fake_call(cmd):
        called['cmd'] = cmd
        return 0
    monkeypatch.setattr('subprocess.call', fake_call)

    tv = TropsView(args, other_args)
    tv.view()

    assert called['cmd'] == ['echo', 'git', 'show', 'HEAD:tmp/test']


def test_view_commit_override(monkeypatch):
    with patch("sys.argv", ["trops", "view", "--commit", "HEAD~1", "/tmp/test2"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_view_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    def fake_init(self, a, b):
        self.args = a
        self.other_args = b
        self.work_tree = '/'
        self.git_cmd = ['echo', 'git']
    monkeypatch.setattr('trops.view.TropsMain.__init__', fake_init)

    captured = {}
    def fake_call(cmd):
        captured['cmd'] = cmd
        return 0
    monkeypatch.setattr('subprocess.call', fake_call)

    tv = TropsView(args, other_args)
    tv.view()

    assert captured['cmd'] == ['echo', 'git', 'show', 'HEAD~1:tmp/test2']


def test_view_requires_file_argument():
    with patch("sys.argv", ["trops", "view"]):
        parser = argparse.ArgumentParser(prog='trops', description='Trops - Tracking Operations')
        subparsers = parser.add_subparsers()
        add_view_subparsers(subparsers)
        with pytest.raises(SystemExit):
            _ = parser.parse_known_args()


