import os
from configparser import ConfigParser
from textwrap import dedent

from trops.utils import real_path


class TropsInit:

    def __init__(self, args, other_args):

        self.args = args
        if other_args:
            msg = f"""\
                # Unsupported argments { ", ".join(other_args)}
                # > trops init --help"""
            print(dedent(msg))
            exit(1)

        if self.args.shell not in ['bash', 'zsh']:
            print("# usage: trops init [bash/zsh]")
            exit(1)

        if os.getenv('TROPS_DIR'):
            self.trops_dir = real_path(os.getenv('TROPS_DIR'))
        else:
            self.trops_dir = real_path('$HOME/.trops')

        self.trops_conf = self.trops_dir + '/trops.cfg'
        self.trops_log_dir = self.trops_dir + '/log'

        self.config = ConfigParser()
        if os.path.isfile(self.trops_conf):
            self.config.read(self.trops_conf)

    def _init_zsh(self):

        zsh_lines = f"""\
            ontrops() {{
                export TROPS_SID=$(trops gensid)
                if [ "$#" -ne 1 ]; then
                    echo "# upsage: on-trops <env>"
                else
                    export TROPS_ENV=$1
                    precmd() {{
                        trops capture-cmd 1 $? $(history|tail -1)
                    }}
                fi
            }}

            offtrops() {{
                LC_ALL=C type precmd >/dev/null && unset -f precmd
            }}
            """

        return dedent(zsh_lines)

    def _init_bash(self):

        bash_lines = f"""\
            _trops_capcmd () {{
                trops capture-cmd 1 $? $(history 1)
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
                PROMPT_COMMAND=${{PROMPT_COMMAND//_trops_capcmd\;}}
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
