# Repo Provenance

This repo skill was generated from a local Kedro checkout. It records source state and evidence paths so future agents can decide whether the skill should be refreshed.

## Source Snapshot

| Field | Value |
| --- | --- |
| repository | Kedro |
| package distribution | `kedro` |
| import package | `kedro` |
| package version inspected | `1.4.0` |
| Python requirement | `>=3.10` |
| git commit | `e69b22eb5a8679b784f9f9a6012d5de7c36d7c4b` |
| git branch | `main` |
| exact tag | none recorded |
| remote URL | https://github.com/kedro-org/kedro |
| dirty state at integration | dirty: generated `skills/` artifacts were present; no pre-existing source changes were recorded in the initial snapshot |

## Evidence Paths

Primary evidence used to create this skill:

- `pyproject.toml`
- `README.md`
- `kedro/__init__.py`
- `kedro/__main__.py`
- `kedro/pipeline/`
- `kedro/io/`
- `kedro/config/`
- `kedro/framework/`
- `kedro/runner/`
- `kedro/inspection/`
- `kedro/server/`
- `kedro/templates/`
- `docs/build/`
- `docs/catalog-data/`
- `docs/configure/`
- `docs/create/`
- `docs/getting-started/`
- `docs/extend/`
- `docs/inspect/`
- `docs/integrations-and-plugins/`
- `docs/deploy/`
- `tests/pipeline/`
- `tests/io/`
- `tests/config/`
- `tests/framework/`
- `tests/runner/`
- `tests/inspection/`
- `tests/server/`
- `tests/validation/`
- `features/`
- `tools/` as source-script inventory evidence only

## Installed Package Inspection

Live inspection verified these public facts:

- `kedro` imports successfully.
- Distribution metadata resolves to Kedro `1.4.0`.
- Console script entry point is `kedro = kedro.framework.cli:main`.
- `pip check` passed in the private inspection environment used for generation.
- `kedro --help` and `kedro --version` worked with telemetry disabled.
- A tiny `Pipeline`/`DataCatalog` smoke path succeeded.

Private environment paths, activation commands, and local installation locations are intentionally omitted from this public provenance file.

## Refresh Signals

Refresh this skill when any of these change materially:

- Kedro package version, public imports, or CLI commands.
- `node()`, `Pipeline`, `DataCatalog`, `OmegaConfigLoader`, `KedroSession`, runner, hook, inspection, or server signatures.
- Project template layout or `kedro new`/`kedro pipeline` behavior.
- Optional dependency groups such as `server`, `jupyter`, or `pydantic`.
- Docs or tests for catalog/config, runner selection, hooks/plugins, inspection, or server endpoints.
