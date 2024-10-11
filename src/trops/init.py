from textwrap import dedent

from .trops import Trops


class TropsInit(Trops):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        if other_args:
            msg = f"""\
                # Unsupported argments { ", ".join(other_args)}
                # > trops init --help"""
            print(dedent(msg))
            exit(1)

        if self.args.shell not in ['bash', 'zsh']:
            print("# usage: trops init [bash/zsh]")
            exit(1)

    def _init_zsh(self):

        zsh_lines = f"""\
            autoload -Uz add-zsh-hook
            ontrops() {{
                setopt INC_APPEND_HISTORY
                export TROPS_SID=$(trops gensid)
                if [ "$#" -ne 1 ]; then
                    echo "# upsage: on-trops <env>"
                else
                    export TROPS_ENV=$1
                    _tr_capcmd() {{
                        trops capture-cmd $? $(fc -ln -1 -1)
                    }}
                    add-zsh-hook precmd _tr_capcmd
                fi
            }}

            offtrops() {{
                unset TROPS_ENV TROPS_SID
                add-zsh-hook -D precmd _tr_capcmd
            }}

            ttags() {{
            export TROPS_TAGS=$(echo $@|sed 's/,/ /g'|tr -s ' '|tr ' ' ,)
            if [ ! x$TMUX = "x" ] ; then
                tmux rename-window "$TROPS_TAGS"
            fi
            }}
            """

        return dedent(zsh_lines)

    def _init_bash(self):

        bash_lines = f"""\
            _trops_capcmd () {{
                trops capture-cmd $? $(history -a && fc -ln -0 -0)
            }}

            ontrops() {{
                if [ "$#" -ne 1 ]; then
                    echo "# upsage: on-trops <env>"
                else
                    export TROPS_ENV=$1
                    export TROPS_SID=$(trops gensid)

                    if ! [[ "${{PROMPT_COMMAND:-}}" =~ "_trops_capcmd" ]]; then
                        PROMPT_COMMAND="_trops_capcmd;$PROMPT_COMMAND"
                    fi

                fi
            }}

            offtrops() {{
                unset TROPS_ENV TROPS_SID
                PROMPT_COMMAND=${{PROMPT_COMMAND//_trops_capcmd\;}}
            }}

            ttags() {{
            export TROPS_TAGS=$(echo $@|sed 's/,/ /g'|tr -s ' '|tr ' ' ,)
            if [ ! x$TMUX = "x" ] ; then
                tmux rename-window "$TROPS_TAGS"
            fi
            }}
            """

        return dedent(bash_lines)

    def run(self):

        print(eval(f"self._init_{ self.args.shell }()"))


def trops_init(args, other_args):

    ti = TropsInit(args, other_args)
    ti.run()


def add_init_subparsers(subparsers):

    # trops init
    parser_init = subparsers.add_parser('init', help="Initialize Trops")
    parser_init.add_argument('shell', help='shell [bash/zsh]')
    parser_init.set_defaults(handler=trops_init)
