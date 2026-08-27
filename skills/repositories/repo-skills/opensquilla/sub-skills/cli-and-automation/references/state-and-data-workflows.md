# State and Data Workflows

Use this reference when the user's task is about existing OpenSquilla state: sessions, memory, diagnostics, cost, replay logs, migration, recovery, inventories, sandbox posture, reset, initialization compatibility, or uninstall.

## Sessions and History

Session commands are gateway-backed. If a session command cannot connect, route to gateway readiness in `../../setup-and-gateway/SKILL.md` before debugging the session itself.

Typical flow:

```sh
opensquilla sessions list --limit 20 --json
opensquilla sessions show <session-key> --json
opensquilla sessions resume <session-key>
```

Operational guidance:

- Use `sessions list --agent <id>`, `--status <status>`, `--channel <name>`, or `--since <ISO-or-epoch>` to narrow a large history.
- `sessions resume` opens terminal chat on the resolved session key so the conversation state continues instead of starting fresh.
- `sessions abort` stops a running turn if one exists; it does not delete the session.
- `sessions delete` is cleanup. Use `--yes` in scripts and export first if the transcript may be needed.

Safe export:

```sh
opensquilla sessions export <session-key> --format md --output session.md
opensquilla sessions export <session-key> --format json --output session.json
```

Before sharing an export, remove secrets, provider tokens, private local paths, customer/project names, channel identifiers, and raw tool/provider content that should not be public.

## Memory Index, Search, Flush, and Repair

Most `opensquilla memory` inspection commands go through the gateway. Use them after startup when the user wants to inspect durable recall:

```sh
opensquilla memory status --deep --json
opensquilla memory index --force --json
opensquilla memory list --json
opensquilla memory search "deployment decision" --source all --json
opensquilla memory show <path> --from-line 1 --lines 80
```

Use memory for stable preferences, reusable project facts, previous decisions, and short durable notes. Do not store API keys, large private dumps, or exact transcripts that belong in session export.

Flush a local persistent session DB into memory when exact session continuity must become searchable durable memory:

```sh
opensquilla memory flush-session \
  --key <session-key> \
  --session-db-path /path/to/session.sqlite \
  --message-window all \
  --segment-mode auto \
  --usage-path flush-usage.json \
  --json
```

Flush notes:

- `--message-window all` makes a full-session flush explicit.
- `--flush-max-chars`, `--segment-max-chars`, and `--segment-overlap-messages` control long transcript segmentation.
- `--workspace` forces memory output into workspace-backed `memory/*.md` style output.
- If a flush degrades to a raw backup, that backup is not searchable durable memory; inspect `memory raw-fallbacks` and repair or re-flush as appropriate.

Repair degraded compaction memory records when diagnostics or status points there:

```sh
opensquilla memory repair list --json
opensquilla memory repair show --summary-id <id> --json
opensquilla memory repair run --summary-id <id> --json
```

For Dream consolidation:

```sh
opensquilla memory dream --agent main --status
opensquilla memory dream --agent main --reset-cursor
opensquilla memory dream --agent main
```

Status and cursor reset are lightweight. A real Dream run can need provider access.

## Diagnostics, Cost, Replay, and Bundles

Use diagnostics only long enough to capture the evidence needed for a confusing turn:

```sh
opensquilla diagnostics status --json
opensquilla diagnostics on
# reproduce or inspect the behavior
opensquilla diagnostics off
```

Only enable raw capture when a maintainer asks for provider-turn evidence:

```sh
opensquilla diagnostics on --raw
```

Raw diagnostics may include private prompts, tool outputs, local paths, or provider-visible content. Turn it off after collection.

Cost inspection is gateway-backed:

```sh
opensquilla cost --json
opensquilla cost --by-model --json
```

Use it after routed, tool-heavy, channel, or long-context tasks. If a premium model dominates cost, route provider/router policy questions to `../../configuration-and-routing/SKILL.md` instead of treating cost output as a CLI bug.

Replay is read-only and does not re-run tools:

```sh
opensquilla replay --session <session-key> --turn <turn-id>
```

Use replay when an earlier turn is surprising but the chat has moved on, or when a bug report needs concise decision-log evidence. Pair it with `sessions export` when exact conversation context matters.

Bundle support evidence:

```sh
opensquilla bundle --days 3 --session <session-key> --output opensquilla-bundle.zip
opensquilla bundle --days 3 --session <session-key> --json
```

Bundles are redacted by default. `--include-content` can include conversation content/raw turn-call capture and should be used only when the user understands the privacy risk.

Inventory the installed runtime:

```sh
opensquilla dist > workspace-state.json
opensquilla dist --output workspace-state.json
```

`dist` emits a reproducible inventory of bundled channels, tools, safety defaults, package metadata, and Python requirement.

## Migration and Recovery

