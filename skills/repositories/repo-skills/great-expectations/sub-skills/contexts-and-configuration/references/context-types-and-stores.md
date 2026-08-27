# Context Types and Stores

Great Expectations exposes Data Contexts through `great_expectations.get_context(...)`. A context owns project configuration, metadata stores, Data Docs site config, and manager/factory objects for datasources, suites, validation definitions, and checkpoints.

## Context Selection

| Need | Use | Notes |
| --- | --- | --- |
| Temporary notebook, smoke test, pipeline-local validation setup | `gx.get_context(mode="ephemeral")` | Builds an `EphemeralDataContext` with in-memory stores. It is safe for experiments but object definitions are not persisted for future sessions. |
| Persist suites, validation definitions, checkpoints, datasources, store paths, and Data Docs config | `gx.get_context(mode="file", project_root_dir=...)` | Builds or loads a filesystem-backed `FileDataContext`. Prefer this for projects and repeatable automation. |
| Load a specific context directory that contains `great_expectations.yml` | `gx.get_context(context_root_dir=...)` | `context_root_dir` points at the context directory itself; `project_root_dir` points at the parent project root. Do not pass both for file mode. |
| Override a file context's config while loading | `gx.get_context(project_config=..., context_root_dir=...)` | Use sparingly for controlled migrations or tests; normal persisted changes should go through `context.variables`. |
| In-memory config without a project directory | `gx.get_context(project_config=DataContextConfig(...), mode="ephemeral")` | Good for small scripts that construct stores and Data Docs config programmatically. |
| GX Cloud | Avoid in this GX Core line | `mode="cloud"`, `cloud_mode=True`, complete `cloud_*` arguments, or complete `GX_CLOUD_*` environment configuration raise a GX Cloud shutdown error. |

If `mode` is omitted, GX first checks for Cloud configuration, then searches for a file-backed project, and finally falls back to an ephemeral context. To avoid surprises, pass `mode="file"` or `mode="ephemeral"` explicitly in generated automation.

## Root Directory Behavior

- `project_root_dir` is the directory that should contain or receive the context directory.
- `context_root_dir` is the context directory itself, often named `great_expectations`.
- `gx.get_context(mode="file")` without an explicit root uses the current working directory as the project root when it needs to scaffold a project.
- A file context scaffolds missing context files and directories when given a valid file-mode root.
- A file context must be reloaded after changes to stores, Data Docs sites, config variables path, or analytics settings because those values are read when the context initializes.

## Persistence Model

Ephemeral contexts:

- Use in-memory store backends by default.
- Return a new in-memory context for each `gx.get_context(mode="ephemeral")` call.
- Can be useful with `DataContextConfig(store_backend_defaults=InMemoryStoreBackendDefaults(...))`.
- Can be converted to a file context with `context.convert_to_file_context()`, which scaffolds a file-backed project in the current working directory.

File contexts:

- Load and save `great_expectations.yml` plus uncommitted config variables and generated metadata directories.
- Persist fluent datasource definitions, expectation suites, validation definitions, checkpoints, validation results, and Data Docs configuration through context variables and stores.
- Use `context.variables.config` when you need the raw values before substitution and `context.variables` properties when you want resolved values.

## Core Managers and Factories

After context creation, these public manager attributes are the stable entry points:

| Attribute | Typical methods | Owns |
| --- | --- | --- |
| `context.data_sources` | `add_*`, `add_or_update_*`, `get`, `all`, `delete_*`, `delete` | Fluent datasource definitions and assets. Route detailed work to `../datasources-and-assets/SKILL.md`. |
| `context.suites` | `add`, `add_or_update`, `get`, `all`, `delete` | Expectation suites. Route suite authoring to `../expectations-and-suites/SKILL.md`. |
| `context.validation_definitions` | `add`, `add_or_update`, `get`, `all`, `delete` | Persistent pairings of data and suites. Route execution to `../validations-and-results/SKILL.md`. |
| `context.checkpoints` | `add`, `add_or_update`, `get`, `all`, `delete` | Checkpoint orchestration. Route actions and Data Docs automation to `../checkpoints-actions-and-data-docs/SKILL.md`. |

## Store Configuration

GX stores separate object types under names recorded in the context config:

- `expectations_store_name` for expectation suites.
- `validation_results_store_name` for validation results.
- `checkpoint_store_name` for checkpoints.
- `validation_definition_store` entries for validation definitions.
- Data Docs site configuration under `data_docs_sites`.

For file contexts, inspect and update raw store config through `context.variables.config.stores`. To change a filesystem store location, update the relevant `store_backend.base_directory`, call `context.variables.save()`, then recreate the context. Prefer paths relative to the project root unless the application intentionally uses an absolute shared path.

## Minimal Patterns

```python
import great_expectations as gx

context = gx.get_context(mode="ephemeral")
print(type(context).__name__, context.mode)
```

```python
import great_expectations as gx

context = gx.get_context(mode="file", project_root_dir="./gx-project")
context.variables.analytics_enabled = False
context.variables.save()
context = gx.get_context(mode="file", project_root_dir="./gx-project")
```
