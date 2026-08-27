# Automation Patterns

Use these patterns when OpenSquilla is already installed and configured enough for the selected provider/model. For provider setup, router selection, and search provider choice, route to `../../configuration-and-routing/SKILL.md`. For gateway startup and readiness, route to `../../setup-and-gateway/SKILL.md`.

## One-Shot Agent Runs

Basic machine-readable run:

```sh
opensquilla agent --json -m "Summarize the current project state in three bullets."
```

Bounded workspace run:

```sh
opensquilla agent \
  --workspace /path/to/project \
  --workspace-strict \
  --workspace-lockdown \
  --scratch-dir /path/to/project/.opensquilla-scratch \
  --timeout 600 \
  --max-iterations 20 \
  --max-provider-retries 2 \
  --transcript-path run.transcript.jsonl \
  --usage-path run.usage.json \
  --json \
  -m "Inspect this repository and return a short JSON risk summary."
```

Useful controls:

- `--workspace` sets the root the agent should operate in.
- `--workspace-strict` restricts read-side file tools to the workspace.
- `--workspace-lockdown` contains writes to the workspace or scratch directory; it requires a workspace, configured workspace, or `--scratch-dir`.
- `--workspace-lockdown-deny-paths` adds workspace-relative write-deny globs; repeat or comma-separate values.
- `--scratch-dir` gives tool-generated scripts/logs/candidate patches a known place.
- `--timeout`, `--max-iterations`, `--iteration-timeout-seconds`, `--tool-timeout-seconds`, `--request-timeout-seconds`, and `--max-provider-retries` prevent unattended runs from hanging indefinitely.
- `--length-capped-continuations` bounds automatic continuation after length-limited provider output.
- `--thinking` can override configured reasoning effort (`off|minimal|low|medium|high|xhigh|adaptive`).
- `--file`/`-f` attaches local files; repeat it for multiple attachments.
- `--no-memory-capture` avoids recording the invocation into durable searchable memory.
- `--stateless` or `--clean-room` uses clean-room prompt bootstrap; `--stateless-keep-project-rules` preserves project rules only.
- `--permissions restricted|on|bypass|full` overrides the permission profile for a single run. Treat `bypass`/`full` as trusted-task modes.

The JSON payload includes run status, agent id, session key, text, usage, errors, workspace posture, routing metadata, transcript/usage paths, and public artifact metadata. Artifact metadata is intentionally public-facing and should not expose session keys.

## Progress Event Stream

Add `--event-stream-stderr` when an orchestrator needs progress events without changing stdout:

```sh
opensquilla agent \
  --event-stream-stderr \
  --json \
  -m "Run a bounded investigation."
```

Consumers should drain stderr continuously, parse it line by line, and accept only JSON objects whose `_event` field is `true`. Normal warnings or diagnostics can also appear on stderr. Known event kinds include `router_decision`, `thinking`, `text_delta`, `run_heartbeat`, `tool_use_start`, `tool_result`, `warning`, `error`, `artifact`, and `done`. Read the final result from stdout, not from the event stream.

## Parallel Agent Subprocesses

A write-capable agent holds a profile-wide writer lease. Parallel automation that shares one OpenSquilla state root can conflict. Give each child a separate profile/state root and separate output paths:

```sh
OPENSQUILLA_STATE_DIR=/tmp/opensquilla-agent-a \
OPENSQUILLA_GATEWAY_STATE_DIR=/tmp/opensquilla-agent-a/state \
  opensquilla agent \
    --session-db-path /tmp/opensquilla-agent-a/session.sqlite \
    --transcript-path /tmp/opensquilla-agent-a/transcript.jsonl \
    --usage-path /tmp/opensquilla-agent-a/usage.json \
    --workspace /path/to/project-a \
    --scratch-dir /path/to/project-a/.opensquilla-scratch \
    --json \
    -m "Task A" &
```

Do not assume `OPENSQUILLA_STATE_DIR` overrides a `state_dir` already present in copied config files or profile homes. When cloning a profile for parallel runs, remove or rewrite `state_dir` and set `OPENSQUILLA_GATEWAY_STATE_DIR` intentionally. On Windows, pass environment variables through the child-process environment instead of relying on POSIX inline assignment syntax.

## Chat Automation Choices

