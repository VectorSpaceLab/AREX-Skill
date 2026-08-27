# ODS ops CLI and host tools troubleshooting

Start with read-only diagnostics. Only run repair, lifecycle, restore, purge, uninstall, or peer-model mutations after explicit user intent.

## Docker or compose commands fail

Symptoms:

- `ods status` cannot talk to Docker or Compose.
- Lifecycle commands report no compose files, wrong services, missing containers, or stale `docker-compose.cloud.yml`/backend overlays.
- Docker Desktop reports file-sharing or daemon availability errors.

Triage:

1. Run `ods doctor --json --report <report.json>` and inspect Docker CLI, daemon, compose, managed container counts, and install diagnoses.
2. Use `ods list --json` to confirm expected service IDs and enabled/disabled state.
3. Check whether `.compose-flags` is stale. Service toggles, mode changes, backend/tier changes, and extension edits should regenerate compose flags.
4. Avoid raw `docker compose` from a source checkout unless the exact compose flags are known. Prefer `ods start|restart|status` for installed systems.
5. For rootless Docker bind-mount ownership symptoms, use doctor hints first; `ods repair rootless-ownership` is mutating and should be user-approved.

## CLI exits under `set -u` or Bash incompatibility

Symptoms:

- `unbound variable` in help/version or optional code paths.
- macOS system Bash 3.2 errors on associative arrays.
- Pipefail-related aborts in pipelines.

Triage:

1. Confirm the CLI keeps `#!/usr/bin/env bash` and `set -euo pipefail`.
2. Use Bash 4+ for `ods-cli`; macOS users may need a Homebrew Bash path.
3. Prefer `${VAR:-}` or `${VAR:-default}` for optional env reads.
4. Avoid `| head -1` in pipelines under pipefail; use `sed -n '1p'` or another non-SIGPIPE pattern.
5. Run the static CLI contract and flag-hygiene tests after edits.

## Configuration or secret masking looks wrong

Symptoms:

- `ods config show` exposes a value that should be redacted.
- Support bundle includes unexpected env keys.
- Mode/model/config changes do not take effect after restart.

Triage:

1. Use `ods config show`, not raw `.env`, when asking users for config snippets.
2. Keep `.env.schema.json` secret markers aligned with CLI config masking and support-bundle redaction.
3. `ods config edit` only edits `.env`; tell the user to restart affected services afterwards.
4. `ods config validate` runs env validation plus manifest validation when the installed scripts exist.
5. For generated config drift, route to the owning installer/config sub-skill and select focused generated-config tests.

## Extension enable/disable/audit problems

Symptoms:

- `ods enable <service>` refuses a backend, asks about missing dependencies, or cannot find a service alias.
- `ods disable <service>` warns about dependents.
- `ods purge <service>` refuses because the service is still enabled or a container is running.

Triage:

1. Use `ods list --json` and `ods audit --json <service>` before changing state.
2. For manifest IDs, dependencies, ports, categories, and compose security, route to `services-and-extensions`.
3. Backend compatibility warnings depend on current `GPU_BACKEND` and manifest metadata; route GPU support facts to `hardware-and-models`.
4. Never suggest `purge` as a generic fix. It permanently deletes service data after typed confirmation and should follow disable/stop verification.

## Backup, restore, update, or rollback problems

Symptoms:

- Backup verification fails.
- Restore prompts are confusing or restore was run against the wrong directory.
- Update fails after pulling images or services do not become healthy.
- Rollback point is missing or restore does not recover service health.

Triage:

1. For backups, run `ods backup --list` or `ods-backup.sh --list`, then `ods backup verify <id>` before restore.
2. Use `ods restore --dry-run <id>` before a real restore. Real restore should keep checksum verification enabled unless the user explicitly accepts the risk.
3. `ods update --dry-run` previews changes. Real update creates a pre-update snapshot when helpers exist, then pulls/recreates services and verifies running containers.
4. If update fails, inspect the update output and doctor report before `ods rollback`. Rollback is mutating and restores older config/service state.
5. If uninstall is requested, prefer `ods-uninstall.sh --help` first. `--force` skips prompts; `--keep-models` and `--keep-data` preserve only selected data while still removing the installation.

