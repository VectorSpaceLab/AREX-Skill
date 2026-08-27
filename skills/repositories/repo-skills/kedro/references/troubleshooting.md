# Kedro Cross-Cutting Troubleshooting

Use this reference for package-level failures before routing to a focused sub-skill.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'kedro'` | Kedro is not installed in the active Python environment. | Run `python -m pip install kedro` in the intended environment and verify with `python -c "import kedro; print(kedro.__version__)"`. |
| `kedro: command not found` | Console script path is not on `PATH` or Kedro is installed in a different environment. | Use `python -m kedro --help` or run `python -m pip show kedro` in the intended environment; fix activation or PATH. |
| `No module named kedro_datasets...` | Core Kedro no longer bundles most concrete dataset implementations. | Install `kedro-datasets` and the dataset-specific dependency, then route catalog details to `sub-skills/data-catalog-and-config/SKILL.md`. |
| Optional server imports fail for `fastapi`, `uvicorn`, or pydantic | Server dependencies are optional. | Install `kedro[server]` or equivalent packages, then route endpoint details to `sub-skills/inspection-and-server/SKILL.md`. |
| Notebook commands fail for `IPython`, `jupyter`, or `notebook` | Interactive dependencies are optional. | Install notebook dependencies or `kedro[jupyter]`, then route setup to `sub-skills/project-cli-and-sessions/SKILL.md`. |

## CLI and Telemetry

- Use `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for automated probes that must not attempt telemetry calls.
- If `kedro --help` logs telemetry text or waits on a network timeout, rerun with telemetry disabled.
- If a project command such as `kedro run` is missing outside a project, Kedro likely did not detect a project; route project detection to `sub-skills/project-cli-and-sessions/SKILL.md`.
- If a plugin command shadows a built-in command, Kedro gives plugin commands precedence. Route plugin and custom CLI conflicts to `sub-skills/hooks-and-extensions/SKILL.md`.

## Project Detection

Kedro project commands require a project root or parent directory with Kedro metadata.

Check these points:

1. The current directory or a parent has `pyproject.toml` with a Kedro project section.
2. The project package is importable from its source directory or installed package.
3. `settings.py` and `pipeline_registry.py` are valid Python modules for the project package.
4. Scripts outside the project call `bootstrap_project(project_root)` before creating sessions.
5. Packaged-project code calls `configure_project(package_name)` when it is not running through `kedro` CLI bootstrapping.

## Stale API Imports

- Use `from kedro.pipeline import pipeline`, not `kedro.pipeline.modular_pipeline`, for reusable and namespaced pipelines in this Kedro version.
- Use `DataCatalog.from_config(catalog, credentials=None, load_versions=None, save_version=None)` for catalog dictionaries.
- Use `OmegaConfigLoader` for modern config loading; older `ConfigLoader` and `TemplatedConfigLoader` guidance is stale for current Kedro.
- Treat `DataSet` spelling in dataset class names as legacy; current `kedro-datasets` names use `Dataset`.

## Config and Credentials

- Do not print credential values while debugging. Show key names and missing-key errors only.
- `conf/local` is intended for local or protected settings; do not tell users to commit secrets from `credentials.yml`.
- Duplicate top-level config keys in the same environment usually raise errors; duplicate keys across environments are overridden by the later environment unless a merge strategy changes behavior.
- Remote config sources such as S3, GCS, Azure, or HTTP require authentication outside the Kedro config tree.

Route detailed catalog/config errors to `sub-skills/data-catalog-and-config/SKILL.md`.

## Pipeline and Runner Failures

| Symptom | Route |
| --- | --- |
| Invalid node input/output types, duplicate outputs, circular dependencies, stale modular pipeline imports, bad `params:` mapping | `sub-skills/pipelines-and-nodes/SKILL.md` |
| Missing catalog datasets, dataset type import failures, credentials, versioned dataset errors, factories, lazy dataset materialization | `sub-skills/data-catalog-and-config/SKILL.md` |
| Runner choice, `--async`, `ParallelRunner`, `KEDRO_MP_CONTEXT`, hooks missing under parallel execution, missing-output resume | `sub-skills/runners-and-execution/SKILL.md` |
| Hook/plugin/custom CLI/custom dataset/custom runner behavior | `sub-skills/hooks-and-extensions/SKILL.md` |
| Read-only project snapshot, optional `/snapshot` API, server startup | `sub-skills/inspection-and-server/SKILL.md` |

## Side-Effect Boundaries

Warn before running commands that can write files, use network access, or start long-running processes:

- `kedro new` writes a project directory.
- `kedro starter list` or remote starter creation may use network/Git/Cookiecutter.
- `kedro run` executes user node code and may load/save datasets.
- `kedro package` builds artifacts under `dist/`.
- `kedro server start` starts a service and may trigger project snapshot/run behavior depending on endpoint use.
- Deployment recipes for Databricks, Airflow, Argo, AWS Batch, Step Functions, Kubeflow, Prefect, Dagster, Dask, and cloud platforms may require credentials and external state.
