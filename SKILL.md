---
name: trops
description: Guide for installing, setting up, and using trops — a CLI for tracking commands and file changes on Linux/macOS systems. Use when the user mentions installing trops, asks how to start tracking with trops, or asks about trops commands like `ontrops`, `offtrops`, `trops env`, `trops log`.
---

# trops — install, setup, and daily usage

When this skill loads, follow the phase appropriate to the user's request:

- User wants to install trops, or `trops` is not on PATH → start at **Install**, then continue through **Setup**.
- User has trops installed but no env active (`echo $TROPS_DIR` empty, no `ontrops`/`offtrops` aliases) → start at **Setup**.
- User asks about `ontrops`, `offtrops`, `trops env`, `trops log`, or other commands → jump to **Daily Usage**.
- User reports trops misbehaving → jump to **Troubleshooting**.

## Execution model (read this first)

This skill follows a **hybrid execution model**:

- **Auto-run (no confirmation):** OS detection, version checks, `trops --version`, `trops env list`, `trops log`, idempotency checks, reading shell rc files, `mkdir` of `TROPS_DIR`.
- **Pause for user confirmation:** any `sudo` command, any append/edit to `~/.bashrc` / `~/.zshrc` / `~/.bash_profile`, anything that overwrites existing files, `trops env create` (because it initializes a git repo).

When you reach a confirmation point, show the exact command(s) you would run, briefly explain the effect, and wait for the user to say yes or run it themselves.

## Install

### Step 1 — Detect the OS

Run:

```
uname -s
```

If the result is `Darwin`, the platform is macOS. If `Linux`, also read:

```
cat /etc/os-release
```

Map `ID` (and `ID_LIKE` if present) to a path:

| Detected | Path to use |
|---|---|
| `Darwin` | macOS / Homebrew |
| `ID=ubuntu` or `ID=debian`, or `ID_LIKE` contains `debian` | apt |
| `ID=rocky`, `rhel`, `centos`, `fedora`, or `ID_LIKE` contains `rhel`/`fedora` | dnf |
| anything else, or detection fails | ask user (menu below) |

**Narrate what you observed and confirm before continuing.** Example:

> I see `ID=ubuntu` in `/etc/os-release`, so I'll use the apt install path. OK to proceed?

If the user is in a restricted environment (no sudo, locked-down distro, HPC node) and the detected path does not work, fall back to the **Conda-forge** path.

If detection is ambiguous, ask:

```
Which install path do you want to use?
 1) Ubuntu/Debian (apt + pipx)
 2) Rocky/RHEL/Fedora (dnf + pipx)
 3) macOS (brew + pipx)
 4) Conda-forge (no sudo required)
```

### Step 2 — Install the package

Show the commands for the chosen path and **wait for the user to confirm** before running anything with `sudo`. The user may prefer to paste the `sudo` lines into their own terminal — that is fine.

**Ubuntu / Debian:**

```
sudo apt install pipx git
pipx install trops
```

**Rocky / RHEL / Fedora:**

```
sudo dnf install epel-release git
sudo dnf install python3.12-pip
pip3.12 install --user pipx
pipx install trops
```

**macOS:**

```
brew install pipx git
pipx install trops
```

**Conda-forge (fallback for restricted environments):**

```
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3
$HOME/miniforge3/bin/conda install git
$HOME/miniforge3/bin/pip install trops
mkdir -p $HOME/bin
ln -sf $HOME/miniforge3/bin/git $HOME/bin/git
ln -sf $HOME/miniforge3/bin/trops $HOME/bin/trops
```

For Conda-forge, the user must also have `$HOME/bin` on their `PATH`. The shell-rc step in **Setup** will add it.

After install, run `pipx ensurepath` if pipx was used. Then verify:

```
trops --version
```

