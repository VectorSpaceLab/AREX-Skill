# Vaex configuration

Vaex builds an effective settings object when `vaex` is imported. Inspect it
before changing it:

```python
import vaex
print(vaex.settings.main.dict(by_alias=True))
vaex.settings.main.thread_count = 4  # current process only
```

The CLI equivalents are:

```bash
vaex settings yaml
vaex settings json
vaex settings schema
vaex settings md
```

Use the bundled read-only probe when output compatibility varies:

```bash
python scripts/vaex_settings_probe.py --help
python scripts/vaex_settings_probe.py
python scripts/vaex_settings_probe.py --format yaml
```

## Sources and priority

There are three different concerns that are easy to conflate:

1. **Process environment at import time.** `VAEX_*` values are read when the
   settings objects are constructed. Set them before `import vaex`; changing an
   environment variable afterward does not retroactively rebuild
   `vaex.settings.main`.
2. **Runtime Python assignments.** Assigning to `vaex.settings.main` or one of
   its nested objects changes that process's effective object. It is not a
   persistent configuration write unless `vaex.settings.save()` is explicitly
   called.
3. **The Vaex home YAML file.** The core settings loader reads `main.yml` from
   the Vaex home directory and passes its values into the top-level settings
   model. In the examined implementation those explicit YAML values override
   environment-derived defaults for the same fields. The file name is
   `main.yml` in the implementation; do not assume `main.yaml` is equivalent.

The public configuration document also describes a current-working-directory
`.env` file via dotenv. The core settings source imports dotenv conditionally
but does not call a dotenv loader itself in the examined version; the server
settings model declares `.env` support separately. Treat `.env` behavior as
component/version-dependent: verify with a clean, non-sensitive probe rather
than assuming it overrides an explicit environment variable or home YAML.

Do not infer priority from a generated settings document alone. For a
reproducible diagnosis, record the Vaex version, set one harmless test setting
before import, inspect `vaex settings json`, and keep any test home/config file
isolated from a user's normal configuration.

## Field and environment map

Environment names are case-insensitive in the lightweight settings loader. A
field's explicit `env` name wins; otherwise the nested model prefix and field
name are upper-cased. Common fields include:

| Setting path | Environment variable | Meaning / caution |
| --- | --- | --- |
| `main.home` | `VAEX_HOME` | Base directory for Vaex configuration and data helpers. |
| `main.thread_count` | `VAEX_NUM_THREADS` | Computation thread count; must be positive when set. |
| `main.thread_count_io` | `VAEX_NUM_THREADS_IO` | IO thread count; must be positive when set. |
| `main.path_lock` | `VAEX_LOCK` | Lock-file directory. Do not clean while active processes run. |
| `main.async_` (alias `async`) | `VAEX_ASYNC` | Async execution mode, such as `nest` or `awaitio`. |
| `main.cache.type` | `VAEX_CACHE` | Cache type, for example `memory`, `disk`, or a comma-separated combination. |
| `main.cache.path` | `VAEX_CACHE_PATH` | Disk-cache location; validate space and permissions. |
| `main.cache.disk_size_limit` | `VAEX_CACHE_DISK_SIZE_LIMIT` | Disk cache bound such as `10GB`. |
| `main.cache.memory_size_limit` | `VAEX_CACHE_MEMORY_SIZE_LIMIT` | In-memory cache bound. |
| `main.chunk.size` | `VAEX_CHUNK_SIZE` | Fixed chunk size when set. |
| `main.chunk.size_min` | `VAEX_CHUNK_SIZE_MIN` | Lower automatic chunk bound. |
| `main.chunk.size_max` | `VAEX_CHUNK_SIZE_MAX` | Upper automatic chunk bound. |
| `main.display.max_columns` | `VAEX_DISPLAY_MAX_COLUMNS` | Printed column limit. |
| `main.display.max_rows` | `VAEX_DISPLAY_MAX_ROWS` | Printed row limit. |
| `main.data.path` | `VAEX_DATA_PATH` | Data directory used by data helpers such as examples. |
| `main.fs.path` | `VAEX_FS_PATH` | File-system cache location for remote access. |
| `main.progress.force` | `VAEX_PROGRESS` | Force a progress-bar type. |
| `main.logging.setup` | `VAEX_LOGGING_SETUP` | Whether Vaex configures logging during import. |
| `main.logging.rich` | `VAEX_LOGGING_RICH` | Rich logging output switch. |
| `main.memory_tracker.type` | `VAEX_MEMORY_TRACKER` | Memory tracker mode. |
| `main.task_tracker.type` | `VAEX_TASK_TRACKER` | Task tracker names. |
| `main.server.*` | `VAEX_SERVER_*` where supported | Server settings are optional and belong to the serving route. |

Nested JSON environment variables such as `_VAEX_CACHE` are implementation
details of the settings model. Prefer the documented leaf variable such as
`VAEX_CACHE` or `VAEX_CACHE_PATH` and verify the exact installed version.

## YAML and persistence

`vaex settings yaml` prints the effective object; `json` is easier to parse.
`schema` is intended to print JSON Schema. `md` prints field documentation,
including environment names and Python paths. These commands are read-oriented.

The persistence commands are different:

```bash
# Both commands write Vaex configuration; obtain approval first.
vaex settings save
vaex settings save-defaults
```

In the examined core implementation, both call a save helper that writes a
YAML file below the Vaex home directory. `save` excludes defaults;
`save-defaults` writes all defaults and can record machine-specific paths.
`vaex settings set` currently follows the non-default save behavior but does
not parse `KEY VALUE` arguments. Do not present it as a generic setter.

The helper script is intentionally read-only unless the caller passes both
`--save-effective` and `--confirm-save`:

```bash
python scripts/vaex_settings_probe.py --save-effective --confirm-save
```

Use `--runtime-set path=value` only for a clearly scoped, current-process probe.
It does not persist the override after the script exits.

## Schema and drift handling

A schema request can fail in a version where the settings model does not expose
`schema_json`; `yaml-diff` can likewise fail if the lightweight model does not
support `exclude_defaults`. These failures do not prove that the settings are
invalid. Capture the exact version and use the probe's field summary/fallback.
When comparing settings across machines, normalize home/cache/data/lock paths,
then compare field names, types, and explicitly set values rather than raw
serialized defaults.
