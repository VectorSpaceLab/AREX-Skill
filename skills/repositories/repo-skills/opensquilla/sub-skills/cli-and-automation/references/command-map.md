# CLI Command Map

This map covers day-to-day commands for an already installed OpenSquilla 0.5.3 runtime. It intentionally does not describe first-run setup, gateway launch, provider/router/search configuration, channels/MCP setup, skill catalog work, or terminal/desktop UI specifics; use the sibling sub-skills linked from `SKILL.md` for those topics.

## Gateway Dependency Guide

| Surface | Gateway needed? | Notes |
| --- | --- | --- |
| `opensquilla chat` | Yes by default | Default chat connects to a running gateway. Use `--standalone` for direct local mode without the gateway. UI renderer details belong to `tui-and-desktop`. |
| `opensquilla agent` | No running gateway required | Builds local services for one automation turn. It still needs provider/model configuration unless the task can complete without a provider. |
| `opensquilla code-task solve` | No running gateway required | Runs an agent on the host in an isolated run directory; it is not an OS sandbox. Non-interactive callers must pass `--yes`. |
| `opensquilla sessions ...` | Yes | Uses the gateway RPC session surface for list/show/resume/abort/delete/export. |
| `opensquilla memory status/index/list/search/show/raw-fallbacks/repair` | Yes | These inspect or repair gateway-backed memory state. |
| `opensquilla memory flush-session` | No running gateway required | Flushes a local persistent session DB into durable memory; requires an explicit `--session-db-path`. |
| `opensquilla memory dream` | Usually local | `--status` and `--reset-cursor` are offline-style checks; a real consolidation run can need provider access. |
| `opensquilla agents ...` | No running gateway required | Edits config directly. Restart the gateway before relying on changed agent entries. |
| `opensquilla cron ...` | Yes | Scheduled jobs are managed through the gateway. |
| `opensquilla cost` | Yes | Reads gateway-recorded usage and estimated cost. |
| `opensquilla diagnostics ...` | Yes | Toggles runtime diagnostics through the gateway. |
| `opensquilla replay` | No | Reads a recorded decision-log turn and does not re-run tools. |
| `opensquilla bundle` | No, but enriches if gateway is live | Collects a redacted diagnostics bundle; live doctor/channel snapshots are best-effort. |
| `opensquilla dist` | No | Emits a reproducible install/workspace-state inventory. |
| `opensquilla migrate ...` | No | Preview/apply profile and external-runtime migrations. Stop any gateway using the target home before applying. |
| `opensquilla recovery ...` | No | Offline profile repair/cleanup protocol, mainly for desktop/profile recovery flows. |
| `opensquilla sandbox ...` | No | Reads or writes configured default sandbox posture; restart gateway for running processes to pick up changes. |
| `opensquilla reset --key <session>` | Yes | Resets a session through the gateway and flushes memory synchronously. |
| `opensquilla init` | No | Compatibility initializer; prefer the setup/onboarding route for full modern setup. |
| `opensquilla uninstall` | No | Inventory-driven removal; stops a lifecycle-managed gateway when possible. Keeps user data unless purge flags are passed. |

## Chat and Agent

| Command | Use for | Common options |
| --- | --- | --- |
| `opensquilla chat` | Interactive terminal chat using the gateway. | `--model`, `--session`, `--ui auto|tui|plain`, `--timeout`. |
| `opensquilla chat --standalone` | Direct local chat without a gateway. | Add `--workspace`, `--workspace-strict`, and `--timeout` when file tools are involved. |
| `opensquilla agent -m "..."` | One-shot automation-friendly agent turn. | `--json`, `--agent`, `--session-id`, `--model`, `--workspace`, `--workspace-strict`, `--workspace-lockdown`, `--scratch-dir`, `--timeout`, `--max-iterations`, `--max-provider-retries`, `--thinking`, `--transcript-path`, `--usage-path`, `--event-stream-stderr`, `--session-db-path`, `--file`, `--permissions`. |
| `opensquilla code-task solve ...` | Trusted-repository coding workflow that clones/uses a disposable run directory, asks an agent to solve, and verifies. | Exactly one of `--issue`, `--task`, or `--task-file`; `--repo` unless using scratch/from-scratch modes; `--verification-mode red-green|build|scratch`; `--yes` for non-interactive; `--json` for scripts. |
| `opensquilla code-task stage-task-file` | Helper for piping task text into a private temp file. | Prints a quoted path for use with `--task-file`. |
| `opensquilla code-task smoke-imports` / `smoke-router` | Local capability checks for packaged optional modules or the bundled router. | Use for troubleshooting package/runtime gaps, not as an ordinary task runner. |

