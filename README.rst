******************************
Trops tracks system operations
******************************

.. image:: https://img.shields.io/pypi/v/trops
   :target: https://pypi.org/project/trops/
   :alt: PyPI Package

.. image:: https://img.shields.io/badge/license-MIT-brightgreen.svg
   :target: LICENSE
   :alt: Repository License

Trops is a command-line tool for tracking Linux system operations in an easy-to-use workflow. 
It helps you interactively develop Ansible roles, Dockerfile, and etc.

Prerequisites
=============

- OS: Linux
- Shell: Bash or Zsh
- Python: 3.8 or higher
- Git: 2.X

Installation
============

Ubuntu::

    apt install python3 python3-pip git
    pip3 install trops

CentOS

CentOS's default Git and Python3 versions might be older than the prerequisites, but you can use Miniconda as shown below.

Miniconda::

    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    chmod +x Miniconda3-latest-Linux-x86_64.sh
    ./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
    $HOME//miniconda3/bin/conda install git
    $HOME/miniconda3/bin/pip install trops
    mkdir $HOME/bin
    cd $HOME/bin
    ln -s ../miniconda3/bin/git git
    ln -s ../miniconda3/bin/trops trops
    export PATH=$HOME/bin:$PATH # Add this line to your .bashrc

Quickstart
==========

Activate trops::

    export TROPS_DIR="/path/to/your/trops"
    test -d $TROPS_DIR || mkdir $TROPS_DIR

    # for Bash
    eval "$(trops init bash)"
    # for Zsh
    eval "$(trops init zsh)"

Create a trops environment(e.g. myenv)::

    trops env create myenv

Turn on/off background tracking::

    # Turn on
    ontrops myenv

    # Turn off
    offtrops

If you turn it on, every command will be logged. You can check it by trops log command::

    trops log

Inspiration
===========

Trops is inspired by the idea on this link.

- `The best way to store your dotfiles: A bare Git repository <https://www.atlassian.com/git/tutorials/dotfiles>`_

Contributing
============

If you have a problem, please `create an issue <https://github.com/kojiwell/trops/issues/new>`_ or a pull request.

1. Fork it ( https://github.com/kojiwell/trops/fork )
2. Create your feature branch (``git checkout -b my-new-feature``)
3. Commit your changes (``git commit -am 'Add some feature'``)
4. Push to the branch (``git push origin my-new-feature``)
5. Create a new Pull Request