# Backend and writer plugins

hls4ml can discover third-party backends and writers without changing the core package. This reference covers the discovery contract and the safest way to inspect it.

## Discovery contract

| Signal | Meaning | What to provide |
| --- | --- | --- |
| Entry point group `hls4ml.backends` | The package importer scans this group during backend import. | A callable entry point that performs registration. |
| Environment variable `HLS4ML_BACKEND_PLUGINS` | Ad hoc plugin modules listed here are imported and treated as registration hooks. | A separator-separated list of importable module names. Each module should expose a `register` callable. |
| `register_backend` helper | Registers a backend instance in the backend registry. | A backend name and a backend class. |
| `register_writer` helper | Registers the writer used by a backend. | A writer name and a writer class. |

## Plugin callable contract

A plugin callable should register both the backend and the writer for that backend.

Recommended signature:

- `register(*, register_backend, register_writer)`

The loader first tries keyword arguments. If that raises a `TypeError`, it retries with positional arguments in the same order. If the callable fails, the loader prints a warning and continues with the next plugin.

## Failure behavior

Plugin discovery is intentionally tolerant. Failures are reported as warnings instead of stopping the import path.

Typical warning patterns:

- `WARNING: failed to load backend plugin entry "..."`
- `WARNING: failed to import backend plugin module "..."`
- `WARNING: plugin entry "..." did not provide a usable backend registration (...)`
- `WARNING: backend plugin callable "..." failed: ...`

Treat these as discovery failures, not conversion failures. Capture stdout when you are diagnosing plugin visibility.

## Registration notes

- Backend names are case-insensitive in the backend registry, but you should still use one canonical name for the backend and writer pair.
- Duplicate backend, writer, or plugin registration names raise or warn during loading.
- Backends can also register their own passes, flows, templates, and source files after the backend object is created.
- If a plugin needs non-Python assets, ship them as package data so they are installed with the plugin distribution.

## Safe inspection

Use `scripts/inspect_plugins.py` first when you only want discovery metadata.

The script reports:

- the entry point group,
- the environment variable name,
- statically discovered built-in backend names,
- advertised plugin entry points,
- raw module names from the environment variable.

It does not import plugin modules.

## Trusted runtime check

If you trust the plugin package and want the final loaded registry, import `hls4ml.backends` in a controlled environment and inspect the available backend names after import. That path executes plugin code, so do it only when the plugin is trusted.
