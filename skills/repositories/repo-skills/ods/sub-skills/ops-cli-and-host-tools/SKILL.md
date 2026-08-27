---
name: ops-cli-and-host-tools
description: "Operate ODS operator CLI, lifecycle, diagnostics, backup/restore,
  host-agent, remote-provider, mDNS, and memory-shepherd surfaces safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ODS ops CLI and host tools sub-skill

Use this sub-skill when an ODS task touches the `ods` operator CLI, lifecycle commands, logs, configuration commands, mode/model command syntax, extension enable/disable/audit commands, backup/restore/update/uninstall helpers, doctor/support-bundle diagnostics, host-agent, mDNS, remote-provider helpers, or memory-shepherd.

Do not use this sub-skill for installer phase internals; route those to `installers-and-platforms`. Do not use it for service manifest schema or compose-extension design; route those to `services-and-extensions`. Do not use it for GPU tier/model catalog internals; route those to `hardware-and-models`. Do not use it for dashboard route/UI implementation except where a host-agent or remote-provider CLI boundary is the task. Route release-lane selection to `testing-and-release` after identifying the touched ops surface.

## Operating workflow

1. Read [`references/cli-operations.md`](references/cli-operations.md) before changing or advising on `ods-cli`, `ods-backup.sh`, `ods-restore.sh`, `ods-update.sh`, or `ods-uninstall.sh`. It marks command families as `help-only`, `read-only`, or `mutating` and records focused validation hints.
2. Read [`references/diagnostics.md`](references/diagnostics.md) for `ods doctor`, support bundles, host-agent endpoints, mDNS, remote-provider, and memory-shepherd behavior.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when symptoms involve Docker access, stale compose flags, secret masking, rootless ownership, host-agent auth, remote-provider lifecycle, backup/restore, mDNS, update rollback, or memory-shepherd resets.
4. To inspect a local ODS CLI dispatch surface without running the CLI, use the bundled read-only helper:

   ```bash
   python3 scripts/check_cli_surface.py --ods-cli <ODS_TREE>/ods-cli
   ```

   Add `--json` for machine-readable output and `--strict` when a new dispatch command should fail review unless it is classified.

## Safety rules

- Prefer `--help`, `--dry-run`, `--json`, `list`, `status`, `plan`, and static parsing before any command that changes files, containers, model state, remote peer state, or services.
- Treat lifecycle commands (`start`, `stop`, `restart`, `update`, `rollback`, `restore`, `uninstall`, `purge`, `repair`, `agent start|stop|restart`) as host-mutating. Do not run them without explicit user intent and a suitable installed ODS target.
- Treat `backup` as write-producing and `restore`/`rollback`/`purge`/`uninstall` as potentially destructive even when they include prompts.
- Never put API keys, bearer tokens, remote-provider secrets, SSH private keys, or raw `.env` contents in public notes. Use streamed secret inputs and redacted support-bundle outputs.
- When editing CLI behavior, keep Bash 4+, `set -euo pipefail`, service aliases, compose flag regeneration, `.env` masking, and remote-provider secret handling intact.

## Common task routing

- CLI command syntax, top-level dispatch, help text, or command risk classification: use this sub-skill, then cross-check with `testing-and-release` for the focused CLI/contract lane.
- Extension enable/disable/audit operator behavior: use this sub-skill for `ods enable|disable|audit`; cross-link `services-and-extensions` for manifest and compose semantics.
- Model/mode operator commands: use this sub-skill for `ods mode`, `ods model`, and remote-provider command syntax; use `hardware-and-models` for tier maps, catalog facts, and runtime backend constraints.
- Host-agent API/service management, mDNS, remote provider, or memory-shepherd host helpers: use this sub-skill first, then route dashboard-facing API/UI details to `dashboard-and-api` if the task crosses into those services.

## Source provenance

This runtime guidance distills evidence from relative ODS source paths such as `ods/ods-cli`, `ods/ods-backup.sh`, `ods/ods-restore.sh`, `ods/ods-update.sh`, `ods/ods-uninstall.sh`, `ods/scripts/ods-doctor.sh`, `ods/scripts/ods-support-bundle.sh`, `ods/bin/ods-host-agent.py`, `ods/bin/ods-mdns.py`, `ods/bin/remote_provider/`, `ods/memory-shepherd/`, `ods/docs/ODS_CLI_DECOMPOSITION.md`, and CLI/doctor/backup/remote-provider/mDNS tests. Future usage should rely on this bundled guidance, the bundled read-only helper, and public ODS commands/tests.
