*****
Trops
*****

.. image:: https://img.shields.io/pypi/v/trops
   :target: https://pypi.org/project/trops/
   :alt: PyPI Package

.. image:: https://img.shields.io/badge/license-MIT-brightgreen.svg
   :target: LICENSE
   :alt: Repository License

Trops is a command-line tool designed for tracking system operations on destributed Linux systems. It keeps a log of executed commands and modified files, being helpful for developing Ansible roles, Dockerfiles, and similar tasks. It is portable and easy to use, and it can be used in a variety of environments, such as local, remote, and containerized environments. You can store your log on a private, internal Git repository (not public) and link it to issues in tools such as GitLab and Redmine.

It aims for solving these challenges:

- Keeping track of when and what has been done on which host (for which issue)
- Note-taking for solo system administrators of destributed systems
- "Potentially" bridging the gap between Dev and Ops

Prerequisites
=============

- OS: Linux, MacOS
- Shell: Bash, Zsh
- Python: 3.10 or higher
- Git: 2.28 or higher

Installation
============

Ubuntu::

    sudo apt install pipx git
    pipx install trops

Rocky::

    sudo dnf install epel-release git
    sudo dnf install python3.12-pip
    pip3.12 install --user pipx
    pipx install trops

MacOS::

    brew install pipx git
    pipx install trops

Conda-forge::

    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
    bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3
    $HOME/miniforge3/bin/conda install git
    $HOME/miniforge3/bin/pip install trops
    mkdir $HOME/bin
    cd $HOME/bin
    ln -s ../miniforge3/bin/git git
    ln -s ../miniforge3/bin/trops trops
    export PATH=$HOME/bin:$PATH # Add this line in your .bashrc

Install as a Claude Code skill
==============================

If you use `Claude Code <https://claude.com/claude-code>`_, you can install a skill that walks Claude through installing, setting up, and using trops on your machine. Run::

    mkdir -p ~/.claude/skills/trops && \
      wget -O ~/.claude/skills/trops/SKILL.md \
        https://raw.githubusercontent.com/kojiwell/trops/main/SKILL.md

After installing, ask Claude something like "install trops" or "set up a trops env for this project" and the skill will load automatically. Re-run the command above any time to pull the latest version of the skill.

Quickstart
==========

Activate trops::

    export TROPS_DIR="/path/to/your/trops"
    test -d $TROPS_DIR || mkdir -p $TROPS_DIR

    # for Bash
    eval "$(trops init bash)"
    # for Zsh
    eval "$(trops init zsh)"

Create a trops environment(e.g. myenv)::

    trops env create myenv

Activate or deactivate background tracking::

    # Activate
    ontrops myenv

    # Deactivate
    offtrops

When activated, every command is logged in a log file located at $TROPS_DIR/log/trops.log, and any modified file is committed to its designated Git repository ($TROPS_DIR/repo/<env>.git). To see this in action, perform tasks such as installing or compiling an application, and then use the trops log command to review the log::

    # Get your work done, and then check log
    trops log

    # You can also pass the output to Trops TLDR(tldr), 
    # which unclutters and shows log in a table
    trops log | trops tldr

If you use tools such as GitLab and Redmine as an internal, remote, private repository for your Trops, you can set it by `--git-remote` option like this::

    # At creation
    trops env create --git-remote=git@gitlab.example.local:username/repository_name.git myenv

    # or update
    ontrops myenv
    trops env update --git-remote=git@gitlab.example.local:username/repository_name.git

Trops now transforms your system operations into an issue-driven project. Create an issue on your private repository, for example, "Install foobar #1," and then set the issue number as a tag in Trops like this::

    # '#<issue number>'
    ttags '#1'

    # repo_name#<number>
    ttags repo_name#1

Once your work is done, you can save and push the log::

    # Save the log as a markdown table
    trops log | trops tldr --save

    # And then, push your trops' commits to the remote repository
    trops repo push

On the issue page, you can find the log in a markdown table format, which is useful for reviewing and sharing your work with your team members.

Now, you can update the tasks and recipes in your Ansible roles, Dockerfiles, and so on, based on the log. You can also use the log as a reference for troubleshooting.

Trops helps you easily try new things, and you don't have to worry about forgetting what you've done. And then, once you've got used to it, it will actually help you organize your day-to-day multitasking, which is probably something that a lot of system admins cannot avoid.

Reviewing and sharing logs
==========================

Once you have been using ``ontrops`` for a while, three subcommands turn the raw ``trops.log`` into shareable artifacts and a browsable history: ``trops tldr`` renders the log as a table, ``trops tablog`` collects and merges the saved tables, and ``trops view`` opens a tracked file or a folder of tables in a local web viewer.

trops tldr
----------

``trops tldr`` (Table Log Direct, "Too Long Don't Read") consumes the output of ``trops log`` on stdin and renders it as a table. By default the output is plaintext for terminal viewing; with ``-m`` or ``--html`` you get Markdown or HTML, and with ``-s`` the table is saved as Markdown into the env's ``tablog_dir`` so that it can be committed and shared (for example, pasted into a GitLab or Redmine issue).

