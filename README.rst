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
- Python: 3.8 or higher
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

    # You can also pass the output to Trops KouMyo(km), 
    # which unclutters and shows log in a table
    trops log | trops km

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
    trops log | trops km --save

    # And then, push your trops' commits to the remote repository
    trops repo push

On the issue page, you can find the log in a markdown table format, which is useful for reviewing and sharing your work with your team members.

Now, you can update the tasks and recipes in your Ansible roles, Dockerfiles, and so on, based on the log. You can also use the log as a reference for troubleshooting.

Trops helps you easily try new things, and you don't have to worry about forgetting what you've done. And then, once you've got used to it, it will actually help you organize your day-to-day multitasking, which is probably something that a lot of system admins cannot avoid.

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