from textwrap import dedent

from .trops import TropsBase, TropsError


class TropsInit(TropsBase):

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        if other_args:
            msg = f"""\
                # Unsupported argments { ", ".join(other_args)}
                # > trops init --help"""
            raise TropsError(dedent(msg))

        if self.args.shell not in ['bash', 'zsh']:
            raise TropsError("# usage: trops init [bash/zsh]")

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
            
            alias ttee="tee"
            """

        return dedent(zsh_lines)

    def _init_bash(self):

        # bash has no preexec hook, so emulate one with a DEBUG trap:
        #   PROMPT_COMMAND = _trops_capcmd;<existing>;_trops_arm
        # _trops_arm runs last, right before the prompt is shown, and arms the
        # trap. The first DEBUG trap after that is the command the user
        # entered; it records the command line and disarms. Since nothing is
        # armed on an empty Enter, the previous command is not re-logged.
        # Plain (non f-string) raw string: no brace escaping needed.
        bash_lines = r"""
            _trops_capcmd () {
                local rc=$?
                history -a
                if [[ -n ${_TR_CMD-} ]]; then
                    trops capture-cmd $rc $_TR_CMD
                fi
                unset _TR_CMD
            }

            _trops_arm () {
                _TR_LAST_HIST=$(HISTTIMEFORMAT= builtin history 1)
                _TR_ARMED=1
            }

            _trops_debug () {
                [[ -n ${_TR_ARMED-} ]] || return 0
                # Ignore programmable completion functions
                [[ -n ${COMP_LINE-} ]] && return 0
                local bc=$BASH_COMMAND
                # PROMPT_COMMAND started without a user command (empty
                # Enter): disarm so later PROMPT_COMMAND entries are ignored.
                if [[ $bc == _trops_capcmd ]]; then
                    unset _TR_ARMED
                    return 0
                fi
                # Ignore PROMPT_COMMAND entries placed before _trops_capcmd
                local IFS=';'
                local pc=";${PROMPT_COMMAND[*]-};"
                pc=${pc//[[:space:]]/}
                [[ $pc == *";${bc//[[:space:]]/};"* ]] && return 0
                unset _TR_ARMED

                local h t= re='^[[:space:]]*[0-9]+\*?[[:space:]]+(.*)$'
                h=$(HISTTIMEFORMAT= builtin history 1)
                [[ $h =~ $re ]] && t=${BASH_REMATCH[1]}
                # A new history entry is the full command line. Otherwise
                # (ignoredups/ignorespace/history off) trust it only when it
                # starts with the current simple command, else fall back to
                # $BASH_COMMAND (the first simple command only).
                if [[ -n $t && ( $h != "${_TR_LAST_HIST-}" || $t == "$bc"* ) ]]; then
                    _TR_CMD=$t
                else
                    _TR_CMD=$bc
                fi
                return 0
            }

            _trops_remove_hooks () {
                if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == "declare -a"* ]]; then
                    local c new=()
                    for c in "${PROMPT_COMMAND[@]}"; do
                        [[ $c == _trops_capcmd || $c == _trops_arm ]] || new+=("$c")
                    done
                    PROMPT_COMMAND=("${new[@]}")
                else
                    local pc=${PROMPT_COMMAND-}
                    pc=${pc//_trops_capcmd;/}
                    pc=${pc//;_trops_arm/}
                    pc=${pc//_trops_arm/}
                    PROMPT_COMMAND=$pc
                fi
                if [[ -n ${_TR_DEBUG_INSTALLED-} ]]; then
                    if [[ -n ${_TR_PREV_DEBUG-} ]]; then
                        eval "$_TR_PREV_DEBUG"
                    else
                        trap - DEBUG
                    fi
                fi
                unset _TR_DEBUG_INSTALLED _TR_PREV_DEBUG _TR_ARMED _TR_CMD _TR_LAST_HIST
            }

            _trops_install_hooks () {
                _trops_remove_hooks
                if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == "declare -a"* ]]; then
                    PROMPT_COMMAND=(_trops_capcmd "${PROMPT_COMMAND[@]}" _trops_arm)
                else
                    local pc=${PROMPT_COMMAND-} re='[[:space:];]$'
                    while [[ $pc =~ $re ]]; do pc=${pc%?}; done
                    PROMPT_COMMAND="_trops_capcmd;${pc:+$pc;}_trops_arm"
                fi
                # Chain an existing DEBUG trap instead of replacing it
                _TR_PREV_DEBUG=$(trap -p DEBUG)
                local prev=
                if [[ -n $_TR_PREV_DEBUG ]]; then
                    eval "set -- $_TR_PREV_DEBUG"
                    prev=$3
                fi
                trap "_trops_debug${prev:+; $prev}" DEBUG
                _TR_DEBUG_INSTALLED=1
            }

            ontrops() {
                if [ "$#" -ne 1 ]; then
                    echo "# upsage: on-trops <env>"
                else
                    export TROPS_ENV=$1
                    export TROPS_SID=$(trops gensid)
                    _trops_install_hooks
                fi
            }

            offtrops() {
                unset TROPS_ENV TROPS_SID
                _trops_remove_hooks
            }

            # Without the trace attribute, a function cannot see the global
            # DEBUG trap via `trap -p`, and bash 3.2 discards a DEBUG trap
            # set inside it on return.
            declare -ft ontrops offtrops _trops_install_hooks _trops_remove_hooks

            ttags() {
            export TROPS_TAGS=$(echo $@|sed 's/,/ /g'|tr -s ' '|tr ' ' ,)
            if [ ! x$TMUX = "x" ] ; then
                tmux rename-window "$TROPS_TAGS"
            fi
            }

            alias ttee="tee"
            """

        return dedent(bash_lines).lstrip("\n")

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
