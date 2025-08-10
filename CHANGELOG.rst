*********
Changelog
*********

`Unreleased`_
=============

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
-. Editor/tee capture-cmd improvements:
  - Detect files edited even when command is repeated
  - Auto-push only when files were added/updated
  - Handle chained pipelines and `|tee` variations
-. Git wrapper improvements:
  - Normalize absolute paths to work-tree relative pathspecs
  - Use `-C <work_tree>` and `--` separator for safety
  - `-v/--verbose` to print wrapped git/touch commands
-. Tags and log improvements:
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

.. _Unreleased: https://github.com/kojiwell/trops/compare/v0.2.27...develop
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
