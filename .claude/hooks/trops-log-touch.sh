#!/bin/sh
# trops-log: record a file edited by Claude Code into the trops env git repo.
#
# Registered by the /trops-log command as BOTH a PreToolUse and a PostToolUse
# hook on the Edit/Write tools. The pre-edit run commits the baseline; the
# post-edit run commits the change, so `trops touch` emits an FL entry:
#   FL trops show <commit>:<path> #> UPDATE O=..,G=..,M=.. TROPS_SID=.. TROPS_ENV=..
#
# `trops touch` requires an active env (it needs the env's git work_tree), and
# it errors on files that do not exist yet -- so a brand-new file's pre-edit run
# is skipped here and only the post-edit run records it (as ADD).
#
# Best-effort and non-blocking: any failure is swallowed and the script always
# exits 0, so trops logging can never block or fail the underlying Edit/Write.

input=$(cat)

[ -n "${TROPS_DIR:-}" ] || exit 0
command -v trops >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

fp=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -n "$fp" ] || exit 0

# Skip nonexistent files: new-file pre-edit run, or a deletion. `trops touch`
# would error; the post-edit run captures the created file instead.
[ -f "$fp" ] || exit 0

if [ -n "${TROPS_TAGS:-}" ]; then
    TROPS_TAGS="${TROPS_TAGS},claude"
else
    TROPS_TAGS="claude"
fi
export TROPS_TAGS

trops touch "$fp" >/dev/null 2>&1

exit 0
