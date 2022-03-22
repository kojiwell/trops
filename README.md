# Trops - Track Operations
[![PyPI Package](https://img.shields.io/pypi/v/trops)](https://pypi.org/project/trops/)
[![Repository License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

Trops is a simple command-line tool to track Linux system operations.

## Preriquisites

- Python-3.8 or higher
- Git 2.X

Ubuntu

    apt install python3 python3-pip git

CentOS

    TBD

## Installation

    pip3 install trops

## Quickstart

Set up a trops project directory

    trops env init <dir>

Set up the trops environment

    # bash
    . <dir>/trops/bash_<hostname>rc
    
    # zsh
    . <dir>/trops/zsh_<hostname>rc

## Usage

TBD

## Inspiration

- [The best way to store your dotfiles: A bare Git repository](https://www.atlassian.com/git/tutorials/dotfiles)

## Contributing

If you have a problem, please [create an issue](https://github.com/kojiwell/trops/issues/new) or a pull request.

1. Fork it ( https://github.com/kojiwell/trops/fork )
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request