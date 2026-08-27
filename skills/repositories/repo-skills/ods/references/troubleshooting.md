# ODS Cross-Cutting Troubleshooting

Use this root troubleshooting map when symptoms span installer, model/backend, compose services, dashboard, CLI, and validation lanes. For workflow-specific details, switch to the nearest sub-skill troubleshooting file.

## Triage order

1. Identify the surface: install, model/backend, service/extension, dashboard/API, CLI/host tool, or validation/CI.
2. Prefer read-only evidence: command help, logs, generated config diffs with secrets masked, static layout checks, manifest summaries, route lists, and focused tests.
3. Only run host-mutating commands when the user requested an installed-system action and understands the side effects.
4. If the symptom involves secrets or auth, avoid printing raw `.env`, API keys, Bearer tokens, OAuth codes, magic-link tokens, or support-bundle internals.
5. Use focused validation before broad gates. Full model downloads, GPU smoke lanes, fleet tests, and release gates are expensive and may mutate host/container state.

## Symptom routing

| Symptom | Likely owner | First safe checks |
| --- | --- | --- |
| Installer fails before Docker or prerequisites | `installers-and-platforms` | Review preflight/platform workflow; run syntax/contract preflight tests or dry-run where safe. |
| Installer finishes but generated `.env`/service config is wrong | `installers-and-platforms` plus affected owner | Compare generated config writers across Linux/macOS/Windows/update/host-agent paths; do not patch one writer only. |
| GPU tier, model, context, or backend overlay is wrong | `hardware-and-models` | Inspect tier maps, backend contracts, model library, context policy, and focused tier/model tests. |
| Service missing, unhealthy, or wrongly exposed | `services-and-extensions` | Inspect manifest category/id/port/health, compose files, resolver behavior, and service registry output. |
| Dashboard UI cannot reach API or shows 401/502 | `dashboard-and-api` | Check dashboard/api ports, Bearer auth injection, host-agent DNS/key config, and baked container vs native dev workflow. |
| `ods` CLI status/list/logs/config output is wrong | `ops-cli-and-host-tools` | Classify command as read-only or mutating, inspect dispatch, aliases, env loading, compose flags, and focused CLI tests. |
| Docker or rootless permissions fail during lifecycle | `ops-cli-and-host-tools` and `installers-and-platforms` | Check Docker access, rootless ownership repair guidance, bind-mount ownership, and non-destructive doctor output. |
| Test or CI lane fails | `testing-and-release` | Map changed paths to focused lanes; reproduce the exact CI command locally only if dependencies and safety class allow it. |

## High-risk operations

Treat these as high-risk unless the user explicitly asks for them:

- Running real installers, updates, uninstalls, backup/restore, or repair flows.
- Starting/stopping/restarting Docker services on a user host.
- Downloading full GGUF models, Docker images, or external datasets.
- Running platform smoke/fleet tests that require Docker, GPU, OS-specific services, or network.
- Editing secrets, `.env`, OAuth provider settings, magic-link state, or support bundle contents.
- Deleting extension data, model files, volumes, or runtime directories.

## Common root causes by area

### Installer/generated config

- A value is written in one platform writer but not the others.
- A bootstrap-upgrade or host-agent writer overwrites installer output later.
- Docker Desktop/WSL2/macOS native bridge behavior differs from Linux Docker.
- Preflight passes on one distro because a tool exists but fails later because a Python module such as PyYAML is missing.
- Ports are already occupied or bind-address defaults changed.

### Hardware/model/backend

- Tier maps and model catalog drift, causing an unsupported model/context pairing.
- Backend contract JSON permits a route not supported by compose overlays.
- CPU import or static tests are mistaken for GPU runtime validation.
- Bootstrap model and full model context policies are confused.
- External Lemonade/Ollama/LM Studio reuse is treated as ambient discovery instead of explicit topology.

### Services/extensions

- User extension shadows a core service id or alias.
- Compose fragment binds public interfaces unexpectedly or requests dangerous capabilities/security options.
- GPU overlay exists for one vendor but not the selected backend.
- Library install/update/rollback receipt state is confused with runtime service data.
- Core services without extension compose fragments are treated like optional extension services.

### Dashboard/API/UI

- Host edits under dashboard-api do not affect the running container because the image bakes `/app` at build time.
- Only dashboard-api is stopped during local dev, leaving dashboard nginx proxying to a missing container and returning 502.
- Bearer auth is missing when bypassing production nginx.
- Host-agent calls fail because native uvicorn cannot resolve Docker-only hostnames.
- Frontend dev proxy and production nginx injection have different auth behavior.

### CLI/host tools

- A command family includes both read-only and mutating forms; choose subcommands conservatively.
- Compose flags are stale after mode/model/extension changes.
- Rootless Docker bind mounts are owned by the wrong UID/GID.
- Support bundle or doctor output must redact secrets before sharing.
- Remote-provider/host-agent operations require two different keys or network assumptions.

### Testing/release

- Full `make gate` is run when a focused contract test would diagnose faster.
- A skipped platform lane is misreported as a release-grade pass.
- Secret-scan fixtures or generated examples contain realistic token shapes.
- CI workflow failure is triaged without reproducing its exact path and environment assumptions.
- Release validation claims are made without User Green or the documented release-grade evidence.

## Escalation checklist

Before making a broad change or running an expensive lane, record:

- The user-visible symptom and the smallest affected capability.
- The sub-skill owner and cross-skill dependencies.
- Read-only evidence already gathered.
- Whether secrets, Docker, GPU, network, or platform-specific services are involved.
- The exact focused check that will prove or disprove the suspected cause.
- Any command that will mutate host state, and why the user authorized it.
