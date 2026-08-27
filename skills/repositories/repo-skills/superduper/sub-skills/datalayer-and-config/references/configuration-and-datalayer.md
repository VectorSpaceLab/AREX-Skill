# Configuration and Datalayer

This reference covers Superduper 0.7.x behavior for the Python API entry point, process configuration, backend URI routing, and core `Datalayer` lifecycle. It is intentionally self-contained: use it without relying on the source checkout.

## Build entry point

Primary import:

```python
from superduper import CFG, superduper
```

`superduper(item=None, **kwargs)` returns a `Datalayer`:

- `superduper()` builds from the process-global `CFG`, plus any keyword overrides.
- `superduper("scheme://...")` validates that the item is a string with a URI scheme matching `^[a-zA-Z0-9]+://`, stores it as `data_backend`, then builds a `Datalayer`.
- Invalid non-URI strings raise `ValueError` before backend construction.
- `initialize_cluster` defaults to `True`; pass `initialize_cluster=False` for lightweight inspection if no jobs, listeners, or schedulers must start.
- `force_apply=True` is commonly used in tests/smokes to avoid duplicate-apply prompts or conflicts, but it does not make destructive backend calls safe.

Minimal scratch build, assuming the MongoDB plugin is installed:

```python
from superduper import superduper

db = superduper("mongomock://skill-smoke", initialize_cluster=False, force_apply=True)
print(type(db).__name__)
print(db.cfg.data_backend)
```

If the task depends on config files or environment variables, set them before the first `import superduper` in that Python process.

## Config defaults and import-time behavior

`superduper.CFG` is created at import time from a `Config` dataclass. Important defaults:

| Field | Default | Notes |
| --- | --- | --- |
| `data_backend` | `mongodb://localhost:27017/test_db` | Requires the MongoDB plugin and a MongoDB service unless overridden. |
| `artifact_store` | `filesystem://./artifact_store` | Used by the filesystem artifact store. Prefer a scratch path for tests. |
| `metadata_store` | empty string | Empty means metadata is stored through the main Datalayer. Non-empty builds a separate metadata Datalayer. |
| `cache` | `None` | Optional cache URI. |
| `vector_search_engine` | `local` | Selects vector-search backend behavior; detailed vector recipes belong elsewhere. |
| `cluster_engine` | `local` | Builtin local cluster by default. `simple` is also builtin; other names load plugins. |
| `secrets_volume` | `~/.superduper/secrets` | Expanded at runtime; missing directory only warns. |
| `log_level` | `USER` | Enum string accepted in config. |
| `logging_type` | `SYSTEM` | Standard output/error logging. |
| `force_apply` | `False` | Global default for apply behavior. |
| `output_prefix` | `_outputs__` | Prefix for listener/model output tables. |
| `vector_search_kwargs` | `{}` | Passed to vector-search setup paths. |
| `use_component_cache` | `False` | Controls component cache use during `load`. |

The effective configuration is built from:

1. dataclass defaults;
2. a config file, if selected;
3. `SUPERDUPER_*` environment variables.

Config-file selection order:

1. `SUPERDUPER_CONFIG` if set;
2. `./superduper.yaml` in the current working directory if present;
3. `~/.superduper/config.yaml` if present.

If `SUPERDUPER_CONFIG` points to a missing file, import/config loading raises a config error. A missing default home config is ignored.

Environment-variable behavior:

- Variables must be uppercase and start with `SUPERDUPER_`.
- Names are lowercased and matched to config fields. Examples: `SUPERDUPER_DATA_BACKEND`, `SUPERDUPER_ARTIFACT_STORE`, `SUPERDUPER_METADATA_STORE`, `SUPERDUPER_CLUSTER_ENGINE`, `SUPERDUPER_VECTOR_SEARCH_ENGINE`, `SUPERDUPER_FORCE_APPLY`.
- Nested dataclass fields use underscore-separated names, for example `SUPERDUPER_RETRIES_STOP_AFTER_ATTEMPT`.
- Unknown or ambiguous variables print a warning to stderr by default instead of failing.
- Boolean defaults accept string values such as `true`, `false`, `1`, and `0`.
- Programmatic keyword overrides support nested fields with double underscores, for example `superduper(retries__stop_after_attempt=3)`.

Secrets behavior:

- If `secrets_volume` exists and contains subdirectories with a `secret_string` file, each subdirectory name is converted to an uppercase environment variable with hyphens replaced by underscores.
- If the secrets directory does not exist, Superduper emits a warning and continues. This is expected for local/mongomock smoke tests without credentials.

Implementation caveat for artifact stores in this version: the Datalayer builder constructs the filesystem artifact store from the process-global `CFG.artifact_store`. For reliable artifact-store changes, set `SUPERDUPER_CONFIG` or `SUPERDUPER_ARTIFACT_STORE` before import rather than relying only on per-call `artifact_store=...` keyword overrides.

## Backend URI mapping

