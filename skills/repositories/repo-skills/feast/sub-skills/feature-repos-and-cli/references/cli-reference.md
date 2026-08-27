# CLI Reference for Feature Repositories

## Global CLI Discovery Flags

Feast commands resolve a feature repository and config file before most repo-aware operations:

```bash
feast --chdir /path/to/feature_repo configuration
feast -c /path/to/feature_repo plan
feast --feature-store-yaml /path/to/custom_feature_store.yaml configuration
feast -c /path/to/feature_repo -f /path/to/custom_feature_store.yaml apply
```

- `--chdir` / `-c` switches to a feature repository directory before running the subcommand. It can also be supplied through `FEATURE_REPO_DIR_ENV_VAR`.
- `--feature-store-yaml` / `-f` overrides the `feature_store.yaml` file Feast should load. It can also be supplied through the Feast feature-store-yaml environment variable used by the CLI.
- `--log-level` accepts standard Python logging levels such as `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
- Repo-aware commands fail early with a message like `Can't find feature repo configuration file at ...` when the selected config file does not exist.

## Create Repositories

```bash
feast init my_project
feast init my_project --minimal
feast init my_project --template local
feast init my_project --repo-path /tmp/my_repo
```

- `feast init PROJECT_DIRECTORY` creates a project directory and, for the default local template, places the actual feature repository under `PROJECT_DIRECTORY/feature_repo`.
- If `PROJECT_DIRECTORY` is omitted, Feast generates a name from an adjective and animal.
- Valid project names use alphanumeric characters, underscores, and hyphens, and must not start with `_` or `-`.
- `--minimal` creates an empty project repository by selecting the minimal template.
- `--template` supports templates including `local`, `gcp`, `aws`, `snowflake`, `spark`, `postgres`, `hbase`, `cassandra`, `hazelcast`, `couchbase`, `milvus`, `ray`, `ray_rag`, and `pytorch_nlp`.
- `--repo-path` creates the repository at an explicit target path instead of the default project-name subdirectory.

## Inspect Configuration

```bash
feast -c feature_repo configuration
feast -c feature_repo registry-dump
feast -c feature_repo version
```

- `configuration` prints the loaded repo config as YAML and omits the internal `repo_path` field.
- `registry-dump` prints registry metadata as JSON for debugging. It reads the configured registry path and project.
- `version` prints the installed Feast SDK version.

## Plan and Apply

```bash
feast -c feature_repo plan
feast -c feature_repo plan --skip-source-validation
feast -c feature_repo plan --skip-feature-view-validation
feast -c feature_repo apply
feast -c feature_repo apply --skip-source-validation --no-progress
feast -c feature_repo apply --no-promote
```

- `plan` imports feature repo Python files, parses Feast objects, validates sources unless skipped, and prints registry and infrastructure diffs without applying them.
- `apply` imports feature repo Python files, computes desired state, and updates the registry and provider-managed infrastructure.
- `--skip-source-validation` skips source existence checks performed by the provider. Use it for local dry planning when data files or remote tables are not yet reachable.
- `--skip-feature-view-validation` skips important feature view checks and should be used only to unblock known-safe migration or diagnosis work.
- `--no-progress` disables apply progress bars by setting Feast's no-progress environment behavior for the process.
- `--no-promote` saves new feature view versions without promoting them to active; version-qualified reads and materialization can still target them.

## List Registered Objects

Common object listing commands are grouped by object type:

```bash
feast -c feature_repo entities list
feast -c feature_repo data-sources list
feast -c feature_repo feature-views list
feast -c feature_repo stream-feature-views list
feast -c feature_repo on-demand-feature-views list
feast -c feature_repo feature-services list
feast -c feature_repo features list
feast -c feature_repo projects list
feast -c feature_repo saved-datasets list
feast -c feature_repo validation-references list
feast -c feature_repo label-views list
feast -c feature_repo permissions list
```

Use `feast COMMAND --help` for object-specific filters or output options. If a listing command reports an empty result after `apply`, verify that the `project` in `feature_store.yaml` matches any `Project(name=...)` object defined in Python.

## Delete and Teardown

```bash
feast -c feature_repo delete OBJECT_ID
feast -c feature_repo teardown
```

- `delete OBJECT_ID` looks up the object by name across supported Feast object types and applies a deletion if found.
- `teardown` removes deployed feature store infrastructure through the configured provider.
- Treat both commands as destructive. Run `configuration`, `registry-dump`, and a reviewed `plan` first, and confirm the selected `--chdir`, `--feature-store-yaml`, `project`, registry, and provider are the intended ones.

## Commands Owned Elsewhere

- `materialize`, `materialize-incremental`, `get-online-features`, `get-historical-features`, `validate`, and `monitor` are primarily retrieval/materialization workflows; use `../../retrieval-and-materialization/SKILL.md`.
- `serve`, `serve_offline`, `serve_registry`, `serve_transformations`, `listen`, `endpoint`, and `ui` are server or service workflows; use `../../servers-and-remote/SKILL.md`.
- `dbt` and optional backend selection usually belong with integrations; use `../../integrations-and-extensibility/SKILL.md` when the task is about external systems rather than basic repo operation.
