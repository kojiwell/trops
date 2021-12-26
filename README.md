# Trops - Track Operations

Trops is a simple tool to track Linux system operations. It is basically a wrapper of Git to track updates of files on a Linux system. It is inspired by [The best way to store your dotfiles: A bare Git repository](https://www.atlassian.com/git/tutorials/dotfiles).

## Installation

```
pip install trops
```

## Usage

Set up a trops project directory

```
trops init .
```

Set up the trops environment

```
source trops/tropsrc
```

- `trops git` or `trgit` to add/commit/push updates
- `trops edit` or `tredit/trvim` to edit a file
- `trops log` or `trlog` to show log

## Notes

- `trops log` only supports Bash. Zsh support will be added later.