---
description: Enable (or disable) automatic logging of Claude's commands and file edits into trops.log
argument-hint: "[off]"
allowed-tools: Bash(command -v:*), Bash(trops:*), Bash(cat:*), Bash(chmod:*), Bash(test:*), Read, Edit, Write
---

# /trops-log

Wire this session up so that everything Claude does is recorded in `trops.log` in
native trops style. It installs Claude Code hooks that call `trops capture-cmd`
(for Bash commands) and `trops touch` (for file edits), so that when the user runs
`trops log` the output shows what Claude did and on which host.

The argument is `$ARGUMENTS`:

- empty  → **enable** logging (install the hooks)
- `off`  → **disable** logging (remove the hooks)

The hooks are installed into **`.claude/settings.local.json`** (personal, git-ignored),
never the shared `.claude/settings.json` — trops logging depends on the user's local
trops env and must not be force-enabled for everyone.

---

## If `$ARGUMENTS` is `off` → disable

1. Read `.claude/settings.local.json`. If it doesn't exist or has no trops-log hooks,
   tell the user logging is already off and stop.
2. Remove **only** the trops-log hook entries — the ones whose `command` ends with
   `/.claude/hooks/trops-log-capture.sh` or `/.claude/hooks/trops-log-touch.sh`. Leave
   every other setting and hook untouched. Drop now-empty `matcher`/event arrays.
3. Confirm: "trops logging disabled — Claude's actions will no longer be written to
   trops.log this session." Stop.

---

## If `$ARGUMENTS` is empty → enable

### Step 1 — Verify trops is usable (abort cleanly if not)

Run these checks. If **any** fails, install nothing and tell the user exactly what to fix.

- `command -v trops` — trops must be on PATH.
  - On failure: "trops is not installed / not on PATH. Install it first (see the `trops`
    skill), then re-run `/trops-log`."
- `echo "$TROPS_DIR"` — must be non-empty.
- `echo "$TROPS_ENV"` — must be non-empty, **and** that env must be a section in
  `$TROPS_DIR/trops.cfg` (check with `trops env list` or by reading the file).
  - On failure: "No active trops env in this session. Claude's Bash shells inherit the
    environment Claude Code was launched from, so run `ontrops <env>` in that terminal
    **before** starting Claude, then re-run `/trops-log`. (An active env is required —
    `trops touch` needs the env's git work-tree to record file edits.)"

Why launch-time: the hooks run in Claude's non-interactive Bash shells, which never run
`ontrops`; they rely on `TROPS_DIR` / `TROPS_ENV` / `TROPS_SID` / `TROPS_TAGS` being
inherited from the shell that started Claude Code.

### Step 2 — Ensure the hook scripts are present and executable

Both scripts are committed in the repo:

- `.claude/hooks/trops-log-capture.sh` — Bash PostToolUse → `trops capture-cmd`
- `.claude/hooks/trops-log-touch.sh` — Edit/Write Pre+PostToolUse → `trops touch`

Confirm they exist and are executable (`chmod +x` them if not). Both are best-effort and
non-blocking: they always exit 0, so a trops failure can never block Claude's real work.

### Step 3 — Install the hooks into `.claude/settings.local.json`

Merge the block below into `.claude/settings.local.json` (create the file if missing).
**Idempotent:** if a trops-log hook with the same `command` is already registered under an
event, do not add a duplicate — leave the file as-is for that entry. Preserve any existing
settings and any non-trops hooks.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/trops-log-touch.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/trops-log-capture.sh" }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/trops-log-touch.sh" }
        ]
      }
    ]
  }
}
```

### Step 4 — Confirm

Tell the user logging is enabled and summarize what will happen:

- Every Bash command Claude runs → a `CM` entry via `trops capture-cmd`.
- Every file Claude edits (Edit/Write) → `trops touch` before and after → `FL` entries
  (new files are recorded as `ADD` on the post-edit run; the pre-edit run is skipped).
- Entries are tagged `claude` (appended to any existing `TROPS_TAGS`) and prefixed with
  `user@host`, so `trops log` shows what Claude did and where.
- **Hook changes take effect on the next session / after reloading** — remind the user
  that newly installed hooks are picked up when the session reloads them.

Then suggest: run some work, then `trops log` to see the trail.
