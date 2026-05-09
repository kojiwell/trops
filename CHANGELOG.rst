*********
Changelog
*********

`Unreleased`_
=============

`v0.2.36`_ - 2026-05-09
=======================
- capcmd: differentiate ``tee`` and ``ttee`` in pipeline detection. Plain ``cmd | tee out`` now commits ``out`` as a transparent passthrough -- the file is no longer mutated. ``cmd | ttee out`` (using the trops-aliased ``ttee`` defined in ``trops init``) commits the file *and* prepends ``# <left-command>`` as the first line, so that the originating command is recorded inside the artifact. ``-a`` / ``--append`` skips the prepend so that growing log files are not silently rewritten. **Backward-compat note**: anyone whose current workflow relied on ``tee`` implicitly prepending ``# <cmd>`` should switch to ``ttee``; existing files in the env git repo are unaffected. (#162)
- perf: cut ``capture-cmd`` baseline overhead by lazy-loading subcommand modules in ``exec.py`` (only the invoked subcommand is imported) and deferring ``subprocess`` / ``re`` imports in ``capcmd.py`` to the editor / tee / package paths that actually need them. Trivial-command import chain drops ~146ms → ~64ms cumulative; user CPU per prompt drops ~50ms → ~30ms (#166).
- capcmd: skip ``tmp/`` ``mkdir`` when the directory already exists; fast-skip the tee-pipeline tokenizer when no ``|`` is in the command; remove the dead duplicated ``_sanitize_for_sudo`` block.
- docs: add "Reviewing and sharing logs" section to README covering ``trops tldr``, ``trops tablog`` (``get`` / ``join``), and ``trops view`` -- including the ``%``-placeholder map for ``--only`` and the ``view --web`` URL/clickable behavior (#165).
- chore(release): make ``release.sh`` portable across BSD and GNU sed, exit on missing/invalid argument, pre-flight check the working tree, and print the git tag/push steps so future releases get a matching annotated tag.

`v0.2.35`_ - 2025-09-23
=======================
- Packaging/docs: bump version to 0.2.35.

`v0.2.34`_ - 2025-09-23
=======================
- tldr: Fix save when git_remote is not configured.

`v0.2.33`_ - 2025-08-18
=======================
- Rename: `km`→`tldr` subcommand; `getkm`→`tablog get`; `joinkm`→`tablog join`.
- CLI: Remove `glab` (GitLab) subcommand.
- view --web: Use `trops tablog get -a -u -f <path>` for `--update-km` refresh.

`v0.2.32`_ - 2025-08-17
=======================
- tablog get: Add `-f/--force` to overwrite existing files and `-u/--update` to run `trops fetch` beforehand.
- view --web: Add `-u/--update-km` to run `trops tablog get -a -u -f <path>` before starting the viewer.
- tablog join: New subcommand to merge multiple KM markdown logs into a single time-sorted table; support append mode and header handling.
- Errors: Replace many `print + exit` paths with structured `TropsError` exceptions; top-level CLI prints the error and exits with non-zero code.
- Core: Rename classes `Trops`→`TropsBase`, `TropsMain`→`TropsCLI` (backward-compatible aliases maintained).

`v0.2.31`_ - 2025-08-13
=======================
- view --web: Use `trops show <hash>[:<path>]` for the web endpoint instead of raw `git show`, so it respects trops configuration.
- tablog get: Create the destination directory automatically if it does not exist. Use `--work-tree=<path>` on checkout-index and strip a leading `/` from `km_dir` when building refs.

`v0.2.30`_ - 2025-08-13
=======================
- capcmd: defer "trops show <hash>:<path>" file logs until after the actual command log, preserving real-world order (e.g., "vi <path>" then "trops show <hash>:<path>").
- tests: add a test to assert the command log precedes the file log for editor commands.
- note: logging deferral is in-memory only; existing log files are not read or rewritten.

`v0.2.29`_ - 2025-08-11
=======================
- capcmd performance: early fast-path ignore for commands like `ttags` (skip side-effects),
  avoid `os.chdir` by using `git -C`, and use a set for `ignore_cmds` membership checks.
- log: default to printing all lines when no filters are specified; apply same logic in follow mode.
- capcmd: clearer error when `TROPS_ENV` is set but missing in config; safer defaults for attributes.
- utils: rename unclear `that` to `sid_seed_text` and add tests for SID format.
- capcmd: rename `_update_files` to `_track_editor_files` for clarity and add test.

`v0.2.28`_ - 2025-08-10
=======================
- capture-cmd: Automatically add the original command (`# <command>`) to the first line of files added with `| tee <file>`.
- view --web: Skip the front matter (YAML, `---` to `---`) and display only the main content.
- view --web: Adjust to display hyperlinks with underlines only, without changing their color.
- trops git: Normalize relative paths or CWD-based paths to work-tree relative paths and appropriately insert `--`.
- trops ll: Normalize directory arguments to work-tree relative paths for display.
- Common: Utility-ize path normalization logic to reduce duplication.

`v0.2.27`_ - 2025-08-10
=======================
- Add trops view command with:
  - Single file viewing from repo: `trops view <file> [--commit <rev>]`
  - Web viewer: `trops view --web <folder>` serving at http://localhost:8001
  - Clickable "trops show <hash>[:<path>]" links in Markdown to open modal with git show outputs
  - Optional `--no-browser` to suppress auto opening browser
  - Markdown tables render with borders in web viewer
  - Improved modern styling and search filter
  - Diff syntax highlighting for git show output
- Editor/tee capture-cmd improvements:
  - Detect files edited even when command is repeated
  - Auto-push only when files were added/updated
  - Handle chained pipelines and `|tee` variations
- Git wrapper improvements:
  - Normalize absolute paths to work-tree relative pathspecs
  - Use `-C <work_tree>` and `--` separator for safety
  - `-v/--verbose` to print wrapped git/touch commands
- Tags and log improvements:
  - Filter log by any tag element; `--tags` override at runtime
  - Primary tag extraction and normalization

`v0.2.26`_ - 2025-08-08
=======================

`v0.2.25`_ - 2024-07-01
=======================

`v0.2.24`_ - 2024-06-16
=======================

`v0.2.23`_ - 2024-01-21
=======================

`v0.2.22`_ - 2023-12-05
=======================

`v0.2.21`_ - 2023-11-23
=======================

`v0.2.20`_ - 2023-10-08
=======================

`v0.2.19`_ - 2023-09-21
=======================

`v0.2.18`_ - 2023-08-07
=======================

.. _Unreleased: https://github.com/kojiwell/trops/compare/v0.2.36...develop
.. _v0.2.36: https://github.com/kojiwell/trops/compare/v0.2.35...v0.2.36
.. _v0.2.35: https://github.com/kojiwell/trops/compare/v0.2.34...v0.2.35
.. _v0.2.34: https://github.com/kojiwell/trops/compare/v0.2.33...v0.2.34
.. _v0.2.33: https://github.com/kojiwell/trops/compare/v0.2.32...v0.2.33
.. _v0.2.32: https://github.com/kojiwell/trops/compare/v0.2.31...v0.2.32
.. _v0.2.31: https://github.com/kojiwell/trops/compare/v0.2.30...v0.2.31
.. _v0.2.30: https://github.com/kojiwell/trops/compare/v0.2.29...v0.2.30
.. _v0.2.29: https://github.com/kojiwell/trops/compare/v0.2.28...v0.2.29
.. _v0.2.28: https://github.com/kojiwell/trops/compare/v0.2.27...v0.2.28
.. _v0.2.27: https://github.com/kojiwell/trops/compare/v0.2.26...v0.2.27
.. _v0.2.26: https://github.com/kojiwell/trops/compare/v0.2.25...v0.2.26
.. _v0.2.25: https://github.com/kojiwell/trops/compare/v0.2.24...v0.2.25
.. _v0.2.24: https://github.com/kojiwell/trops/compare/v0.2.23...v0.2.24
.. _v0.2.23: https://github.com/kojiwell/trops/compare/v0.2.22...v0.2.23
.. _v0.2.22: https://github.com/kojiwell/trops/compare/v0.2.21...v0.2.22
.. _v0.2.21: https://github.com/kojiwell/trops/compare/v0.2.20...v0.2.21
.. _v0.2.20: https://github.com/kojiwell/trops/compare/v0.2.19...v0.2.20
.. _v0.2.19: https://github.com/kojiwell/trops/compare/v0.2.18...v0.2.19
.. _v0.2.18: https://github.com/kojiwell/trops/compare/v0.2.14...v0.2.18