## Host-agent is unreachable or unauthorized

Symptoms:

- `ods agent status` reports not responding.
- `ods model swap` fails with host-agent unreachable or missing API key.
- Dashboard actions that require host access fail.
- Direct curl calls return `401` or `403`.

Triage:

1. Run `ods agent status` and, if needed, `ods agent logs` for existing logs. `logs` follows the file and may block.
2. Confirm `.env` contains `ODS_AGENT_KEY` or legacy `DASHBOARD_API_KEY`, and that the key has no newline characters.
3. Confirm `ODS_AGENT_PORT` and `ODS_AGENT_BIND`. Defaults are loopback on macOS/Windows and Docker-network-gateway-oriented on Linux.
4. If service managers are involved, check launchd on macOS and systemd on Linux. Fallback background mode uses a PID file and `python3`.
5. `ods agent restart` is mutating; use it only after the user agrees.
6. Do not expose bearer tokens in process arguments, logs, or reports.

## Remote-provider lifecycle or peer model issues

Symptoms:

- `remote-provider configure` rejects options or secrets.
- Direct route tests fail while plan succeeds.
- SSH transport fails to start or proof recording is absent.
- Peer model delete/download/load hangs or fails.

Triage:

1. Run `ods remote-provider status --json` and `ods remote-provider plan ...` before `configure`.
2. Do not pass raw secrets. Use `--api-key-stdin`, `--api-key-file`, `--api-key-env`, and the SSH file/env options.
3. For direct transport, remove SSH options. For SSH transport, provide host, user, port, inference host, inference port, private key, and known-hosts source.
4. `test` with provider options is a one-shot probe; `configure` persists route state and secrets. Keep those separate when debugging.
5. Peer model `delete` must include `--yes`. `load` can legitimately take a long time; avoid retry storms.
6. Remote-provider egress/service internals route to diagnostics here and dashboard/API implementation only if changing API handlers.

## mDNS names do not resolve

Symptoms:

- `ods.local`, `chat.<device>.local`, `dashboard.<device>.local`, `auth.<device>.local`, `api.<device>.local`, `hermes.<device>.local`, or `talk.<device>.local` does not resolve on the LAN.
- Phones land on an unresolvable magic-link or talk URL.

Triage:

1. Confirm platform expectations: Linux uses the Python zeroconf announcer; macOS exits as a no-op because mDNSResponder handles hostnames; Windows support varies.
2. Check that the `.env` file exists for the announcer and `ODS_DEVICE_NAME` is hostname-safe.
3. If direct service ports are expected, `BIND_ADDRESS` must not be loopback-only. Default ODS posture advertises proxy-routed hostnames, not direct ports.
4. Confirm the proxy route exists for any new public subdomain. Required subdomains must stay in sync across mDNS, proxy config, and dashboard magic-link/talk targets.
5. Use the static mDNS subdomain contract when modifying the announcer.

## Memory-shepherd reset surprises

Symptoms:

- Agent `MEMORY.md` content appears reset.
- Scratch notes are archived but not visible in current memory.
- Timer/service installation affects more agents than intended.

Triage:

1. Inspect the shepherd config path chosen by `MEMORY_SHEPHERD_CONF`, local config, or `/etc/memory-shepherd/...`.
2. Confirm the target agent section and baseline path before running `memory-shepherd.sh <agent>`.
3. Use `install.sh --dry-run` before installing timers.
4. Missing separators cause full-file backups before reset; check the configured archive directory.
5. Remote agents use SSH/SCP. Treat remote memory paths and credentials as private and do not record them in public skill output.
