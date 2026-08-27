# CLI and Automation Troubleshooting

Use this reference when ordinary CLI commands fail, block, produce unsafe-looking output, or need a recovery workflow. Keep provider/router/search setup questions in `../../configuration-and-routing/SKILL.md`; gateway startup/readiness in `../../setup-and-gateway/SKILL.md`; channel/MCP delivery in `../../channels-and-integrations/SKILL.md`; skill/meta-skill catalog issues in `../../skills-and-meta/SKILL.md`; and terminal/desktop launch behavior in `../../tui-and-desktop/SKILL.md`.

## Command Cannot Reach the Gateway

Affected commands include `sessions`, most `memory` inspection/repair commands, `cron`, `cost`, `diagnostics`, default `chat`, and `reset`.

Triage:

```sh
opensquilla gateway status
opensquilla doctor
```

If the gateway is not running or is on a different host/port, fix that first via the setup/gateway route. If a command supports an explicit gateway URL, pass it instead of relying on defaults. For `chat`, `--standalone` avoids the gateway but has a narrower feature surface than gateway-backed chat.

## No Provider or Wrong Model During Automation

Symptoms: `agent` or `chat --standalone` starts locally but reports no configured provider/API key, wrong model, provider timeout, or unexpected router behavior.

Actions:

- Use setup/onboarding for missing provider credentials.
- Use provider/router configuration guidance for model selection and routing policy.
- For a single `agent` run, `--model provider/model` overrides the configured/default model.
- For a durable agent, set `opensquilla agents add <id> --model provider/model` or edit config, then restart the gateway.
- Use `--max-provider-retries`, `--request-timeout-seconds`, and `--timeout` to bound unstable provider calls in automation.

Do not present live provider behavior as locally verified unless the user has provided fresh live evidence. This sub-skill's inspection evidence was CPU-only and verified local command/import surfaces, not live provider billing or long-context model quality.

## Session Export or Replay Might Leak Private Data

Session exports, replay output, diagnostics, raw captures, and bundles can expose prompts, tool outputs, local paths, channel identifiers, project names, and secrets that appeared in a conversation.

Safer workflow:

```sh
opensquilla sessions export <session-key> --format md --output session.redaction-source.md
# redact locally before sharing
opensquilla replay --session <session-key> --turn <turn-id>
opensquilla bundle --session <session-key> --days 3 --output support-bundle.zip
```

Only use `bundle --include-content` or `diagnostics on --raw` when the user accepts the privacy trade-off or a maintainer explicitly needs that evidence.

## Memory Search Looks Stale or Empty

Check health and force an index refresh:

```sh
opensquilla memory status --deep --json
opensquilla memory index --force --json
opensquilla memory search "known preference" --source all --json
```

If long-session compaction degraded or a flush fell back to raw backup:

```sh
opensquilla memory raw-fallbacks list --json
opensquilla memory repair list --json
opensquilla memory repair show --summary-id <id> --json
opensquilla memory repair run --summary-id <id> --json
```

If exact old wording matters, use `sessions export` instead of relying on memory. Memory is for durable recall, not archival transcript fidelity.

## `memory flush-session` Fails or Produces Raw Fallback

Common causes:

- Missing or wrong `--session-db-path` for local agent runs.
- Wrong `--key` or agent id for the persisted session.
- Transcript too large without explicit segmentation bounds.
- Provider unavailable during LLM summarization.
- Workspace output path not intended or not writable.

Actions:

```sh
opensquilla memory flush-session \
  --key <session-key> \
  --session-db-path /path/to/session.sqlite \
  --message-window all \
  --segment-mode auto \
  --usage-path flush-usage.json \
  --json
```

If it still degrades to raw backup, inspect the fallback receipt and rerun with narrower `--message-window`, lower segment sizes, or after fixing provider/config issues. Treat raw fallback as preservation, not successful searchable memory.

## Cron Job Does Not Run or Deliver

Check gateway and job state first:

```sh
opensquilla gateway status
opensquilla cron list --json
opensquilla cron status <job-id> --json
opensquilla cron runs <job-id> --json
```

Then check likely configuration mistakes:

- Only one schedule source is allowed: `--every`, `--cron`/`--expression`, or `--at`.
- Interval syntax accepts values such as `30s`, `5m`, and `1h`; invalid or fractional cases are rejected.
- `--session-target current` requires a runtime session binding; use `isolated` for ordinary scheduled work.
- `--webhook-url` is mutually exclusive with `--announce` and `--no-deliver`.
- Webhook tokens should come from `--webhook-token-env` or `--webhook-token-file`; inline tokens can leak into shell history.
- Channel delivery requires a configured channel; route channel status/setup to `../../channels-and-integrations/SKILL.md`.
- Primary delivery destinations are not patched in place; remove and re-add a job if the destination must change.

## Code-Task Blocks Before Doing Work

`code-task solve` intentionally refuses ambiguous or unsafe input.

Fixes:

- Pass exactly one of `--issue`, `--task`, or `--task-file`.
- Pass `--repo` for normal `red-green` tasks.
- Do not combine `--repo` with `--verification-mode scratch`.
- Do not use `--issue` with scratch mode.
- Add `--yes` on CI, background jobs, non-TTY shells, or whenever `--json` is used.
- Remember that `code-task` is trusted-host execution, not OS sandboxing. Do not run it against an untrusted repository.

If optional runtime smoke checks fail:

```sh
opensquilla code-task smoke-imports --module mcp
opensquilla code-task smoke-router
```

