# Kedro Package Overview

## Package Facts

- Distribution name: `kedro`.
- Import name: `kedro`.
- Version captured during generation: `1.4.0`.
- Python requirement from package metadata: `>=3.10`.
- Console script: `kedro = kedro.framework.cli:main`.
- Base dependencies include `click`, `cookiecutter`, `dynaconf`, `fsspec`, `gitpython`, `kedro-telemetry`, `omegaconf`, `pluggy`, `PyYAML`, and `rich`.
- Optional dependency groups present in package metadata include `test`, `docs`, `jupyter`, `benchmark`, `pydantic`, `server`, and `all`.

## Command Families

Kedro has global commands that work outside a project and project commands that appear when Kedro detects a project.

| Command family | Commands | Use |
| --- | --- | --- |
| Global | `kedro info`, `kedro new`, `kedro starter` | Package information, project creation, starter discovery. |
| Project | `kedro run`, `kedro catalog`, `kedro pipeline`, `kedro registry`, `kedro package`, `kedro ipython`, `kedro jupyter`, `kedro server` | Project-aware execution, catalog checks, modular pipeline scaffolding, packaging, notebooks, and optional server workflows. |

Use telemetry-safe forms in automation:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro --version
KEDRO_DISABLE_TELEMETRY=1 kedro --help
KEDRO_DISABLE_TELEMETRY=1 kedro info
```

## Public API Map

| Surface | Primary APIs | Owning sub-skill |
| --- | --- | --- |
| Pipeline graph | `node()`, `Node`, `Pipeline`, `pipeline()`, `GroupedNodes` | `sub-skills/pipelines-and-nodes/SKILL.md` |
| Catalog and config | `DataCatalog`, `MemoryDataset`, `AbstractDataset`, `AbstractVersionedDataset`, `OmegaConfigLoader` | `sub-skills/data-catalog-and-config/SKILL.md` |
| Project lifecycle | `bootstrap_project()`, `configure_project()`, `KedroSession.create()`, `session.load_context()` | `sub-skills/project-cli-and-sessions/SKILL.md` |
| Execution | `KedroSession.run()`, `SequentialRunner`, `ThreadRunner`, `ParallelRunner` | `sub-skills/runners-and-execution/SKILL.md` |
| Extension | `hook_impl`, hook specs, plugin entry points, custom CLI/dataset/runner patterns | `sub-skills/hooks-and-extensions/SKILL.md` |
| Inspection/server | `get_project_snapshot`, snapshot models, optional server endpoints | `sub-skills/inspection-and-server/SKILL.md` |

## Current Signature Snapshot

```text
kedro.pipeline.node(func, inputs, outputs, *, name=None, tags=None, confirms=None, namespace=None, preview_fn=None) -> Node
kedro.pipeline.Pipeline(nodes, *, inputs=None, outputs=None, parameters=None, tags=None, namespace=None, prefix_datasets_with_namespace=True)
kedro.pipeline.pipeline(nodes, *, inputs=None, outputs=None, parameters=None, tags=None, namespace=None, prefix_datasets_with_namespace=True) -> Pipeline
kedro.io.DataCatalog(datasets=None, config_resolver=None, load_versions=None, save_version=None)
kedro.io.DataCatalog.from_config(catalog, credentials=None, load_versions=None, save_version=None) -> DataCatalog
kedro.config.OmegaConfigLoader(conf_source, env=None, runtime_params=None, *, config_patterns=None, base_env=None, default_run_env=None, custom_resolvers=None, merge_strategy=None, ignore_hidden=True)
kedro.framework.session.KedroSession.create(project_path=None, save_on_close=True, env=None, runtime_params=None, conf_source=None) -> KedroSession
kedro.framework.session.KedroSession.run(self, pipeline_name=None, pipeline_names=None, tags=None, runner=None, node_names=None, from_nodes=None, to_nodes=None, from_inputs=None, to_outputs=None, load_versions=None, namespaces=None, only_missing_outputs=False) -> dict[str, Any]
kedro.runner.SequentialRunner(is_async=False)
kedro.runner.ThreadRunner(max_workers=None, is_async=False)
kedro.runner.ParallelRunner(max_workers=None, is_async=False)
```

## Cross-Skill Workflow Examples

### Create and Run a Small Project

1. Use `project-cli-and-sessions` to choose `kedro new --name=... --tools=... --example=... --telemetry=no` and validate the generated package name.
2. Use `pipelines-and-nodes` to design pipeline factories under the project package.
3. Use `data-catalog-and-config` to create `catalog.yml`, `parameters.yml`, and credentials indirection.
4. Use `runners-and-execution` to construct `kedro run` with runner, tags, namespaces, runtime params, and load versions.

### Debug a Pipeline Failure

1. Use `runners-and-execution` to classify whether the failure happened during selection, load, node run, save, hook execution, or runner orchestration.
2. Use `pipelines-and-nodes` if the failure mentions invalid nodes, duplicate outputs, circular dependencies, parameter mapping, or graph slicing.
3. Use `data-catalog-and-config` if the failure mentions missing datasets, dataset type imports, credentials, versioning, config duplicate keys, or interpolation.
4. Use `hooks-and-extensions` if a hook/plugin/custom command/custom runner changes the execution path.

### Inspect Without Running

1. Use `inspection-and-server` for `get_project_snapshot` or optional `/snapshot` server behavior.
2. Use `project-cli-and-sessions` only for project detection and bootstrap metadata.
3. Avoid `kedro run`, dataset loads, credentials access, or server startup unless the user explicitly asks for execution.

## Optional Extras Guidance

- Use base `kedro` for core project, pipeline, catalog, config, session, and runner APIs.
- Add `kedro-datasets` and its dataset-specific dependencies when catalog entries use concrete dataset types such as `pandas.CSVDataset`.
- Add `kedro[jupyter]` or notebook dependencies for `kedro jupyter`, `%reload_kedro`, or notebook integration workflows.
- Add `kedro[server]` or equivalent `fastapi` and `uvicorn` packages for `kedro server` workflows.
- Add `kedro[pydantic]` when project validation/server models require pydantic support.
- Avoid broad `kedro[all]` installs unless the user explicitly needs multiple optional surfaces.