- Use `opensquilla chat` for an interactive gateway-backed session.
- Use `opensquilla chat --session <session-key>` to resume from terminal chat.
- Use `opensquilla chat --standalone --workspace /path/to/project` when the gateway is not running and direct local chat is sufficient.
- Add `--workspace-strict` in standalone chat when file reads should stay inside that workspace.
- Use `--ui plain` for a rescue terminal renderer; UI-specific behavior belongs to `../../tui-and-desktop/SKILL.md`.

## Code-Task Runs

`code-task solve` is for trusted repositories. It runs an OpenSquilla agent on the host and may install dependencies; it is not an OS sandbox.

```sh
opensquilla code-task solve \
  --repo /path/to/repo \
  --task-file task.md \
  --verification-mode red-green \
  --timeout 5400 \
  --yes \
  --json
```

Rules pinned by the CLI:

- Pass exactly one task source: `--issue`, `--task`, or `--task-file`.
- Pass `--repo` unless using `--verification-mode scratch` or a from-scratch build-mode task.
- `--verification-mode red-green` is the default for existing repos.
- `--verification-mode build` is for app/artifact delivery checks.
- `--verification-mode scratch` creates an empty throwaway repo and must not be combined with `--repo` or `--issue`.
- Non-interactive runs (`--json`, CI, daemons, background tasks, or non-TTY stdin) must include `--yes` to acknowledge trusted-host execution.
- Work happens in an OpenSquilla run directory first; the source repo is updated only after the workflow collects and verifies a productive change.

For local capability checks, `code-task smoke-imports` verifies optional packaged modules and `code-task smoke-router` verifies the bundled router classifier. These are diagnostics, not general task runners.

## Scheduled Runs

Scheduled jobs run through the gateway. Start or connect to the gateway first, then add one schedule source.

Interval job:

```sh
opensquilla cron add \
  --every 1h \
  --text "Summarize important project updates" \
  --name hourly-project-check \
  --json
```

Cron-expression job with timezone:

```sh
opensquilla cron add \
  --cron "0 9 * * 1-5" \
  --tz "America/Los_Angeles" \
  --text "Prepare a short weekday briefing" \
  --name weekday-briefing
```

One-time job:

```sh
opensquilla cron add \
  --at "2026-06-01T09:00:00+00:00" \
  --text "Remind me to review the launch checklist" \
  --name launch-checklist-reminder
```

Delivery choices:

- Default scheduled output targets an isolated session.
- Use `--session-target isolated|session|main` intentionally. The `current` target is only valid when the runtime has a current session binding.
- Use `--no-deliver` for private scheduled work that should not be posted anywhere.
- Use `--announce`, `--channel`, `--to`, and `--account` for channel delivery; route channel configuration questions to `../../channels-and-integrations/SKILL.md`.
- Use `--webhook-url` for webhook delivery. Prefer `--webhook-token-env` or `--webhook-token-file` over inline `--webhook-token` so secrets do not enter shell history.
- Use `--failure-mode channel|webhook` and the corresponding failure destination flags when alerts should go somewhere separate from the primary delivery.

Manage jobs:

```sh
opensquilla cron list --json
opensquilla cron status <job-id> --json
opensquilla cron update <job-id> --disabled --json
opensquilla cron run <job-id> --yes --json
opensquilla cron runs <job-id> --limit 50 --json
opensquilla cron remove <job-id> --yes --json
```

Primary delivery destinations are not patched in place from the CLI; remove and re-add a job when the main channel/webhook destination changes.

## Durable Agent Profiles

Create a durable agent when a recurring work stream needs a stable workspace, model, name, description, or channel/scheduling target. Do not create a new agent for every conversation; use sessions for ordinary continuity.

```sh
opensquilla agents add research \
  --name Research \
  --description "Research and synthesis workspace" \
  --workspace /path/to/research \
  --model provider/model
opensquilla gateway restart
```

Then use it from sessions, one-shot runs, or cron:

```sh
opensquilla agent --agent research -m "Summarize the current research notes."
opensquilla sessions list --agent research
opensquilla cron add --agent research --every 1h --text "Summarize new research notes" --name research-hourly
```

Deleting an agent removes its config entry only; it leaves workspace files and state untouched.

## Profile and Config Selection

The top-level `--profile` option selects a named OpenSquilla profile home. Command groups that accept `--config` can also target a specific config file. Use explicit profile/config selection in automation instead of relying on whichever shell or current directory happens to be active.

If proxy environment variables are present and a command warns that proxy variables are ignored, set `OPENSQUILLA_TRUST_ENV=1` only when the user intends OpenSquilla to honor those environment proxy settings.