The inspection build for this skill successfully imported `mcp`, `lightgbm`, `onnxruntime`, `tokenizers`, `tiktoken`, and `jieba`, but a user's install may omit optional extras. Route missing package installation and first-run setup to `../../setup-and-gateway/SKILL.md`; route MCP usage/setup to `../../channels-and-integrations/SKILL.md`; route router-model selection to `../../configuration-and-routing/SKILL.md`.

## Migration Preview Differs From Apply Expectations

Migration is dry-run by default. If nothing changes, check whether `--apply` was intentionally omitted.

Safer apply sequence:

```sh
opensquilla migrate openclaw --json
opensquilla migrate openclaw --preset user-data --exclude <ids> --json
opensquilla migrate openclaw --preset user-data --exclude <ids> --apply
```

Conflict handling:

- Use `--skill-conflict skip|overwrite|rename` for imported skill name collisions.
- Use OpenClaw `--persona-conflict prompt|use-opensquilla|use-openclaw|merge|skip` when persona files conflict.
- Use `--overwrite` only after the user understands item-level replacement and backups.
- Use `--migrate-secrets` only after reviewing which secrets will be copied.
- When both OpenClaw and Hermes are detected in a non-interactive context, explicitly pass `--source openclaw,hermes` or a subset.
- For `migrate opensquilla`, whole-profile replacement requires `--replace-target` and exact `--confirm-replace-target`; do not guess the path.

After apply, validate with a gateway start, a small chat/agent check, memory status, and review of migration summaries/notes.

## Recovery Commands Need Exact Transaction Data

Recovery commands are mostly offline profile/desktop safety protocols. Do not invent paths, transaction ids, expected revisions, cleanup modes, or scope fingerprints. Use values from a preceding recovery inspection/report.

Safe pattern:

```sh
opensquilla recovery inspect --home /path/to/profile-home --json
opensquilla recovery recover-config --home /path/to/profile-home --json
opensquilla recovery recover-transaction \
  --home /path/to/profile-home \
  --transaction-id <reported-id> \
  --expected-revision <reported-revision> \
  --json
```

For desktop UI launch, profile ownership, Electron user data paths, and shell-specific cleanup UX, route to `../../tui-and-desktop/SKILL.md`.

## Sandbox Posture Is Confusing

There are two related controls:

- Global/default posture: `opensquilla sandbox status|safe|full|reset` writes configuration and requires a gateway restart for running processes.
- Per-run posture: `opensquilla agent --permissions restricted|on|bypass|full` affects a one-shot run.

Guidance:

```sh
opensquilla sandbox status --json
opensquilla sandbox safe
opensquilla gateway restart
opensquilla agent --permissions restricted --workspace /path/to/project -m "Inspect only"
```

`safe` uses system sandboxing and configured Safe policies. `full` disables runtime sandboxing and skips approval/sensitive-path gates. Legacy aliases such as bypass/trust/on may exist, but prefer the visible `safe`, `full`, and `reset` commands. Do not claim `code-task` becomes OS-sandboxed just because a sandbox setting exists; its source-documented posture is trusted-host execution.

## Uninstall or Purge Refuses to Run

The uninstaller is intentionally conservative.

Expected behavior:

- `opensquilla uninstall --dry-run` previews the plan and touches nothing.
- Default uninstall keeps user data.
- Non-interactive or `--json` surfaces require `--yes`.
- `--purge-state` and `--purge-config` opt into deleting runtime state or config/secrets.
- `--purge-all` requires the exact confirmation phrase even with `--yes`.
- Desktop-profile purges are refused and routed to complete desktop cleanup.
- Source installs surface manual checkout removal rather than deleting an arbitrary source tree automatically.

Safer script sequence:

```sh
opensquilla uninstall --dry-run --json
opensquilla uninstall --yes --json
```

Only add purge flags after the user has confirmed the data-loss scope.

## Bundle, Dist, or Replay Output Is Not What a Script Expected

- `dist` prints JSON to stdout by default; with `--output`, stdout is the output path.
- `bundle --json` prints bundle manifest/path JSON; without `--json`, it prints human-readable lines.
- `bundle` may silently omit live doctor/channel enrichment if the gateway is down; the bundle itself can still succeed.
- `replay` exits non-zero if no matching decision-log entry exists for the session/turn pair.
- `agent --event-stream-stderr` sends progress events to stderr; stdout remains the final result. Scripts must not treat all stderr lines as errors.

## Concurrent Run or Profile Lock Failure

Write-capable agent runs can conflict when they share one profile/state root. Isolate parallel jobs with separate state roots, gateway state roots, session DBs, workspaces, scratch directories, transcripts, and usage paths. If a copied profile contains a `state_dir`, rewrite it or it can defeat `OPENSQUILLA_STATE_DIR` isolation.

## Source Scripts Were Not Bundled

The assigned source scripts for this sub-skill were live/provider/maintainer harnesses rather than safe general runtime helpers:

- `live_long_task_case_driver.py`: reference-only live automation harness.
- `live_long_task_release_gate.py`: reference-only release/maintainer gate.
- `live_long_context_chat_smoke.py`: reference-only live model/provider smoke.
- `live_tokenrhythm_billing_audit.py`: reference-only provider-billing/live dependency.
- `long_task_fault_proxy.py`: excluded internal fault-test harness.

Use the command patterns in this generated skill instead of expecting those source scripts to exist at runtime.
