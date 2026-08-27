# Custom Datasets CLI And Runner Extensions

Use this reference when extending Kedro with new dataset implementations, project-specific commands, reusable plugin commands, or custom runner classes. For basic `catalog.yml` and config behavior, use `../data-catalog-and-config/SKILL.md`; for routine runner selection and `kedro run` flags, use `../runners-and-execution/SKILL.md`.

## Custom Dataset Contract

Custom datasets subclass `kedro.io.AbstractDataset` or `kedro.io.AbstractVersionedDataset`. A minimum dataset implements:

- `load(self) -> LoadedType`
- `save(self, data: SavedType) -> None`
- `_describe(self) -> dict[str, Any]`

Kedro wraps `load` and `save` methods to log operations and convert unexpected exceptions into `kedro.io.DatasetError`. Raise `DatasetError` yourself when you can provide a clearer message.

```python
# src/<package_name>/datasets/json_lines_dataset.py
from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any

import fsspec
from kedro.io import AbstractDataset
from kedro.io.core import get_filepath_str, get_protocol_and_path


class JsonLinesDataset(AbstractDataset[list[dict[str, Any]], list[dict[str, Any]]]):
    def __init__(self, filepath: str, fs_args: dict[str, Any] | None = None):
        protocol, path = get_protocol_and_path(filepath)
        self._protocol = protocol
        self._filepath = PurePosixPath(path)
        self._fs_args = fs_args or {}
        self._fs = fsspec.filesystem(protocol, **self._fs_args)

    def load(self) -> list[dict[str, Any]]:
        load_path = get_filepath_str(self._filepath, self._protocol)
        with self._fs.open(load_path, "r") as file_obj:
            return [json.loads(line) for line in file_obj if line.strip()]

    def save(self, data: list[dict[str, Any]]) -> None:
        save_path = get_filepath_str(self._filepath, self._protocol)
        with self._fs.open(save_path, "w") as file_obj:
            for row in data:
                file_obj.write(json.dumps(row) + "\n")

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._filepath), "protocol": self._protocol}
```

Register by fully qualified class path in `catalog.yml`:

```yaml
events:
  type: <package_name>.datasets.json_lines_dataset.JsonLinesDataset
  filepath: data/01_raw/events.jsonl
```

Dataset constructor parameters should match the YAML keys. Kedro raises `DatasetError` messages such as `must only contain arguments valid for the constructor` when the config contains unknown keys, and `cannot be instantiated` when abstract methods are missing.

## Dataset Design Rules

- Prefer constructor names `filepath`, `filename`, or `path` for storage locations.
- Use `fsspec` and Kedro helpers `get_protocol_and_path()` and `get_filepath_str()` when supporting local and remote file systems.
- Return a compact `_describe()` dictionary with safe, non-secret configuration details.
- Do not print credentials or resolved secret values in `_describe()`, errors, hooks, or logs.
- If the dataset cannot work with multiprocessing, set `_SINGLE_PROCESS = True`; `ParallelRunner` catalog validation checks this constraint.
- Use `AbstractVersionedDataset` only when the dataset must support Kedro load/save version semantics. Accept a `version` argument and delegate path resolution through the versioned base class.
- Do not combine versioning with partitioned dataset patterns unless the concrete partitioned dataset implementation explicitly supports it.
- If the dataset requires optional packages such as `Pillow`, `s3fs`, cloud SDKs, or database drivers, document them in project requirements and test import errors separately from catalog syntax.

## Dataset Validation Checks

Run small checks before using a custom dataset in a full pipeline:

```python
from kedro.io import AbstractDataset, DataCatalog
from <package_name>.datasets.json_lines_dataset import JsonLinesDataset

assert issubclass(JsonLinesDataset, AbstractDataset)

catalog = DataCatalog.from_config({
    "events": {
        "type": "<package_name>.datasets.json_lines_dataset.JsonLinesDataset",
        "filepath": "data/01_raw/events.jsonl",
    }
})
assert "events" in catalog.list()
```

If validation fails, first check importability and constructor arguments. If validation passes but `load()` fails, move to data availability, permissions, optional backends, or remote filesystem credentials.

## Project CLI Overrides

Use `src/<package_name>/cli.py` when a single Kedro project needs custom behavior or a command override. The module must expose a Click group named `cli`.

```python
# src/<package_name>/cli.py
from __future__ import annotations

import click
from kedro.framework.cli.project import run as kedro_run


@click.group(name=__file__)
def cli() -> None:
    """Project-specific Kedro commands."""


@cli.command("hello")
def hello() -> None:
    click.echo("Hello from this Kedro project")


# Reuse the built-in command under the same name only when you intentionally override it.
run = kedro_run
```

Kedro imports `<package_name>.cli` for project commands. If `cli.py` exists but lacks a `cli` object, Kedro raises `Cannot load commands from <package_name>.cli`. If you override `run`, either preserve Kedro's run options or clearly document the new contract.