## Sessions and History

| Command | Use for | Common options |
| --- | --- | --- |
| `opensquilla sessions list` | Find recent sessions. | `--limit`, `--agent`, `--status`, `--channel`, `--since`, `--json`. |
| `opensquilla sessions show <session-key>` | Inspect metadata and preview. | `--json`. |
| `opensquilla sessions resume <session-key>` | Reopen a session in terminal chat. | Requires gateway-backed chat. |
| `opensquilla sessions abort <session-key>` | Stop a running turn without deleting the session. | `--json`. |
| `opensquilla sessions export <session-key>` | Write transcript and metadata. | `--format md|json`, `--output`. Redact before sharing. |
| `opensquilla sessions delete <session-key>` | Delete old session state. | `--yes` skips confirmation. Export first if the record matters. |

## Memory

| Command | Use for | Common options |
| --- | --- | --- |
| `opensquilla memory status` | Check memory backend health. | `--agent`, `--deep`, `--json`, `--config`. |
| `opensquilla memory index` | Sync or rebuild the memory search index. | `--agent`, `--force`, `--json`. |
| `opensquilla memory list` | List durable memory source files. | `--agent`, `--json`. |
| `opensquilla memory search "query"` | Search memory or prior sessions. | `--agent`, `--limit`, `--source memory|sessions|all`, `--json`. |
| `opensquilla memory show <path>` | Show one memory source. | `--agent`, `--from-line`, `--lines`, `--json`. |
| `opensquilla memory flush-session` | Turn a local persistent session DB transcript into searchable durable memory. | Required `--key` and `--session-db-path`; optional `--workspace`, `--config`, `--agent`, `--message-window`, `--timeout`, `--flush-max-chars`, `--segment-mode`, `--segment-max-chars`, `--segment-overlap-messages`, `--usage-path`, `--json`. |
| `opensquilla memory raw-fallbacks list/show` | Inspect raw fallback receipts from failed/degraded memory flushes. | `--agent`, `--json`; `show` also supports line slicing. |
| `opensquilla memory repair list/show/run` | Inspect or repair degraded compaction memory records. | `--agent`, `--summary-id`, `--session-key`, `--compaction-id`, `--limit`, `--entry-limit`, `--json`. |
| `opensquilla memory dream` | Run or inspect Dream consolidation for an agent. | `--agent`, `--force`, `--status`, `--reset-cursor`. |

## Durable Agents and Scheduling

| Command | Use for | Common options |
| --- | --- | --- |
| `opensquilla agents list` | Show built-in and configured durable agents. | `--json`, `--config`. |
| `opensquilla agents add <agent-id>` | Add a durable agent profile. | `--name`, `--description`, `--workspace`, `--model`, `--json`, `--config`. Restart the gateway afterward. |
| `opensquilla agents delete <agent-id>` | Remove a durable agent entry from config. | `--force`, `--json`, `--config`. Workspace and state are left untouched. |
| `opensquilla cron list` | List scheduled jobs. | `--agent`, `--json`. |
| `opensquilla cron status <job-id>` | Inspect one job. | `--json`. |
| `opensquilla cron add` | Add interval, cron-expression, or one-time scheduled work. | One schedule source: `--every`, `--cron`/`--expression`, or `--at`; required `--text`; optional `--name`, `--agent`, `--job-kind`, `--session-target`, `--timeout`, `--tz`, `--wake`, `--exact`, `--jitter`, delivery/failure options, `--json`. |
| `opensquilla cron update <job-id>` | Change schedule, text, enabled state, timeout, timezone, wake, or failure destination. | `--enabled`/`--disabled`, schedule flags, failure destination flags, `--json`. |
| `opensquilla cron run <job-id>` | Trigger a scheduled job immediately. | `--yes`, `--json`. |
| `opensquilla cron remove <job-id>` | Delete a job. | `--yes`, `--json`. |
| `opensquilla cron runs <job-id>` | List recent job runs. | `--limit`, `--json`. |

