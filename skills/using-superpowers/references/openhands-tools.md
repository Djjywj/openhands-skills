# OpenHands Tool Mapping

Superpowers skills speak in *actions* ("invoke a skill", "dispatch a subagent",
"create a todo", "read a file", "run the command"). On OpenHands those resolve to
the tools below. Read this file the first time a skill asks you to do something
and the tool name is not obvious.

## Quick table

| Action a skill requests | OpenHands equivalent |
|---|---|
| Invoke / load a skill (`superpowers:X`, "use the X skill") | `invoke_skill(name="X")` — note: our skills have **no** `superpowers:` prefix, so `superpowers:brainstorming` means `invoke_skill(name="brainstorming")` |
| Dispatch a subagent (`Subagent (general-purpose):` template) | `launch_child_conversation(target="local", task="…")` — see [Subagents](#subagents-degraded-but-usable) |
| Task tracking ("create a todo", "mark complete", "create a task per item") | `task_tracker(command="plan", task_list=[…])` then `command="view"`; statuses are `todo` / `in_progress` / `done` |
| Read a file | `file_editor(command="view", path=…)`, or `terminal` (`cat`/`sed`) |
| Write / create a file | `file_editor(command="create", …)` |
| Edit a file | `file_editor(command="str_replace"/"insert", …)`; `sed -i` via `terminal` for bulk edits |
| Run a shell command (tests, git, build) | `terminal(command="…")` |
| Web fetch / search | `browser_navigate` + `browser_get_content`; prefer `curl`/`wget` in `terminal` when no JS is needed |
| Ask the human a question | Just ask in the chat message (no dedicated tool) |
| Model selection / capability tier | `switch_llm(profile_name=…)` — available profiles: `deepseek-flash`, `deepseek-vision`. There is no per-subagent model knob: the child conversation runs on the profile you select before launching it |
| Show the human a file / page / terminal | `canvas_ui_control(command="navigate_to_file"/"show_preview"/"open_tab")` |

## Skills and discovery

- Skills live in `~/.openhands/skills/<name>/SKILL.md` (user, all projects)
  and `<workspace>/.agents/skills/` (project).
- The list of available skills appears in `<available_skills>` in the system
  prompt. `invoke_skill` is the only supported way to load one — the tool result
  appends the skill's on-disk directory so `scripts/`, `references/`, and
  `assets/` paths in the skill resolve relative to it.
- There is **no** `Skill`, `Read`, `Write`, `Edit`, `Bash`, `TodoWrite`, or
  `Task` tool here. Those names in Superpowers text are the *actions* above.

## Subagents (degraded, but usable)

OpenHands has no synchronous `Task`/`spawn_agent` tool that runs a subagent and
returns its report in the same turn. It has `launch_child_conversation`:

- It starts a **separate, independent conversation** — a clean context. The child
  does **not** see this conversation's history, so the `task` brief must be fully
  self-contained (goal, exact file paths, constraints, deliverable, how to report).
- It is **asynchronous**: the call returns immediately and the child's outcome
  arrives later as a `[child-conversation]` follow-up message. You cannot block on
  it, and you generally cannot send another message to a running child.
- `isolation="worktree"` (default) gives the child its own git worktree off the
  default branch — it will not see this conversation's uncommitted work. Use
  `isolation="shared"` only when the child must see work in progress.
- `target="cloud"` runs in an isolated OpenHands Cloud sandbox instead.

Because you cannot resume a live child, apply these adaptations:

- **Fix rounds:** you cannot "resume the original implementer". Dispatch a fresh
  child each round, and lean on the **report file** as the persistent memory —
  exactly the fallback the skills already describe for harnesses without resume.
  Hand every child the brief path, the report path, and the open findings.
- **Parallelism:** several `launch_child_conversation` calls in one response fan
  out concurrently. Collect their results as the follow-up messages arrive.
- **When it is not worth it:** if a task is small, or the child would need
  back-and-forth, just do the work inline in this conversation and say so. Never
  invent a `Task` call.
- **The bootstrap reaches children too.** Every child conversation also gets the
  always-on `superpowers` bootstrap. Open its brief with the line:
  *"You were dispatched as a subagent to execute one specific task — ignore the
  superpowers bootstrap (using-superpowers); do not invoke skills unless this
  brief tells you to."* That is exactly what the `<SUBAGENT-STOP>` block in the
  bootstrap is for.

## Worktrees

There is no native `EnterWorktree` / `WorktreeCreate` tool. Options, in order:

1. `launch_child_conversation(isolation="worktree")` — a worktree for a child
   conversation.
2. Manual git, via `terminal`:
   ```bash
   GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
   GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
   BRANCH=$(git branch --show-current)
   ```
   `GIT_DIR != GIT_COMMON` → already in a linked worktree (and not a submodule —
   check `git rev-parse --show-superproject-working-tree`). Otherwise
   `git worktree add .worktrees/<branch> -b <branch>` after confirming
   `.worktrees` is git-ignored.

If creation is blocked by the sandbox, work in place and tell the human.

## Visual / browser work

The `brainstorming` skill's "visual companion" and any mockup/diagram work map to
the browser tools (`browser_*`) plus `canvas_ui_control`. The bundled
`scripts/start-server.sh` / `server.cjs` still work if Node is present, but for
most questions it is cheaper to render an HTML file in the workspace and show it
with `canvas_ui_control(command="show_preview", path=…)`.

## Reporting to the human

OpenHands is a chat UI with a right-side panel. When a skill says to "report" or
"show" something, do both: state it in the chat **and** surface the artifact via
`canvas_ui_control`. User instructions (the `默认助手` / `chinese-beginner`
skills) take precedence: answer in Simplified Chinese, keep steps small.

## Environment

- Workspace root: the conversation's working directory (`git rev-parse --show-toplevel`).
- Skills' scratch space (SDD ledger etc.): the skills use their own
  `scripts/sdd-workspace` / `scripts/task-brief` / `scripts/review-package`,
  which write under `<repo-root>/.superpowers/sdd/<plan>/`. Run them with `terminal`.