For command groups such as `kedro pipeline` or `kedro jupyter`, import and extend the corresponding group from Kedro framework modules, then attach additional subcommands. Keep the base group available if you still want stock subcommands.

## Reusable Plugin Commands

Use plugins when the command should work across multiple Kedro projects.

```python
# myplugin/commands.py
import click
from kedro.framework.session import KedroSession


@click.group(name="myplugin")
def commands() -> None:
    """Reusable Kedro plugin commands."""


@commands.command("summarise")
@click.pass_obj
def summarise(project_metadata) -> None:
    with KedroSession.create(project_path=project_metadata.project_path) as session:
        context = session.load_context()
    click.echo(f"Datasets: {len(context.catalog.list())}")
```

```toml
[project.entry-points."kedro.project_commands"]
myplugin = "myplugin.commands:commands"
```

For commands that run outside a project, use `kedro.global_commands` and avoid `click.pass_obj` project metadata assumptions. For heavy command groups, consider lazy loading by using `kedro.framework.cli.utils.LazyGroup` and delayed imports in subcommands.

## Command Conflict Rules

- Built-in project commands are loaded first.
- Plugin project command groups can override built-in commands.
- Project `cli.py` commands can override both plugins and built-ins.
- Group options and callbacks can be lost when Click groups are merged into Kedro's command collection; put important validation on the command function itself.
- If a custom command should make network calls, mutate cloud state, create projects, or upload artifacts, include explicit flags and dry-run modes where practical.

Use telemetry-safe probes while debugging command availability:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro --help
KEDRO_DISABLE_TELEMETRY=1 kedro info
```

`kedro info` reports installed plugins and their entry point groups when discovery succeeds.

## Custom Runner Surface

A custom runner subclasses `kedro.runner.AbstractRunner`. In Kedro 1.4.0, `AbstractRunner.run()` performs shared validation and then calls `_run(pipeline, catalog, hook_manager, run_id)`. Concrete runners implement:

- `__init__(..., is_async: bool = False)` and call `super().__init__(is_async=is_async)`.
- `_get_executor(self, max_workers: int) -> Executor | None` when using the shared scheduling implementation.
- `_run(...)` to execute nodes, respecting catalog load/save/release behavior and hook manager behavior.

A minimal custom runner often wraps existing runner behavior rather than reimplementing scheduling:

```python
from kedro.pipeline import Pipeline
from kedro.runner import AbstractRunner, SequentialRunner


class AuditedRunner(AbstractRunner):
    def __init__(self, is_async: bool = False):
        super().__init__(is_async=is_async)
        self._delegate = SequentialRunner(is_async=is_async)

    def _get_executor(self, max_workers: int):
        return None

    def _run(self, pipeline: Pipeline, catalog, hook_manager=None, run_id: str | None = None) -> None:
        self._logger.info("Audited runner starting %d nodes", len(pipeline.nodes))
        self._delegate._run(pipeline, catalog, hook_manager, run_id)
```

For production runners, prefer using `SequentialRunner` internally for single-node execution and be explicit about distributed object serialization, catalog persistence, hook registration, and failure propagation.

## Custom Runner With Server

`kedro.server` accepts runner short names such as `SequentialRunner` and fully qualified runner paths. Fully qualified runner modules must belong to `kedro.runner`, the project package, or a module listed in `settings.RUNNER_MODULES_WHITELIST`.

```python
# src/<package_name>/settings.py
RUNNER_MODULES_WHITELIST = ("external_runner_package.runners",)
```

The server rejects runner classes that are not subclasses of `kedro.runner.AbstractRunner`. Route detailed endpoint behavior to `../inspection-and-server/SKILL.md`.

## Runner Extension Checks

- Instantiate the runner before passing it to `KedroSession.run()`: `runner=MyRunner()`, not `runner=MyRunner`.
- Confirm every node function and custom dataset can be serialized before using multiprocessing or distributed runners.
- Decide whether node/dataset hooks should run on workers. `ParallelRunner` does not pass the hook manager to worker `Task` objects in its process pool path, so extension runners must deliberately register or proxy hooks if needed.
- Preserve `run_id`, `is_async`, exception propagation, dataset release, and `only_missing_outputs` expectations where possible.
- For external compute engines, ensure all intermediate datasets needed across tasks are persisted in the catalog; `MemoryDataset` is not sufficient across process, worker, or orchestrator boundaries.

## Cross-Routes

- Use `../data-catalog-and-config/SKILL.md` for catalog factories, credentials injection, versioning configuration, and `DataCatalog.from_config()` details.
- Use `../runners-and-execution/SKILL.md` for choosing between built-in runners, constructing `kedro run --runner ...`, and debugging resume or slicing flags.
- Use `../project-cli-and-sessions/SKILL.md` for `bootstrap_project()`, `configure_project()`, `KedroSession.create()`, package mode, and stock CLI commands.
