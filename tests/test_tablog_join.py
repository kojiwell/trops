import argparse
from unittest.mock import patch

import pytest

from trops.tablog import add_tablog_subparsers, run_join as tablog_join_run


def _write(path, content: str):
    path.write_text(content, encoding='utf-8')


def test_tablog_join_requires_output(tmp_path):
    f1 = tmp_path / 'f1.md'
    _write(
        f1,
        """
| Date | Time | User@host | Command | Directory/O,G,M | Exit |
| --- | --- | --- | --- | --- | --- |
| 2025-08-12 | 12:03:49 | root@host | cmd1 | /root | 0 |
        """.strip()
    )

    with patch('sys.argv', ['trops', 'tablog', 'join', str(f1)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        with pytest.raises(SystemExit):
            _ = parser.parse_known_args()


def test_tablog_join_merges_and_sorts(tmp_path):
    # Prepare three input files
    f1 = tmp_path / 'file1.md'
    f2 = tmp_path / 'file2.md'
    f3 = tmp_path / 'file3.md'
    out = tmp_path / 'out.md'

    _write(
        f1,
        """
| Date       | Time     | User@host       | Command | Directory/O,G,M      | Exit   |
|------------|----------|-----------------|---------|----------------------|--------|
| 2025-08-12 | 12:03:49 | root@myhost01     | A       | /root                | 0      |
| 2025-08-12 | 12:03:52 | root@myhost01     | B       | /root                | 0      |
        """.strip()
    )

    _write(
        f2,
        """
| Date       | Time     | User@host     | Command | Directory/O,G,M       | Exit   |
|------------|----------|---------------|---------|-----------------------|--------|
| 2025-08-07 | 14:40:25 | root@myhost01   | C       | /root/myops/ansible | 0      |
        """.strip()
    )

    _write(
        f3,
        """
| Date       | Time     | User@host   | Command | Directory/O,G,M      | Exit   |
|------------|----------|-------------|---------|----------------------|--------|
| 2025-08-10 | 12:50:15 | root@myhost01 | D       | /root                | 0      |
| 2025-08-10 | 12:50:23 | root@myhost01 | E       | /root                | 0      |
        """.strip()
    )

    # Build CLI args and run
    with patch('sys.argv', ['trops', 'tablog', 'join', str(f1), str(f2), str(f3), '-o', str(out)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()

    tablog_join_run(args, other_args)

    # Validate output
    text = out.read_text(encoding='utf-8').strip().splitlines()

    # header + separator + 5 rows
    assert len(text) == 7
    assert text[0].startswith('| Date') and text[0].endswith('|')
    assert text[1].startswith('| ---')

    # Ascending by Date+Time
    rows = text[2:]
    assert rows[0].startswith('| 2025-08-07 | 14:40:25 |')
    assert rows[1].startswith('| 2025-08-10 | 12:50:15 |')
    assert rows[2].startswith('| 2025-08-10 | 12:50:23 |')
    assert rows[3].startswith('| 2025-08-12 | 12:03:49 |')
    assert rows[4].startswith('| 2025-08-12 | 12:03:52 |')


def test_tablog_join_append_mode(tmp_path):
    # Initial output
    out = tmp_path / 'out.md'
    f1 = tmp_path / 'f1.md'
    f2 = tmp_path / 'f2.md'

    _write(
        f1,
        """
| Date | Time | User@host | Command | Directory/O,G,M | Exit |
| --- | --- | --- | --- | --- | --- |
| 2025-08-01 | 10:00:00 | u@h | X | /d | 0 |
        """.strip()
    )

    # First write (overwrite)
    with patch('sys.argv', ['trops', 'tablog', 'join', str(f1), '-o', str(out)]):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    tablog_join_run(args, other_args)

    text1 = out.read_text(encoding='utf-8').strip().splitlines()
    assert len(text1) == 3  # header, sep, 1 row

    # Prepare second input and append using -a (also accept --apend alias)
    _write(
        f2,
        """
| Date | Time | User@host | Command | Directory/O,G,M | Exit |
| --- | --- | --- | --- | --- | --- |
| 2025-08-02 | 11:00:00 | u@h | Y | /d | 1 |
        """.strip()
    )

    with patch('sys.argv', ['trops', 'tablog', 'join', str(f2), '-o', str(out), '--apend']):
        parser = argparse.ArgumentParser(prog='trops')
        subparsers = parser.add_subparsers()
        add_tablog_subparsers(subparsers)
        args, other_args = parser.parse_known_args()
    tablog_join_run(args, other_args)

    text2 = out.read_text(encoding='utf-8').strip().splitlines()
    # First block: 3 lines, then append writes another header+sep+row -> +3 lines
    assert len(text2) == 6
    # First block header
    assert text2[0].startswith('| Date')
    # First block row
    assert text2[2].startswith('| 2025-08-01 | 10:00:00 |')
    # Second block header
    assert text2[3].startswith('| Date')
    # Second block row
    assert text2[5].startswith('| 2025-08-02 | 11:00:00 |')


