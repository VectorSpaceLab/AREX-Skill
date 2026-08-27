# Inspection API

Use this reference when the task is to inspect a Kedro project structure without executing pipeline nodes or loading datasets.

## Primary Entry Point

Import the public API from `kedro.inspection`:

```python
from kedro.inspection import get_project_snapshot

snapshot = get_project_snapshot(project_path=".")
```

Signature in Kedro `1.4.0`:

```text
get_project_snapshot(project_path=None, env=None, conf_source=None, metadata=None) -> ProjectSnapshot
```

Arguments:

- `project_path`: path to the Kedro project root, meaning the directory containing `pyproject.toml`; accepts a string or `pathlib.Path`.
- `env`: optional Kedro configuration environment such as `local`, `staging`, or `prod`; valid values contain only letters, digits, hyphens, and underscores.
- `conf_source`: optional configuration directory override, equivalent to the configuration source used by project/session workflows.
- `metadata`: optional `ProjectMetadata` returned by `kedro.framework.startup.bootstrap_project()`; when supplied, the snapshot builder skips another bootstrap call.

At least one of `project_path` or `metadata` is required. If both are supplied and point to different projects, `metadata.project_path` takes precedence and a `UserWarning` is emitted.

## What It Reads And Does Not Do

`get_project_snapshot()` bootstraps or uses project metadata, imports registered project pipelines, loads catalog configuration, and reads top-level parameter keys. It does not execute nodes, call `DataCatalog.load()`, call `DataCatalog.save()`, run hooks through a runner, or write pipeline outputs.

Safe uses:

- Summarize project metadata and registered pipeline names for documentation, CI checks, or IDE tooling.
- Check whether expected datasets and parameter keys are configured.
- Inspect node names, namespaces, tags, free inputs, and final outputs.
- Compare structural snapshots across environments by changing `env` or `conf_source`.

Unsafe assumptions:

- It is not a static parser; bootstrapping may import project package code and pipeline registry modules.
- It does not prove that a pipeline run will succeed; execution, runner, hook, dataset dependency, and credentials errors may only appear at run time.
- It does not expose parameter values, credentials, or arbitrary catalog fields; use config/catalog guidance for those workflows.

## Snapshot Dataclasses

`ProjectSnapshot` has four fields:

- `metadata`: `ProjectMetadataSnapshot` with `project_name`, `package_name`, and `kedro_version` from project metadata.
- `pipelines`: list of `PipelineSnapshot` objects, one per registered pipeline that is not `None`.
- `datasets`: dictionary mapping dataset names to `DatasetSnapshot` objects built from catalog configuration, including concrete entries resolved from dataset factory patterns when used by pipeline nodes.
- `parameters`: sorted list of top-level parameter keys; values are intentionally not stored.

`PipelineSnapshot` fields:

- `name`: pipeline registry key such as `__default__`, `data_engineering`, or `training`.
- `nodes`: topologically ordered list of `NodeSnapshot` objects.
- `inputs`: sorted free inputs of the pipeline.
- `outputs`: sorted final outputs of the pipeline.

`NodeSnapshot` fields:

- `name`: fully qualified node name, including namespace prefix when present.
- `namespace`: namespace string or `None`.
- `tags`: sorted list of tag strings.
- `inputs`: ordered input dataset names.
- `outputs`: ordered output dataset names.

`DatasetSnapshot` fields:

- `name`: catalog dataset name.
- `type`: configured dataset type string such as `pandas.CSVDataset`.
- `filepath`: configured file path if present, otherwise `None`; URI credentials of the form `scheme://user:password@host` are redacted as `<redacted>`.

## Read-Only Summary Pattern

Use this pattern when an agent needs a compact project summary without executing the project:

```python
from kedro.inspection import get_project_snapshot

snapshot = get_project_snapshot(project_path=".", env="local")

summary = {
    "project_name": snapshot.metadata.project_name,
    "package_name": snapshot.metadata.package_name,
    "kedro_version": snapshot.metadata.kedro_version,
    "pipelines": [
        {
            "name": pipeline.name,
            "nodes": [node.name for node in pipeline.nodes],
            "inputs": pipeline.inputs,
            "outputs": pipeline.outputs,
        }
        for pipeline in snapshot.pipelines
    ],
    "datasets": {
        name: {"type": dataset.type, "filepath": dataset.filepath}
        for name, dataset in snapshot.datasets.items()
    },
    "parameters": snapshot.parameters,
}
```

Keep the output structural. Do not print credential files, full parameter dictionaries, or arbitrary `OmegaConfigLoader` values unless the user explicitly requests config debugging and secrets are handled.

## Multi-Environment Pattern

For repeated snapshots, bootstrap once and reuse metadata:

```python
from kedro.framework.startup import bootstrap_project
from kedro.inspection import get_project_snapshot

metadata = bootstrap_project(".")
base_snapshot = get_project_snapshot(metadata=metadata)
staging_snapshot = get_project_snapshot(metadata=metadata, env="staging")
```

Use the programmatic API rather than the HTTP server when the task needs per-call `env` or `conf_source` changes. The HTTP `/snapshot` endpoint uses the environment and configuration source fixed at server startup.

## Empty And Missing Sections

- Missing catalog configuration is treated as an empty dataset mapping for snapshot construction.
- Dataset entries whose names start with `_` and non-dictionary catalog entries are skipped.
- Datasets referenced only as node inputs/outputs but not configured in the catalog are not included, unless a dataset factory pattern resolves to a concrete dataset used by a node.
- Missing parameters configuration produces an empty `parameters` list.
- A pipeline registry value of `None` is skipped.

## Routing Decisions

- If the user wants to author or refactor nodes/pipelines, route to `../pipelines-and-nodes/SKILL.md`.
- If the user wants to validate catalog YAML, credentials, factory patterns, config loaders, or parameter values, route to `../data-catalog-and-config/SKILL.md`.
- If the user wants to execute or dry-run pipeline code, route to `../runners-and-execution/SKILL.md`; inspection is not an execution dry run.
- If project bootstrap or CLI discovery fails before inspection can start, route to `../project-cli-and-sessions/SKILL.md`.
