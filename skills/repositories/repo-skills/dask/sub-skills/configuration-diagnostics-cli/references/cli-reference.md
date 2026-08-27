# Dask CLI Reference

The installed console script is `dask`, implemented by Dask's Click-based CLI. Use it for low-risk environment inspection, config lookup, docs launching, and extension commands registered by packages through the `dask_cli` entry point group.

## Top-Level Commands

| Command | Purpose | Side effects |
| --- | --- | --- |
| `dask --help` | Show CLI command tree | None |
| `dask --version` | Print installed Dask version | None |
| `dask docs` | Open Dask documentation in a web browser | Opens a browser; avoid in noninteractive smoke checks |
| `dask info versions` | Print Dask and related package versions | None beyond imports |
| `dask config --help` | Show config subcommands | None |

## Config Commands

| Command | Use | Notes |
| --- | --- | --- |
| `dask config get KEY` | Print one config value | Exits nonzero and prints `Section not found: KEY` when missing |
| `dask config list` | Print the merged active config as YAML | May page output via Click |
| `dask config find KEY` | Show config files containing a key | Searches active config paths; if absent, prints all searched paths |
| `dask config set KEY VALUE [--file PATH]` | Persist a key/value to YAML | Writes a config file; use only when persistent mutation is intended |

`dask config set` interprets values before writing, so `True`, `123`, `None`, lists, and dict-like values may become typed YAML values. Without `--file`, it writes to the first existing config file containing the key, otherwise to the default Dask config file under the active `DASK_CONFIG` directory or user config directory.

## Safe CLI Smoke Checks

From the root of this `configuration-diagnostics-cli` sub-skill directory, use the bundled script for repeatable checks:

```bash
python scripts/dask_cli_smoke.py
```

Equivalent manual commands:

```bash
dask --help
dask config get temporary-directory
dask config list
dask info versions
```

Avoid `dask config set` in smoke checks unless you pass `--file` pointing to a temporary file that is safe to mutate.

## CLI Extension Entry Points

Dask discovers Python entry points in the `dask_cli` group at CLI startup. Each entry point should load to a `click.Command` or `click.Group`. Invalid or failing entry points emit warnings and are skipped. If an extension command name collides with an existing command, the existing command or group can be overwritten with a warning.

When debugging extension commands:

1. Confirm the package exposing the entry point is installed in the same environment as `dask`.
2. Run `dask --help` and inspect whether the command appears.
3. Import the entry point target manually if registration warns.
4. Verify the object is a Click command/group, not an arbitrary function.

## Browser And Noninteractive Environments

`dask docs` calls Python's `webbrowser.open("https://docs.dask.org")`. In CI, servers, SSH sessions, and headless containers, prefer printing the URL or using docs references instead of running the command.

## Distributed CLI Boundary

Core Dask's `dask` CLI does not provide `dask scheduler`, `dask worker`, SSH cluster, or Kubernetes cluster commands. Those are owned by the `distributed` package and deployment-specific packages. If a user asks about cluster daemons, route to deployment/distributed documentation after confirming `distributed` is installed.
