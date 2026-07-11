#!/bin/sh
# trops-log: capture a Bash command run by Claude Code into trops.log.
#
# Registered as a PostToolUse hook on the Bash tool by the /trops-log command.
# Reads the hook payload (JSON) on stdin, extracts the command string and its
# exit code, and records them via `trops capture-cmd` so the entry looks exactly
# like a human command captured by the `ontrops` shell hook:
#   CM <command> #> PWD=..., EXIT=..., TROPS_SID=..., TROPS_ENV=...
# The trops logger prefixes each line with `username@hostname`, so the log shows
# what was done and on which host.
#
# Best-effort and non-blocking: any failure is swallowed and the script always
# exits 0, so trops logging can never block or fail the underlying Bash call.

set -f  # disable globbing: command tokens must not be expanded as file globs

input=$(cat)

# Nothing to do unless trops is usable in this environment.
[ -n "${TROPS_DIR:-}" ] || exit 0
command -v trops >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[ -n "$cmd" ] || exit 0

rc=$(printf '%s' "$input" | jq -r '.tool_response.exit_code // 0')
case "$rc" in
    ''|*[!0-9]*) rc=0 ;;  # non-numeric / missing -> treat as success
esac

# Attribute the entry to Claude: append a `claude` tag, preserving any tag the
# user already set (e.g. an issue number) so tldr's %t column shows both.
if [ -n "${TROPS_TAGS:-}" ]; then
    TROPS_TAGS="${TROPS_TAGS},claude"
else
    TROPS_TAGS="claude"
fi
export TROPS_TAGS

# Word-split $cmd intentionally (matches how trops joins command tokens).
trops capture-cmd "$rc" $cmd >/dev/null 2>&1

exit 0
