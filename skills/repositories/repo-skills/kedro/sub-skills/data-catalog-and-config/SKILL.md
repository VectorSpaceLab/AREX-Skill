---
name: data-catalog-and-config
description: "Configure, inspect, validate, and troubleshoot Kedro DataCatalog
  datasets credentials versioning and OmegaConfigLoader behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Catalog And Config

Use this sub-skill when the task is about Kedro data catalog entries, dataset classes, credentials, versioning, catalog factories, parameters, globals, or `OmegaConfigLoader` merge behavior.

## Route First

- Read [`references/api-reference.md`](references/api-reference.md) when you need the current `DataCatalog`, dataset, `CatalogConfigResolver`, `MemoryDataset`, `CachedDataset`, `SharedMemoryDataset`, or versioning APIs.
- Read [`references/configuration-and-catalogs.md`](references/configuration-and-catalogs.md) when you need `catalog.yml`, `credentials.yml`, `parameters.yml`, `globals.yml`, config environments, runtime params, factories, or merge strategies.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when a catalog/config import, validation, interpolation, credentials, optional dependency, versioning, or merge error appears.
- Run [`scripts/validate_catalog_config.py`](scripts/validate_catalog_config.py) to validate a standalone catalog YAML and optional credentials YAML without printing credential values.

## Boundary Rules

- Stay here for `DataCatalog`, `AbstractDataset`, `AbstractVersionedDataset`, `MemoryDataset`, `CachedDataset`, `SharedMemoryDataset`, credentials injection, dataset type resolution, versioning, load/save versions, catalog factories, lazy datasets, `OmegaConfigLoader`, `config_patterns`, `runtime_params`, globals, and merge strategy.
- Route pipeline graph construction, node inputs/outputs, namespaces, tags, and duplicate graph outputs to [`../pipelines-and-nodes/SKILL.md`](../pipelines-and-nodes/SKILL.md).
- Route `kedro run`, session flags, project command setup, project discovery, and CLI command construction to [`../project-cli-and-sessions/SKILL.md`](../project-cli-and-sessions/SKILL.md) or [`../runners-and-execution/SKILL.md`](../runners-and-execution/SKILL.md).
- Route hook-based catalog mutation, external credentials hooks, custom datasets as extension design, and plugin behavior to [`../hooks-and-extensions/SKILL.md`](../hooks-and-extensions/SKILL.md).
- Return to the root router at [`../../SKILL.md`](../../SKILL.md) if the request spans multiple Kedro workflow families.

## Fast Workflow

1. Identify whether the user has raw dictionaries, standalone YAML files, or a full Kedro project configuration tree.
2. For raw dictionaries or standalone YAML, validate structure with `DataCatalog.from_config(catalog, credentials)` before running any pipeline.
3. For a config tree, load through `OmegaConfigLoader(conf_source=..., env=..., runtime_params=..., base_env="base", default_run_env="local")`, then pass `conf_loader["catalog"]` and redacted `conf_loader.get("credentials", {})` to `DataCatalog.from_config()`.
4. For factories, inspect `catalog.config_resolver.list_patterns()` and use `resolve_pattern(dataset_name)` to explain how a dataset name is matched.
5. For optional dataset types such as `pandas.CSVDataset`, check that `kedro-datasets` and the relevant extras are installed; core Kedro 1.4.0 does not bundle most concrete dataset implementations.
6. For any `kedro` command used during validation, set `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` when a no-telemetry run is required.