## Cost, Diagnostics, Replay, Bundle, and Dist

| Command | Use for | Common options |
| --- | --- | --- |
| `opensquilla cost` | Show gateway-recorded usage and estimated cost. | `--by-model`, `--json`. |
| `opensquilla diagnostics status` | Show effective diagnostics and raw-capture state. | `--json`, `--config`. |
| `opensquilla diagnostics on` | Enable runtime diagnostics. | `--raw` only when raw provider-turn evidence is explicitly needed; `--json`. |
| `opensquilla diagnostics off` | Disable diagnostics and runtime raw capture. | `--json`. |
| `opensquilla replay --session <key> --turn <id>` | Print a recorded decision-log turn. | Read-only; no tools are re-executed. |
| `opensquilla bundle` | Collect redacted logs/error records/config into a zip. | `--output`, `--days`, `--session`, `--include-content`, `--json`. |
| `opensquilla dist` | Emit a reproducible workspace-state inventory. | `--output` writes to a file; otherwise prints JSON to stdout. |

## Migration, Recovery, Sandbox, Reset, Init, and Uninstall

| Command | Use for | Common options |
| --- | --- | --- |
| `opensquilla migrate` | Auto-detect supported sources and preview or apply migrations. | `--source`, `--config`, `--apply`, `--migrate-secrets`, `--overwrite`, `--preset`, `--include`, `--exclude`, `--skill-conflict`, `--persona-conflict`, `--json`. |
| `opensquilla migrate openclaw` | Import OpenClaw state into OpenSquilla-native files. | Preview by default; add `--apply` only after reviewing. Supports persona and skill conflict controls. |
| `opensquilla migrate hermes` | Import Hermes Agent state into OpenSquilla-native files. | Preview by default; supports `--profile`, secrets, presets, include/exclude, and skill conflict controls. |
| `opensquilla migrate opensquilla` | Import another OpenSquilla CLI/Desktop/portable profile. | `--kind`, `--source`, `--home`, `--dry-run`/`--apply`, `--replace-target`, `--confirm-replace-target`, `--inspect-candidate`, `--json`. Whole-profile replacement requires exact target confirmation. |
| `opensquilla recovery ...` | Inspect and repair desktop/profile state offline. | Commands include `inspect`, `reconcile`, `choose-workspace`, `apply-settings`, `recover-settings`, `recover-config`, `restore-profile`, `recover-transaction`, profile consolidation, and cleanup inspect/apply. Most require exact paths and transaction/revision values. |
| `opensquilla sandbox status` | Show configured default sandbox posture. | `--config`, `--json`. |
| `opensquilla sandbox safe` / `full` / `reset` | Change configured default posture. | Restart the gateway for running processes to apply changes. `full` disables runtime sandboxing and skips approval/sensitive-path gates. |
| `opensquilla reset --key <session-key>` | Reset a session and flush memory synchronously through the gateway. | `--gateway` can override the gateway URL. |
| `opensquilla init` | Compatibility first-run initializer. | Interactive; prefer the setup/onboarding route for modern setup. |
| `opensquilla uninstall` | Remove OpenSquilla inventory items. | `--dry-run`, `--yes`, `--json`, `--purge-state`, `--purge-config`, `--purge-all`, `--remove-source-dir`, `--confirm-purge-all`. Keeps user data by default. |
