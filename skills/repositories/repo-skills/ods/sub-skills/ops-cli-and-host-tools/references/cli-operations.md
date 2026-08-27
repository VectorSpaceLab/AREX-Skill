# ODS CLI operations reference

The installed operator command is `ods`, backed by the Bash entrypoint `ods-cli`. It assumes Bash 4+, uses `set -euo pipefail`, resolves its installation directory from `ODS_HOME` or the installed script location, reads `.env` through safe loaders, resolves service aliases from the service registry, and runs Docker Compose through generated or dynamically resolved compose flags.

Use this file to decide whether a command can be inspected safely or requires explicit user intent.

## Top-level dispatch risk map

`help-only` means no ODS installation state is required and the command only prints usage/version. `read-only` means it should not intentionally mutate ODS configuration or service state, though it may read Docker status, contact local services, tail logs, or write a requested report/bundle. `mutating` means the command can change files, containers, model state, presets, remote peer state, system services, or installed data.

| Command family | Category | Read-only/help-only forms | Mutating or risky forms | Notes |
| --- | --- | --- | --- | --- |
| `help`, `--help`, `version`, `--version` | help-only | all forms | none | Minimal-env help/version are tested so they should not trip `set -u`. |
| `status`, `status-json`, `list` | read-only | `ods status [--json]`, `ods status-json`, `ods list [--json]` | none | Reads compose state, registry, health endpoints, and service ports. |
| `logs` | read-only | `ods logs <service> [lines]` | none | Tails Docker logs; may block because it follows logs. |
| `doctor` | read-only diagnostic | `ods doctor [--json] [--report PATH]` | writing a report path is output-only | Delegates to the doctor script and formats the JSON report. |
| `audit` | read-only | `ods audit [extensions] [--json|--strict] [service]` | none | Delegates extension audit; manifest semantics belong to `services-and-extensions`. |
| `config` | mixed, treat as mutating unless subcommand is known | `ods config show`, `ods config validate` | `ods config edit` | `show` masks schema-marked secret keys. `validate` runs env and manifest validation. |
| `chat`, `benchmark` | read-only service calls | default forms | none | Do not change config, but consume local inference resources and require running services. |
| `gpu` | mixed, treat as mutating unless subcommand is known | `status`, `topology`, `assignment`, `validate`, `reassign --dry-run` | `reassign`, `reassign --auto`, `reassign --manual` | GPU internals route to `hardware-and-models`; CLI syntax and risk live here. |
| `mode` | mixed, treat as mutating unless no mode is supplied | `ods mode` | `ods mode local|cloud|hybrid` | Mutates `.env`, may enable LiteLLM, then requires restart. |
| `model` | mixed, treat as mutating unless subcommand is known | `current`, `list` | `swap <tier>` | `swap` uses the host-agent model activation endpoint instead of direct model env writes. |
| `remote-provider` | mixed, treat as mutating unless subcommand is known | `status`, `plan`, configured or one-shot `test`, `peer-models list`, `peer-models download-status` | `configure`, `disable`, `remove`, `peer-models download|load|cancel-download|delete` | Raw secrets are not accepted as argv; peer model deletion requires `--yes`. |
| `stt` | mixed, treat as mutating unless subcommand is known | `current`, `status` | `download [MODEL]` | Download hits Whisper model API and populates cache. |
| `enable`, `disable` | mutating | none except usage errors | all normal forms | Toggle extension compose files, update compose flags, and may stop services. |
| `purge` | mutating/destructive | none | all normal forms | Permanently deletes disabled service data after typed confirmation. |
| `preset` | mixed, treat as mutating unless subcommand is known | `list`, `diff` | `save`, `load`, `delete`, `export`, `import` | `load` overwrites `.env` and extension state after confirmation. |
| `template` | mixed, treat as mutating unless subcommand is known | `list`, `preview` | `apply` | `apply` enables services from template definitions. |
| `start`, `stop`, `restart` | mutating lifecycle | none | all normal forms | Start/stop/recreate containers; `start|restart --rebuild-images` also rebuilds local images. |
| `shell` | mutating/interactive | none | all normal forms | Opens an interactive shell inside a service container. |
| `repair` / `fix` | mutating repair | none | `voice`, `hermes-workers`, `rootless-ownership` | Starts services, prunes processes, or fixes bind-mount ownership. |
| `agent` | mixed, treat as mutating unless subcommand is known | `status`, `logs` | `start`, `stop`, `restart` | Manages the host-agent via launchd, systemd, or a background Python fallback. |
| `backup` | mixed, write-producing by default | `verify <id>`, `--list` | default create, `--delete`, compressed output | Creates backup artifacts under the selected backup root and enforces checksums. |
| `restore` | mixed/destructive unless dry-run/list | `--list`, `--dry-run BACKUP_ID` | restore with or without `--force`, `--stop-containers`, `--skip-verify` | Requires backup-id confirmation unless forced. Avoid `--skip-verify` unless the user accepts integrity risk. |
| `update` | mixed, mutating by default | `--dry-run` | default update, `--force`, `--rebuild-images` | Takes a pre-update snapshot when helpers exist, pulls/recreates containers, verifies, and restarts the host-agent. |
| `rollback` | mutating/destructive | none | all normal forms | Restores pre-update config and restarts services after confirmation. |

