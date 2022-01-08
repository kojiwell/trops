# Trops - Track Operations

Trops is a simple command-line tool to track Linux system operations. It is basically a wrapper of Git to track updates of files on a Linux system. It is inspired by [The best way to store your dotfiles: A bare Git repository](https://www.atlassian.com/git/tutorials/dotfiles).

## Preriquisites

- Python-3.7 or higher
- Git

```
# Ubuntu
pip install python3 python3-pip git

# CentOS
TBD
```

## Installation

```
pip install trops
```

## Setup

Set up a trops project directory

```
trops init
```

Set up the trops environment

```
# bash
. ~/.trops/trops/bash_tropsrc
# zsh
. ~/.trops/trops/bash_tropsrc
```

## Usage

```
trops -h         
usage: trops [-h] {init,git,log,show-log,ll,touch,bye,random-name} ...

Trops - Tracking Operations

positional arguments:
  {init,git,log,show-log,ll,touch,bye,random-name}
    init                initialize trops
    git                 git wrapper
    log                 log command
    show-log            show log
    ll                  list files
    touch               add/update file in the git repo
    bye                 remove file from the git repo
    random-name         generate random name

optional arguments:
  -h, --help            show this help message and exit
```