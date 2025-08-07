"""
Initialize module for handling shell initialization.
"""
import argparse
import os
import sys
import textwrap


def handle_init(args: argparse.Namespace) -> None:
    """
    Handle the init subcommand.

    Args:
        args: Command line arguments.
    """
    # Check if TROPS_DIR environment variable exists
    trops_dir = os.getenv("TROPS_DIR")
    if not trops_dir:
        print("Error: TROPS_DIR environment variable is not set.", file=sys.stderr)
        print("Please set TROPS_DIR to specify the directory for trops operations.", file=sys.stderr)
        sys.exit(1)
    
    shell = args.shell
    
    if shell == "bash":
        bash_script = textwrap.dedent(r'''
            _trops_capcmd () {
                trops capcmd $? $(history -a && fc -ln -0 -0)
            }

            ontrops() {
                if [ "$#" -ne 1 ]; then
                    echo "# upsage: on-trops <env>"
                else
                    export TROPS_ENV=$1
                    export TROPS_SID=$(trops gensid)

                    if ! [[ "${PROMPT_COMMAND:-}" =~ "_trops_capcmd" ]]; then
                        PROMPT_COMMAND="_trops_capcmd;$PROMPT_COMMAND"
                    fi

                fi
            }

            offtrops() {
                unset TROPS_ENV TROPS_SID
                PROMPT_COMMAND=${PROMPT_COMMAND//_trops_capcmd\;}
            }

            ttags() {
            export TROPS_TAGS=$(echo $@|tr ' ' ,)
            if [ ! x$TMUX = "x" ] ; then
                tmux rename-window "$TROPS_TAGS"
            fi
            }
        ''').strip()
        print(bash_script)
    elif shell == "zsh":
        zsh_script = textwrap.dedent(r'''
            autoload -Uz add-zsh-hook
            ontrops() {
                setopt INC_APPEND_HISTORY
                export TROPS_SID=$(trops gensid)
                if [ "$#" -ne 1 ]; then
                    echo "# upsage: on-trops <env>"
                else
                    export TROPS_ENV=$1
                    _tr_capcmd() {
                        trops capcmd $? $(fc -ln -1 -1)
                    }
                    add-zsh-hook precmd _tr_capcmd
                fi
            }

            offtrops() {
                unset TROPS_ENV TROPS_SID
                add-zsh-hook -D precmd _tr_capcmd
            }

            ttags() {
            export TROPS_TAGS=$(echo $@|tr ' ' ,)
            if [ ! x$TMUX = "x" ] ; then
                tmux rename-window "$TROPS_TAGS"
            fi
            }
        ''').strip()
        print(zsh_script)
    else:
        print(f"Initializing trops for {shell} shell")


def add_init_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Add the init subcommand parser.

    Args:
        subparsers: The subparsers object from the main parser.
    """
    init_parser = subparsers.add_parser("init", help="Initialize trops for a specific shell")
    init_parser.add_argument(
        "shell",
        choices=["bash", "zsh"],
        help="Shell type to initialize (bash or zsh)",
    )
    init_parser.set_defaults(func=handle_init)
