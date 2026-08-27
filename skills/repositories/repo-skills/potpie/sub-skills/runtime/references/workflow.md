# Runtime workflow reference

## Install and smoke checks

| Goal | Command | Notes |
| --- | --- | --- |
| Install published CLI | `uv tool install potpie` | Keeps the CLI isolated from the current project. |
| Install with pip | `python -m pip install potpie` | Use when `uv` is unavailable or an existing env is intentional. |
| Refresh from a live source checkout | `make cli-install` | Repo-local convenience path; not required for normal installed-package use. |
| Basic CLI smoke | `potpie --version && potpie --help` | Confirms the entry point and Typer app can render help. |
| Safe daemon check | `potpie daemon status` | Works when the daemon is stopped and reports detached readiness. |
| Broad bundled smoke | `../../scripts/potpie_smoke.sh` | Runs version/help checks and a daemon-status probe. |
| Public API import smoke | `python ../../scripts/typecheck_public_context_api.py` | Checks public context-core/context-engine API imports. |
| Agent-surface reference | `python ../../scripts/generate_agent_contract.py` | Emits installed-package graph/agent contract Markdown. |

## First-run setup

Use `potpie setup --dry-run` when you want to inspect the plan before Potpie mutates agent files, repo defaults, daemon state, or backend configuration. After review, run `potpie setup` with the intended repo and agent options.

Typical setup decisions:

- **Host mode:** default is `daemon`; local CLI commands expect a running daemon for many read/write/status paths.
- **Backend profile:** default is `falkordb_lite`; other profiles include `in_memory`, `embedded`, `neo4j`, `falkordb`, `postgres`, `chroma`, and `hosted` depending on installed dependencies and runtime configuration.
- **Repo binding:** setup can create the first pot and bind a repo, but detailed pot/source behavior belongs to `workspace-boundaries`.
- **Agent skills:** setup can install Potpie's bundled agent skills, but detailed install/update/status guidance belongs to `skills-management`.

## Runtime command ownership

| Command family | Use for | Route if the question is deeper |
| --- | --- | --- |
| `potpie status` | High-level daemon/runtime readiness | This sub-skill, then daemon troubleshooting. |
| `potpie doctor` | Structured diagnosis of runtime health | This sub-skill, then daemon/backend troubleshooting. |
| `potpie daemon status/start/stop/restart/logs` | Local daemon lifecycle | This sub-skill. |
| `potpie backend ...` | Backend profile inspection and switching | This sub-skill for readiness; graph sub-skills for read/write effects. |
| `potpie ui` | Opening the local graph/UI explorer | This sub-skill for startup and URL issues. |
| `potpie telemetry status/enable/disable` | Telemetry preference and Sentry reporting state | This sub-skill. |
| `potpie whoami` / `login` / `logout` | Potpie account auth | Basic account status here; provider details in `auth-integrations`. |

## Daemon-dependent command pattern

During inspection, `potpie daemon status` can succeed while `potpie status`, `potpie doctor`, `potpie backend list`, or `potpie skills status` report `unavailable`. This means the package and CLI are importable, but the daemon is not running. Diagnose daemon startup before reinstalling dependencies.

Useful order:

1. `potpie --help`
2. `potpie daemon status`
3. If stopped, `potpie daemon start` or rerun setup in the intended repo/session.
4. `potpie status` or `potpie doctor` after the daemon is up.
5. Only then inspect backend/skills/graph commands that require daemon RPC.

## Backend readiness notes

- The selected skill scope does not require a GPU. CPU or local daemon availability is enough for CLI/contract verification.
- `falkordb_lite` is the default backend profile and is suitable for local embedded-first usage when the package dependencies are installed.
- Backend switching should be deliberate. Treat `hosted`, `postgres`, `neo4j`, and `falkordb` as configuration choices that may require services, credentials, or ports outside the installed package.

## Telemetry notes

Potpie includes Sentry/telemetry controls. Use telemetry commands to inspect or change local preference before assuming reporting is active. Telemetry failures should not block graph correctness unless the task explicitly requires observability behavior.