Migration commands are designed as preview-first workflows. Before applying:

1. Stop any running gateway that is using the target home.
2. Make a manual whole-home backup if whole-home rollback matters.
3. Run a dry run with `--json` and inspect the item-level report.
4. Avoid `--migrate-secrets` until the user has reviewed which secrets will be copied.
5. Choose conflict behavior deliberately.

Auto-detect and preview:

```sh
opensquilla migrate --json
opensquilla migrate --source openclaw,hermes --json
```

External runtimes:

```sh
opensquilla migrate openclaw --json
opensquilla migrate openclaw --apply
opensquilla migrate hermes --json
opensquilla migrate hermes --apply
```

Common controls:

- `--source PATH` selects a source home.
- `--config PATH` selects the OpenSquilla config to preview/write for foreign migrations.
- `--preset user-data|full` narrows or expands imported data.
- `--include IDS` / `--exclude IDS` select item ids.
- `--skill-conflict skip|overwrite|rename` controls imported skill collisions.
- `--migrate-secrets` copies recognized secrets; default is false.
- `--overwrite` allows replacing item conflicts after item-level backups where supported.
- OpenClaw also supports `--persona-conflict prompt|use-opensquilla|use-openclaw|merge|skip` for identity/persona files.

Self/profile import:

```sh
opensquilla migrate opensquilla --kind cli-home --source /path/to/source-home --json
opensquilla migrate opensquilla --kind desktop-home --source /path/to/source-home --apply --replace-target --confirm-replace-target /exact/target-home --json
opensquilla migrate opensquilla --kind windows-portable --inspect-candidate --json
```

Whole-profile replacement requires an exact `--confirm-replace-target` path. Do not use `--config` for self-migration when the command tells you to use profile/state targeting instead.

Validate after applying a migration:

```sh
opensquilla gateway start --json
opensquilla agent -m "Briefly summarize your active persona and available memory."
opensquilla memory status --deep
```

Also inspect migrated workspace files, imported skill directories, and migration summaries/notes. If behavior looks wrong, stop the gateway, review the migration report, then re-run with narrower `--preset`, `--include`, or `--exclude` settings.

Recovery commands are offline/profile-oriented. They are used when desktop/profile state cannot safely start or when a migration/settings transaction was interrupted:

```sh
opensquilla recovery inspect --home /path/to/profile-home --json
opensquilla recovery reconcile --home /path/to/profile-home --json
opensquilla recovery recover-config --home /path/to/profile-home --json
opensquilla recovery recover-transaction \
  --home /path/to/profile-home \
  --transaction-id <id> \
  --expected-revision <n> \
  --json
```

Treat recovery commands as protocol commands: preserve exact `transaction-id`, `expected-revision`, profile kind, cleanup mode, and path values from the prior inspection/report. UI-specific desktop launch and shell behavior belongs to `../../tui-and-desktop/SKILL.md`.

## Reset, Init, Sandbox, and Uninstall

Reset a gateway-backed session and synchronously flush memory:

```sh
opensquilla reset --key <session-key>
```

If reset reports a raw fallback, the session may have been reset while only a raw transcript backup was written. Inspect the reported fallback and memory status before assuming searchable memory is healthy.

`opensquilla init` is a compatibility initializer that interactively writes basic provider/env/config files. Prefer the setup/onboarding route in `../../setup-and-gateway/SKILL.md` for modern first-run setup.

Inspect sandbox posture:

```sh
opensquilla sandbox status --json
```

Change configured default posture:

```sh
opensquilla sandbox safe
opensquilla sandbox full
opensquilla sandbox reset
opensquilla gateway restart
```

`safe` uses the system sandbox and configured Safe policies. `full` disables runtime sandboxing and skips approval/sensitive-path gates. `reset` restores the default safe posture. For one-shot automation, prefer per-run `opensquilla agent --permissions ...` when the posture should not become the global default.

Uninstall safely:

```sh
opensquilla uninstall --dry-run
opensquilla uninstall --dry-run --json
opensquilla uninstall --yes --json
```

Data deletion is opt-in:

```sh
opensquilla uninstall --yes --purge-state --json
opensquilla uninstall --yes --purge-config --json
opensquilla uninstall --yes --purge-all --confirm-purge-all "delete everything" --json
```

Rules:

- Default uninstall removes the program/inventory items and keeps user data.
- `--purge-state` deletes runtime state such as sessions, scheduler state, memory, logs, and cache.
- `--purge-config` deletes config and secrets.
- `--purge-all` implies state and config deletion and requires the confirmation phrase, even with `--yes`.
- Non-interactive or `--json` surfaces refuse to act without `--yes`.
- Desktop-profile data deletion is routed to complete desktop cleanup instead of generic purge flags.
- Source installs surface manual source-checkout removal rather than silently deleting an arbitrary checkout.
