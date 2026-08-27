# Dask Configuration

Dask configuration combines built-in defaults, YAML files, environment variables, and temporary in-process overrides. Use this reference for the mechanics before handing collection-specific settings to the array or dataframe sub-skills.

## Core APIs

| API | Use | Notes |
| --- | --- | --- |
| `dask.config.get(key, default=no_default, config=None, override_with=None)` | Read a nested setting by dot path | Raises for a missing key unless `default` is provided; returns `override_with` directly when it is not `None` |
| `dask.config.set(mapping=None, **kwargs)` | Temporarily or permanently update a config dict | Use as a context manager for scoped overrides; dot paths build nested dictionaries |
| `dask.config.collect(paths=..., env=None)` | Read YAML/JSON files and env vars into a dict | Does not mutate global config |
| `dask.config.refresh(paths=..., env=...)` | Rebuild global config from defaults, files, and env | Useful after changing env vars or config files in the same process |
| `dask.config.merge(*dicts)` / `update(old, new, priority=...)` | Merge nested dictionaries | Later mappings normally win; `priority='old'` preserves existing values |
| `dask.config.ensure_file(source, destination=...)` | Copy a default config file into a config directory | Does not overwrite existing files |
| `dask.config.serialize` / `deserialize` | Encode config for worker inheritance | Used internally via `DASK_INTERNAL_INHERIT_CONFIG` |

## Search Paths And Priority

Dask builds config paths from:

1. `DASK_ROOT_CONFIG`, defaulting to `/etc/dask`.
2. Environment-specific `etc/dask` directories from the active Python prefix/site prefixes.
3. The user config directory, usually `~/.config/dask`.
4. `DASK_CONFIG`, when set, appended as an additional path and also used as the default write directory for `dask config set`.

Config files may be `.yaml`, `.yml`, or `.json`. Directory contents are read in sorted filename order. Later config sources override earlier ones during collection, while nested dictionaries are merged.

## Key Syntax

- Use dot notation for nested access: `optimization.fuse.ave-width`.
- Hyphens and underscores are canonicalized against existing keys, so `ave_width` and `ave-width` can refer to the same existing setting.
- Environment variables use `DASK_` prefix, lowercase conversion, and `__` for nesting. Example: `DASK_ARRAY__CHUNK_SIZE='256MiB'` maps to `array.chunk-size`.
- Environment values are interpreted with Python literal parsing where possible, so strings like `True`, `123`, `None`, lists, and dicts may become typed values.

## Built-In Defaults

Representative defaults from the bundled config include:

| Key | Default | Ownership |
| --- | --- | --- |
| `temporary-directory` | `null` | Cross-cutting local disk spill/temp behavior |
| `visualization.engine` | `null` | Collection graph visualization engine selection |
| `tokenize.ensure-deterministic` | `false` | Tokenization determinism behavior |
| `optimization.annotations.fuse` | `true` | Optimization handling for annotated layers |
| `optimization.tune.active` | `true` | Partition tuning optimization |
| `optimization.fuse.active` | `null` | Generic fuse activation; collection-specific behavior may differ |
| `admin.async-client-fallback` | `null` | Async client fallback behavior |
| `admin.traceback.shorten` | list of regexes | Short traceback filtering |

Collection-owned defaults are present in the same config file but should be routed for details:

- Array: `array.backend`, `array.chunk-size`, `array.rechunk.*`, `array.slicing.split-large-chunks`, `array.query-planning`.
- Dataframe: `dataframe.backend`, `dataframe.shuffle.*`, `dataframe.parquet.*`, `dataframe.convert-string`, `dataframe.query-planning`.

## Safe Usage Patterns

```python
import dask

# Read with a fallback.
tmpdir = dask.config.get("temporary-directory", default=None)

# Scoped override; automatically restored afterward.
with dask.config.set({"optimization.fuse.active": False}):
    result = collection.compute()

# Inspect a custom config directory without mutating global config.
config = dask.config.collect(paths=["/path/to/config"], env={})
```

For generated code and examples, prefer context-managed `dask.config.set` over global mutation. Avoid calling `.compute()` or `.persist()` while defining lazy Dask collections unless the user explicitly asks to materialize results.

## Import-Time Configuration Caveats

Some settings affect module-level backend selection or query-planning behavior and must be set before importing the relevant collection module in a Python process. Common examples include:

- `array.query-planning`
- `dataframe.query-planning`
- Backend selection keys used during collection module initialization

If a value appears not to take effect, start a fresh Python process with the environment variable or YAML setting in place before the first `import dask.array` or `import dask.dataframe`.

## Persistent Objects

Dask objects may capture some configuration-derived behavior when they are created. If a config override should affect graph construction, set it before constructing the collection, not only before `.compute()`.

## Schema And Validation

`dask/dask-schema.yaml` is the repo-maintained JSON schema for bundled config defaults. It is useful when adding or auditing config keys: every default should be represented in the schema, and tests validate the default config against the schema.
