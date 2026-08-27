# CLI, Backend, Scanner, and GUI Reference

Use this reference for PyRIT command surfaces. The console-script help checks were verified for `pyrit_scan`, `pyrit_shell`, and `pyrit_backend`.

## Command split

| Command | Role | Safe check |
|---|---|---|
| `pyrit_backend` | Starts the FastAPI backend service used by scanner, shell, and GUI. | `pyrit_backend --help` |
| `pyrit_scan` | CLI scanner client for listing registered objects, starting/stopping backend, running scenarios, and viewing results. | `pyrit_scan --help` |
| `pyrit_shell` | Interactive REST client shell for the backend. | `pyrit_shell --help` |

`pyrit_scan` and `pyrit_shell` are clients. Most discovery/run commands require a reachable backend unless the command is help-only or stopping a local backend.

## Backend service: `pyrit_backend`

Common flags:

- `--host HOST` and `--port PORT` bind the API server. Prefer loopback for ad hoc work.
- `--config-file CONFIG_FILE` loads database, initializers, and environment files.
- `--log-level LEVEL` controls logging.
- `--reload` watches code for development; avoid for stable runs unless explicitly needed.

Do not bind to a public interface without an approved deployment/security plan.

## Scanner client: `pyrit_scan`

Important flag groups:

- Server lifecycle: `--server-url`, `--start-server`, `--stop-server`, `--startup-timeout`, `--config-file`, `--log-level`, `--request-timeout`.
- Discovery: `--list-scenarios`, `--list-initializers`, `--list-targets`, `--list-converters`, `--list-datasets`.
- Run selection: positional `scenario_name`, `--target`, `--initializers`, `--techniques`.
- Dataset/result controls: `--dataset-names`, `--max-dataset-size`, `--dataset-filters KEY=VALUE`, `--memory-labels JSON`, `--scenario-results`, `--view {overview,attacks}`, `--attack-result-ids`, `--limit`.

## Shell: `pyrit_shell`

Use `pyrit_shell` for interactive exploration against a backend. It accepts `--server-url`, `--start-server`, `--config-file`, `--log-level`, and `--no-animation`. Keep shell commands distinct from `pyrit_scan` flags.

## Backend REST and GUI

The Python backend exposes PyRIT scenarios, targets, converters, datasets, initializers, attacks/results, health/version, and media routes. The CoPyRIT GUI is a browser client over that backend. This skill covers operating the Python backend and GUI at a high level; it does not cover frontend TypeScript development.

## Docker/container caveats

Container docs are operational context, not bundled scripts. Before container operations, ask for permission because builds and runs can download images, bind ports, mount volumes, and persist data. Keep secrets outside image layers.

Run `scripts/pyrit_cli_smoke.py --json` for help-only command availability checks; it does not start a server or run a scan.