If `trops` is not found, ask the user to open a new shell (so `pipx`'s PATH change takes effect), or check whether `~/.local/bin` is on PATH.

## Setup

### Step 3 — Choose `TROPS_DIR`

Default is `$HOME/.trops`. Propose this and let the user override:

> I'll set `TROPS_DIR=$HOME/.trops`. Press enter to accept, or give me a different path.

If the chosen directory already exists and contains files (especially a `repo/` subdirectory), **do not clobber**. Confirm with the user that they want to reuse it or pick a different path.

Create the directory:

```
mkdir -p "$TROPS_DIR"
```

### Step 4 — Configure shell init

Detect the user's shell:

```
echo "$SHELL"
```

Map to the rc file:

| `$SHELL` | Rc file |
|---|---|
| `*/bash` on Linux | `~/.bashrc` |
| `*/bash` on macOS | `~/.bash_profile` (fall back to `~/.bashrc` if it exists) |
| `*/zsh` | `~/.zshrc` |
| anything else | ask the user which file to edit |

The lines to append (Bash example — substitute `bash` → `zsh` for zsh):

```
export TROPS_DIR="$HOME/.trops"
test -d "$TROPS_DIR" || mkdir -p "$TROPS_DIR"
eval "$(trops init bash)"
```

For Conda-forge users, also prepend to PATH:

```
export PATH="$HOME/bin:$PATH"
```

**Idempotency check before appending.** Run:

```
grep -F 'trops init' ~/.bashrc
```

(Substitute the appropriate rc file.) If a matching line is already there, **skip the append** and tell the user it is already configured.

If no match, show the diff that would be applied and ask the user to confirm. Then append. Do **not** auto-overwrite or modify existing lines.

After appending, tell the user to either open a new shell or `source` the rc file:

```
source ~/.bashrc
```

### Step 5 — Create the first env

A trops "env" is a git repository under `$TROPS_DIR/repo/` that records command history and modified-file commits.

Ask the user for an env name (suggest the hostname or project name as a default). Then run, after confirming:

```
trops env create <name>
```

Optionally, if the user has a private remote (GitLab / Gitea / private GitHub) for storing this env's history:

```
trops env create --git-remote=git@example.local:user/trops-history.git <name>
```

Verify:

```
trops env list
```

### Step 6 — Activate tracking

```
ontrops <name>
```

After this, every command the user runs in the shell is logged to `$TROPS_DIR/log/trops.log`, and any modified file is auto-committed to the env's git repo. To stop tracking:

```
offtrops
```

Tell the user that activation is per-shell — opening a new terminal starts un-tracked. They re-run `ontrops <name>` to resume.

## Daily Usage

Common operations:

```
ontrops <env>          # activate background tracking in this shell
offtrops               # deactivate
trops env list         # show all envs
trops log              # show the log
trops log | trops tldr # cleaner tabular view (uses the tldr subcommand)
trops tablog           # alternate tabular log view
trops branch           # git branch operations on the env's repo
trops show <commit>    # inspect a commit in the env's repo
trops touch <path>     # add/update a tracked file
trops drop <path>      # remove a file from tracking
trops fetch            # fetch from the configured git remote
```

If the user asks about a subcommand not listed here, run `trops <subcmd> --help` to get the authoritative usage. Do not invent flags.

To link a trops env to a remote private repo after creation, the user can use `trops git` to operate on the env's git repo directly (e.g., `trops git remote add origin ...` then `trops git push -u origin main`).

## Troubleshooting

**`trops: command not found` after install**
- Run `pipx ensurepath`, then open a new shell.
- Check that `~/.local/bin` (pipx) or `~/bin` (Conda-forge) is on `PATH`.

**`ontrops` / `offtrops` not recognized**
- The shell-init step (Step 4) was skipped or has not been sourced. Run `source ~/.bashrc` (or the appropriate rc file), or open a new shell.

**`echo $TROPS_DIR` is empty**
- Same root cause as above — `eval "$(trops init bash)"` has not run in this shell.

**Tracking does not seem to capture commands**
- Confirm `ontrops <env>` was run in *this* shell. Activation does not propagate across shells.
- Run `trops env list` to confirm the env exists.
- Check `$TROPS_DIR/log/trops.log` directly to see what is being captured.

**`trops env create` fails on git**
- Ensure git ≥ 2.28 is installed: `git --version`.
- Ensure `$TROPS_DIR` is writable.

**Multiple shells, multiple envs**
- One env per shell. If the user wants different envs in different shells, that is fine — each `ontrops` activation is shell-local.

For anything else, suggest the user file an issue at https://github.com/kojiwell/trops/issues with the output of `trops --version`, their OS, and the failing command.