Pipe ``trops log`` into ``tldr``, and optionally save::

    trops log | trops tldr
    trops log | trops tldr -s

Notable options:

- ``-o, --only <fmt>`` -- ``%``-placeholder string controlling which columns appear. Supported codes: ``%D`` Date, ``%T`` Time, ``%u`` ``User@host``, ``%ll`` Log level, ``%lt`` Log type, ``%c`` Command, ``%d`` Directory/Owner,Group,Mode, ``%x`` Exit code, ``%i`` ID, ``%e`` Env, ``%t`` Tags. Default: ``%D,%T,%u,%c,%d,%x``.
- ``-s, --save`` -- save the rendered table as Markdown under the env's ``tablog_dir`` (default ``$TROPS_DIR/tablog`` per env config). The filename is auto-generated from repo + env + tag.
- ``--name <name>`` -- override the auto-generated filename when used with ``--save``.
- ``-m, --markdown`` / ``--html`` -- output format selectors (mutually exclusive); default is plaintext.
- ``-n, --no-declutter`` -- disable noise filtering. ``-a, --all`` -- include all log entries.

trops tablog
------------

``trops tablog`` works on the Markdown tables that ``trops tldr -s`` saves. The saved tables live as commits inside each env's git repo (under ``tablog_dir``); ``tablog get`` extracts them onto the filesystem so they can be browsed, merged, or served by ``trops view --web``, and ``tablog join`` merges multiple of them into a single time-sorted table.

tablog get
~~~~~~~~~~

Extract the saved tables from one or all envs into a target directory::

    trops tablog get -a -u -f /path/to/extract

Notable options:

- positional ``path`` -- destination directory; created if missing. Used as ``--prefix`` for the underlying ``git checkout-index``.
- ``-a, --all`` -- process every env in ``trops.cfg``. Mutually exclusive with ``-e``.
- ``-e, --env <name>`` -- process a single env.
- ``-u, --update`` -- run ``trops fetch`` before extracting (refreshes from the configured remote).
- ``-f, --force`` -- overwrite existing files in the target directory.

tablog join
~~~~~~~~~~~

Merge multiple Markdown tables into one time-sorted table::

    trops tablog join -o merged.md file1.md file2.md

Notable options:

- ``-o, --output <path>`` -- required output file path.
- ``-a, --append`` -- append to the output file instead of overwriting it.

trops view
----------

``trops view`` has two modes. In **file mode** it shows a tracked file's content at a given commit (default ``HEAD``); useful for inspecting historical state without leaving the shell. In **web mode** (``--web``) it serves a folder of ``.md`` tablog files in a browser, with each ``trops show <hex>:<path>`` entry hyperlinked: clicking ``<hex>`` opens a diff view, and clicking ``<path>`` opens the file's content at that commit.

File mode::

    trops view /etc/hosts
    trops view --commit 1a2b3c /etc/hosts

Web mode (after extracting tablog files with ``trops tablog get``)::

    trops view --web /path/to/extract

Notable options:

- positional ``file`` -- absolute path to a tracked file (file mode), or a folder of ``.md`` tablog files (with ``--web``).
- ``-e, --env <name>`` -- select the env. ``--commit <hash>`` -- commit-ish to view; default ``HEAD``.
- ``--web`` -- start a local web viewer. The server binds to ``http://localhost:8001`` and the default browser opens automatically.
- ``-u, --update-tablog`` -- before starting the web viewer, run ``trops tablog get -a -u -f <folder>`` to refresh the tablog files into the served folder.
- ``--no-browser`` -- do not auto-open a browser tab (useful for headless or remote sessions; you can still navigate to ``http://localhost:8001`` manually, e.g., via an SSH port-forward).

Sharing trops tags among hosts and sudoers
==========================================

Add SendEnv TROPS_TAGS to ~/.ssh/config::

    SendEnv TROPS_TAGS

Add TROPS_TAGS to AcceptEnv in /etc/ssh/sshd_config::

    AcceptEnv TROPS_TAGS

Add TROPS_TAGS to /etc/sudoers::

    Defaults    env_keep += "TROPS_TAGS"

Check TROPS_TAGS in environment variables and actiavate trops::

    if [[ -n "${TROPS_TAGS}" ]]; then
        . /path/to/trops/tropsrc
    fi

The tropsrc looks like this::

    export TROPS_DIR="/path/to/trops"
    test -d $TROPS_DIR || mkdir -p $TROPS_DIR

    # for Bash
    eval "$(trops init bash)"
 
    if [ ! -d "$TROPS_DIR/repo/$(hostname -s).git" ]; then
        trops env create $(hostname -s)
    fi

    ontrops $(hostname -s)

Contributing
============

If you have a problem, please `create an issue <https://github.com/kojiwell/trops/issues/new>`_ or a pull request.

1. Fork it ( https://github.com/kojiwell/trops/fork )
2. Create your feature branch (``git checkout -b my-new-feature``)
3. Commit your changes (``git commit -am 'Add some feature'``)
4. Push to the branch (``git push origin my-new-feature``)
5. Create a new Pull Request