# Trops - Track Operations

Trops is a simple command-line tool to track Linux system operations. It is basically a wrapper of Git to track updates of files on a Linux system. It is inspired by [The best way to store your dotfiles: A bare Git repository](https://www.atlassian.com/git/tutorials/dotfiles).

## Preriquisites

- Python-3.7 or higher
- Git

Ubuntu

    apt install python3 python3-pip git

CentOS

    TBD

## Installation

    pip install trops

## Setup

Set up a trops project directory

    trops init

Set up the trops environment

    # bash
    . ~/.trops/trops/bash_tropsrc
    
    # zsh
    . ~/.trops/trops/zsh_tropsrc

## Usage
