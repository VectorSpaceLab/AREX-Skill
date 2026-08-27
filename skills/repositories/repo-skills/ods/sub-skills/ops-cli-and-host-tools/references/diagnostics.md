# ODS diagnostics, host-agent, remote-provider, mDNS, and memory-shepherd reference

This reference covers the host-facing tools around the operator CLI. It is intentionally action-oriented: start with diagnostics, keep secrets redacted, and escalate to mutating repairs only when the user explicitly requests them.

## Doctor command

`ods doctor` delegates to the doctor script, writes a JSON report, then formats an operator summary unless `--json` is used.

Safe forms:

```bash
ods doctor --json --report <report.json>
ods doctor <report.json>
```

The report includes these major sections and signals:

- Runtime prerequisites: Docker CLI, Docker daemon, Docker Compose, Dashboard HTTP, Open WebUI HTTP, rootless Docker subordinate ID status, and managed/running container counts.
- Inference routing: configured LLM provider, model, endpoint URL, local/remote/cloud mode warnings, AMD/Lemonade runtime health, DGX Spark CUDA architecture support, and recovery hints.
- Voice readiness: Whisper STT cache status, configured STT model, TTS HTTP status, and suggested recovery actions.
- Extension diagnostics: each service's container state, health endpoint status, image/build indicators, and issues such as missing containers, exited containers, or failed health checks.
- Install evidence: latest install report/log when present, generated compose/config artifacts, and diagnoses for missing `.env`, zero managed containers, failed image pulls, missing PyYAML, or Docker Desktop file-sharing confusion.
- `autofix_hints`: deduplicated next steps. Treat hints as proposals; run repairs only after user approval.

Doctor is read-only diagnostic work, but it may call Docker/curl and write the requested report path. It does not replace focused tests for a code change.

## Support bundle

`ods/scripts/ods-support-bundle.sh` creates a redacted archive for support and is safe to use as an output-producing diagnostic when the user agrees to collect host information.

Safe first forms:

```bash
scripts/ods-support-bundle.sh --help
scripts/ods-support-bundle.sh --output <dir> --no-logs --json
```

Important behavior:

- Raw `.env` is never included. The bundle writes `config/env.redacted` and redacts schema-marked secret, user, email, token, password, key, bearer, and authorization values.
- The bundle can include doctor output, extension audit output, compose resolution/validation, port listings, selected logs unless `--no-logs` is used, hashes/metadata, `manifest.json`, and `manifest/evidence.json`.
- Docker-dependent collection can be skipped in constrained environments; expect explicit skipped messages rather than treating every missing Docker signal as an ODS defect.
- Inspect redacted bundle contents before sharing publicly if the operator has custom config keys.

## Host agent

The host-agent is `ods/bin/ods-host-agent.py`, managed by `ods agent status|start|stop|restart|logs` and platform service units. It lets containerized dashboard services ask the host to perform operations Docker Desktop or the browser cannot do directly.

Core runtime facts:

- Default port is `7710`, overridden by `ODS_AGENT_PORT` or `--port`.
- Auth uses `Authorization: Bearer <key>`, with `ODS_AGENT_KEY` preferred and `DASHBOARD_API_KEY` as legacy fallback. Every non-health endpoint should be treated as authenticated.
- Bind address comes from `ODS_AGENT_BIND` when set. Defaults are platform-safe: macOS/Windows bind loopback; Linux prefers the ODS Docker network gateway, then Docker bridge, then loopback. Binding `0.0.0.0` is explicitly logged and still requires bearer auth.
- `ods agent start` uses launchd on macOS, systemd on Linux when available, or a background `python3 ods-host-agent.py --pid-file ...` fallback. `logs` tails the host-agent log file and may block.

Representative GET endpoints:

| Endpoint | Purpose | Notes |
| --- | --- | --- |
| `/health` | unauthenticated health/version | Useful for liveness only. |
| `/v1/gpu/metrics` | host GPU counters | Authenticated; Windows/macOS/Linux support depends on host tools. |
| `/v1/llm/status` | local inference status | Authenticated. |
| `/v1/service/health`, `/v1/service/stats` | service summaries | Authenticated. |
| `/v1/model/list`, `/v1/model/status` | model catalog/state | Authenticated. |
| `/v1/network/status`, `/v1/network/wifi-scan` | host network information | Authenticated. |
| `/v1/tailscale/status`, `/v1/ap-mode/status` | remote/local access status | Authenticated. |
| `/v1/update/status` | update status | Authenticated. |
| `/v1/remote-provider/ssh-supervisor` | SSH route supervisor status | Authenticated. |
| `/v1/host/port?host=127.0.0.1&port=N` | loopback port probe | Restricted to loopback hosts to avoid becoming a network scanner. |