## Backup, restore, update, and uninstall helpers

The top-level CLI delegates some flows to standalone scripts. These scripts are valid public commands for an installed/source ODS tree, but future agents should still prefer help/list/dry-run forms before mutation.

| Helper | Safe first command | Mutating forms | Important behavior |
| --- | --- | --- | --- |
| `ods-backup.sh` | `ods-backup.sh --help`, `ods-backup.sh --list`, `ods-backup.sh verify <id>` | default backup, `--delete <id>` | Supports `--output`, `--type user-data|config|full`, `--compress`, descriptions, checksum generation/verification, retention cleanup, and backup-root override through `ODS_DIR`/options. |
| `ods-restore.sh` | `ods-restore.sh --help`, `--list`, `--dry-run <id>` | restore with optional `--force`, `--stop-containers`, `--data-only`, `--config-only` | Validates checksums unless `--skip-verify` is requested; asks for backup-id confirmation unless forced. |
| `ods-update.sh` | `ods-update.sh status`, `check`, `changelog`, `health` | `backup`, `update`, `rollback` | Maintains rollback snapshots, resolves compose flags, pulls source updates, runs migrations, restarts services, and rolls back on health failure. |
| `ods-uninstall.sh` | `ods-uninstall.sh --help` | uninstall, even with `--keep-models` or `--keep-data` | Stops/removes ODS containers, volumes, systemd/launchd agents, symlinks, install directory, and backup directory. Use only with explicit user confirmation; `--force` skips prompts. |

## Operator workflows

### Inspecting a CLI change

1. Identify whether the change touches dispatch/help, risk classification, env parsing, compose flag resolution, service aliases, remote-provider secret handling, or lifecycle operations.
2. Run a static parse with the bundled helper:

   ```bash
   python3 scripts/check_cli_surface.py --ods-cli <ODS_TREE>/ods-cli --strict
   ```

3. Prefer focused native checks over lifecycle commands. Relevant public tests include static CLI contracts, CLI flag hygiene, backup/restore CLI delegation, backup integrity, restore safety UX, remote-provider CLI contracts, doctor tests, support-bundle tests, and mode/model/update contracts.
4. If changing model, mode, extension, or lifecycle behavior, cross-route to the owning sub-skill for product facts and to `testing-and-release` for lane selection.

### Safe operator triage order

1. `ods help` or command-specific help.
2. `ods status --json` and `ods list --json` for machine-readable state.
3. `ods doctor --json --report <path>` for diagnostics; inspect `autofix_hints` before repair.
4. `ods logs <service> [lines]` only after resolving the service alias.
5. `ods config show` to inspect masked configuration; avoid copying raw `.env`.
6. `ods update --dry-run`, `ods restore --dry-run <id>`, `ods remote-provider plan ...`, or `ods template preview <id>` before applying a mutating operation.

### Configuration and compose behavior

- `ODS_HOME` overrides the install directory used by `ods-cli`; installed deployments typically execute from the ODS install tree.
- `.env` is the primary runtime config. CLI helpers update it with safe key replacement helpers and avoid exposing schema-marked secrets in `config show`.
- `.compose-flags` is regenerated or dynamically resolved when service, mode, tier, or backend state changes. Stale compose flags are a common source of wrong-stack operations.
- Service aliases are resolved through the registry, so commands such as `logs llm`, `restart stt`, or extension aliases should resolve to canonical service IDs before compose calls.
- Enabling `ods-proxy` or starting Open WebUI while proxy is enabled enforces `WEBUI_AUTH=true` before exposing network access.

## Focused validation hints

Use the smallest test that covers the changed command family:

- Top-level dispatch/help/Bash hygiene: CLI static contract and BATS flag tests.
- Backup/restore delegation or safety prompts: backup/restore CLI, backup integrity, restore safety UX.
- Doctor/support bundle: doctor contract/symptom tests and support-bundle redaction test.
- Remote-provider command syntax or secret handling: remote-provider CLI and egress policy/service contracts.
- Mode/model/update: mode switch status, generated config contracts, model activation, update verification/rollback contracts.
- mDNS: static mDNS subdomain contract.
- Host-agent service management: host-agent platform tests for Linux/macOS/desktop-agent behavior.