Data backend construction matches URI prefixes and loads a plugin module. Missing plugin modules usually surface as `ModuleNotFoundError` for `superduper_<plugin>`.

| URI prefix | Plugin family loaded | Flavour | Notes |
| --- | --- | --- | --- |
| `mongodb://` | `mongodb` (`superduper_mongodb`) | `mongodb` | Requires MongoDB plugin and a reachable MongoDB service. |
| `mongodb+srv://` | `mongodb` (`superduper_mongodb`) | `atlas` | Atlas-style MongoDB URI; credentials/service required. |
| `mongomock://` | `mongodb` (`superduper_mongodb`) | `mongomock` | No external MongoDB service, but the MongoDB plugin and `mongomock` dependency are required. Best local smoke choice when installed. |
| `sqlite://` | `sql` (`superduper_sql`) | `base` | SQL plugin path; useful for local SQL-style tests when installed. |
| `duckdb://` | `sql` (`superduper_sql`) | `base` | SQL plugin path; requires SQL plugin plus DuckDB-compatible dependencies if used. |
| `postgresql://` | `sql` (`superduper_sql`) | `base` | PostgreSQL mapping uses `postgresql://`; service credentials required. |
| `snowflake://` | `snowflake` (`superduper_snowflake`) | `base` | External Snowflake credentials/service required. |
| `redis://` | `redis` (`superduper_redis`) | `base` | Redis plugin and service required. |
| `inmemory://` | builtin `inmemory` backend | `base` | No external plugin. Can be ephemeral (`inmemory://`) or file-backed (`inmemory://path`). |

The source also routes some additional SQL-style prefixes through the SQL plugin. Prefer the explicit prefixes above unless a task specifically targets another SQL dialect.

Cluster engine loading is separate from data backend loading:

- `local`, `simple`, and `inmemory` are builtin plugin names in the loader.
- Other cluster engine names load `superduper_<name>` and expect that plugin to expose a `Cluster` implementation.

## Datalayer lifecycle essentials

A constructed `Datalayer` owns:

- `databackend`: a proxy around the concrete data backend;
- `artifact_store`: filesystem artifact store by default;
- `cluster`: local/simple/plugin cluster backend;
- `metadata`: metadata store backed by the main Datalayer or a separate metadata Datalayer;
- `cfg`: the effective `Config` object attached after construction.

Frequently used methods:

| Method | Use | Safety notes |
| --- | --- | --- |
| `db.apply(component, force=None, wait=False, jobs=True, **variables)` | Add components such as `Table`, models, listeners, or applications. | Component/model/listener recipes are routed to other sub-skills. |
| `db.plan(component, ...)` | Produce an apply plan without applying. | Useful before mutating metadata/artifacts. |
| `db.load(component, identifier=None, version=None, uuid=None, huuid=None, overrides=None)` | Load a saved component. | `uuid` can identify a component without an identifier. |
| `db.load_all(component, **kwargs)` | Load all components of a type matching attributes. | Uses metadata and may skip missing entries. |
| `db.show(component=None, identifier=None, version=None, uuid=None, render=True)` | List components, identifiers, versions, or metadata. | `version` requires an identifier; `version=-1` means latest. |
| `db.execute(query)` | Execute a backend-native query. | Native query object/string requirements are backend-specific; not every backend implements it. |
| `db.select_nearest(like, vector_index, ids=None, outputs=None, n=100)` | Call an existing vector index to find nearest items. | Vector index construction and retrieval recipes are routed elsewhere. |
| `db.drop(force=False, data=False)` | Drop data, artifacts, metadata, and cluster state. | Destructive. Use only scratch databases; without `force=True` it asks for confirmation. |
| `db.disconnect()` | Disconnect the cluster. | Assumes a cluster object exists. |

Scratch teardown pattern:

```python
try:
    # perform smoke or test operations
    ...
finally:
    # only for scratch/local test backends you created for this run
    db.drop(force=True, data=True)
```

Do not run this teardown against user, production, or shared service-backed URIs.

## Local/mongomock smoke pattern

Use the bundled helper for diagnostics:

```bash
python scripts/superduper_datalayer_smoke.py --help
python scripts/superduper_datalayer_smoke.py --check-imports
python scripts/superduper_datalayer_smoke.py --build-db --uri mongomock://skill-smoke --check-imports
```

A config-file smoke should set a temporary YAML file and pass it with `--config-path`:

```yaml
data_backend: mongomock://skill-smoke
artifact_store: filesystem://./artifact_store
metadata_store: ""
cluster_engine: local
vector_search_engine: local
force_apply: true
log_level: INFO
```

Then run:

```bash
python scripts/superduper_datalayer_smoke.py --build-db --config-path /path/to/scratch-superduper.yaml
```

## CLI caveat

The package declares a `superduper` console script pointing at `superduper.__main__:run`, but this version does not provide `superduper.__main__`. Treat the CLI as unavailable unless a refreshed installation proves the module exists. Use the Python API or the bundled smoke script instead of routing users to `superduper --help`.