Representative POST endpoints include extension lifecycle (`/v1/extension/start`, `/stop`, `/install`, `/activate`, `/deactivate`, `/hooks`), service logs/restart, model download/cancel/activate/delete, compose cache invalidation, env update, update check/backup/start, Wi-Fi connect/forget, Windows Lemonade ensure, and remote-provider plan/apply/proof. These endpoints can mutate host state; use the CLI or dashboard workflow rather than ad-hoc curl unless debugging the host-agent itself.

## Remote provider helpers

`ods remote-provider` talks to the local Dashboard API, which in turn coordinates host-agent and egress components. It supports direct OpenAI-compatible routes and SSH-tunneled routes.

Safe/non-config-mutating forms:

```bash
ods remote-provider status --json
ods remote-provider plan configure --base-url URL --model MODEL --api-key-stdin
ods remote-provider test --json
ods remote-provider test --base-url URL --model MODEL --api-key-stdin --json
ods remote-provider peer-models list --json
ods remote-provider peer-models download-status --json
```

Mutating forms:

```bash
ods remote-provider configure --base-url URL --model MODEL --api-key-stdin
ods remote-provider disable
ods remote-provider remove
ods remote-provider peer-models download MODEL
ods remote-provider peer-models load MODEL
ods remote-provider peer-models cancel-download
ods remote-provider peer-models delete MODEL --yes
```

Secret-handling invariants:

- Raw `--api-key`, raw `--ssh-private-key`, and raw `--ssh-known-hosts` arguments are intentionally rejected so secrets do not appear in process listings or shell history.
- Provider API keys may come from stdin, a local file, or a named process environment variable. SSH private keys and known-hosts content may come from files or named environment variables.
- Dashboard API bearer tokens are streamed to curl through standard input headers rather than argv.
- Request/response payloads use private temporary files with owner-only permissions.
- Peer credentials remain in ODS secret custody; the CLI must not accept peer tokens as arguments.

Route lifecycle semantics:

- `plan` validates and prints redacted JSON without mutating route state.
- `configure` persists route state and secrets, then applies lifecycle effects. Failures should report rollback status.
- `test` without provider options probes the configured route; with provider options it performs a one-shot probe without writing provider state.
- `disable` keeps stored secrets while disabling the route; `remove` deletes route state and stored secrets.
- Peer model `delete` requires `--yes`; `load` uses a long timeout because remote model activation can take many minutes.

## mDNS announcer

`ods/bin/ods-mdns.py` publishes LAN-discoverable names for ODS when supported.

Key behavior:

- Linux path imports `zeroconf` and requires an `.env` file under `ODS_INSTALL_DIR` (default `/opt/ods`). Missing `zeroconf` exits with a package-install message.
- macOS exits successfully because mDNSResponder already announces `hostname.local`; Windows exits successfully because support varies.
- `ODS_DEVICE_NAME` must be hostname-safe; invalid names fall back to `ods`.
- Direct-port SRV records are only published when `BIND_ADDRESS` is LAN-reachable. Default loopback binding skips direct-port records to avoid advertising unreachable ports.
- Proxy-routed hostnames are published as A records via service registration. Required subdomains are `root`, `chat`, `dashboard`, `auth`, `api`, `hermes`, and `talk`.
- Relevant ports are read from `.env`: `ODS_PROXY_PORT`, `DASHBOARD_PORT`, `WEBUI_PORT`, `DASHBOARD_API_PORT`, and `HERMES_PORT`.
- The announcer polls for env changes and re-registers services when name, bind, IP, or ports change.

Use the static mDNS subdomain contract when adding or removing public proxy hosts; public hostnames must also agree with proxy routing and dashboard magic-link targets.

## Memory-shepherd

`ods/memory-shepherd/` is a host utility for long-running LLM agents, not part of the main ODS service stack. It periodically archives scratch notes and resets `MEMORY.md` files to known-good baselines.

Safety classification:

- `memory-shepherd/install.sh --dry-run` is the safe first form.
- `memory-shepherd.sh <agent|all>` mutates agent memory files by archiving scratch content and replacing the memory body with the configured baseline.
- `install.sh` and `uninstall.sh` mutate systemd user/system units depending on prefix and host permissions.

Operational facts:

- Config search order is `MEMORY_SHEPHERD_CONF`, `./memory-shepherd.conf` beside the script, then `/etc/memory-shepherd/memory-shepherd.conf`.
- Each agent needs a baseline file and either a local `memory_file` or remote `remote_host` plus `remote_memory` target.
- The separator line divides protected baseline memory from scratch notes. Missing separators trigger a full backup before reset.
- Oversized memory files trigger forced reset when over `max_memory_size`.
- Remote mode uses SSH/SCP; treat remote paths and credentials as private operator state.

Do not use memory-shepherd to modify a user's agent memory unless they explicitly ask for that reset/installation behavior.
