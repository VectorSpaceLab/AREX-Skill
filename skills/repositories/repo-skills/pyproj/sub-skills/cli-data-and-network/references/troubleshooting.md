# CLI, data, and native-runtime troubleshooting

## Triage order

1. Run `python scripts/diagnose_pyproj.py` from the installed skill tree. It is
   read-only and distinguishes import failure from data-directory failure.
2. Run `python -m pyproj -v` if import succeeds. Compare `PROJ (runtime)` and
   `PROJ (compiled)`, selected `data dir`, user directory, and database metadata.
3. Inspect only the relevant environment settings: `PROJ_DATA`, legacy
   `PROJ_LIB`, `PROJ_NETWORK`, `PROJ_CURL_CA_BUNDLE`, `CURL_CA_BUNDLE`, and
   `SSL_CERT_FILE`. Remove stale overrides in the process that launches Python.
4. Start a fresh process after environment changes, then repeat the diagnostic.
5. Only after import/data checks pass, debug a missing grid or transform
   operation in [`../../coordinate-transformations/SKILL.md`](../../coordinate-transformations/SKILL.md).

## Import or native-extension failure

Symptoms include `ModuleNotFoundError` for a pyproj native module, an undefined
symbol, a shared-library loading error, or a crash during import. Check:

- Python meets the package's supported version (`>=3.11` for this build).
- A wheel or conda package was installed as one coherent pyproj/PROJ pair.
- A source build had Cython available and used PROJ `>=9.4.0` headers and
  libraries from the same installation.
- `PROJ_DIR`, `PROJ_LIBDIR`, `PROJ_INCDIR`, and `PROJ_VERSION` do not point at
  different installations; `PROJ_DIR` is a base, not the library or data
  directory itself.
- The process is not loading a stale extension or shared library from another
  prefix. Reinstall into a clean environment rather than copying `.so`/`.dll`
  files between environments.

If import still fails, record the exact exception and the Python/OS/package
versions. Do not “fix” it by changing data variables; data paths cannot repair a
missing binary extension.

## `SQLite error on SELECT`, invalid `proj.db`, or wrong CRS database

This usually means the native PROJ library opened a database from an
incompatible or mixed data tree. `get_data_dir()` validates presence of
`proj.db`, not that every file is version-compatible. Resolve it as follows:

1. Print the selected path with `pyproj.datadir.get_data_dir()` and run the
   verbose version report.
2. Check whether `PROJ_DATA` is set. It takes precedence over legacy `PROJ_LIB`
   when present; an invalid `PROJ_DATA` can prevent the expected legacy fallback.
3. Unset stale `PROJ_DATA`/`PROJ_LIB`, or set exactly one known-good data tree
   containing the database shipped for the active native PROJ.
4. Do not prepend a different installation's `share/proj` directory merely to
   find a missing grid. Use `datadir.append_data_dir()` only for a compatible
   extra grid path, with the database-bearing path first.
5. Restart Python and validate a harmless CRS/database lookup. If the error
   persists, reinstall a matching pyproj and PROJ distribution.

An explicit current-process override is:

```python
from pyproj.datadir import set_data_dir
set_data_dir("/chosen/proj/share/proj")
```

The directory must contain a compatible `proj.db`; a dummy file or a directory
from another PROJ generation is not sufficient.

## `DataDirError` or no data directory

`get_data_dir()` raises `DataDirError` when none of its candidates contains
`proj.db`. Check the actual directory layout (`share/proj/proj.db`), correct
`PROJ_DATA`/`PROJ_LIB`, or reinstall the data package. Do not point `PROJ_DATA`
at the parent `share` directory or at a grid-only directory. A grid-only path
can be appended after a valid database path, but cannot replace it.

## Network, TLS, and checksum failures

`network.is_network_enabled()` is false by default in the verified runtime.
Use `network.set_network_enabled(True)` only for an approved bounded operation;
this controls PROJ remote access but does not select or download files by itself.
For certificate errors, inspect the three CA environment variables, verify a
custom path is readable, or use `network.set_ca_bundle_path(True)` to use the
certifi bundle. Do not disable certificate verification as a workaround.

For `sync` failures:

- ensure the manifest/target directory exists and is writable;
- use a narrow filter and an explicit target rather than `--all`;
- keep the checksum check and remove any stale `.part` file before retrying;
- check disk space and proxy/firewall policy;
- distinguish a missing URL in the manifest from a transient transport error;
- rerun `--list-files` before retrying a changed or broad selection.

A `files.geojson` cache can be refreshed by removing or aging that cache only
when the caller explicitly permits filesystem mutation. The bundled diagnostic
never does this.

## CLI misuse

`--target-directory` and `--system-directory` are mutually exclusive.
`--all` conflicts with `--list-files`, `--source-id`, `--area-of-use`, `--bbox`,
and `--file`. A bbox must contain four comma-separated numbers. If a command
prints help unexpectedly, include one of the actual selection arguments. If a
list has only a header, the filters or `include_already_downloaded` policy may
have excluded every feature; broaden one filter for diagnosis, then restore a
bounded selection.
