# Installation and runtime prerequisites

## Supported installation routes

For a normal runtime, prefer one coherent binary distribution:

```bash
python -m pip install pyproj
```

or a new conda environment from conda-forge:

```bash
conda config --prepend channels conda-forge
conda config --set channel_priority strict
conda create -n <new-env> -c conda-forge pyproj
conda run -n <new-env> python -c "import pyproj; print(pyproj.__version__)"
```

Do not mix pip and conda packages casually in one environment. pyproj wheels do
not include transformation grids; CRS construction and `Geod` calculations do
not require grids, while some datum transformations do. Choose a grid policy
separately instead of treating installation as grid installation.

## Source-build contract

The current packaging metadata requires Python `>=3.11`, a build backend with
`setuptools>=77.0.1`, and `cython>=3.1`. The source build checks for PROJ
`>=9.4.0`; the runtime should expose a compatible native PROJ library and data
package. `certifi` is a runtime dependency for the CA fallback.

The build searches for a PROJ base directory in this order:

1. `PROJ_DIR`, when set and existing;
2. the packaged internal PROJ directory, when present;
3. a `proj` executable under the Python prefix;
4. a `proj` executable on `PATH`.

`PROJ_LIBDIR` overrides library-directory discovery; otherwise `lib` and
`lib64` beneath the selected base are checked. `PROJ_INCDIR` overrides header
directory discovery; otherwise `include` beneath the base is checked.
`PROJ_VERSION` can supply a version when a PROJ executable is unavailable but
headers/libraries exist. `PROJ_WHEEL` controls inclusion of packaged PROJ data
when building a wheel. `PYPROJ_FULL_COVERAGE` is a build-time Cython coverage
switch, not a runtime data setting.

After a source build, verify with:

```bash
python -c "import pyproj; print(pyproj.__version__, pyproj.__proj_version__, pyproj.__proj_compiled_version__)"
python -m pyproj -v
```

Do not infer successful compilation from the presence of Python files alone;
pyproj imports native extension modules and needs a usable `proj.db`.

## Data-directory resolution

`pyproj.datadir.get_data_dir()` returns a valid directory or raises
`pyproj.exceptions.DataDirError`. A valid directory is one containing
`proj.db`. The effective search order is:

1. a valid path configured by `set_data_dir`;
2. packaged/internal PROJ data;
3. `PROJ_DATA` (PROJ 9.1+) or legacy `PROJ_LIB` (older PROJ);
4. `sys.prefix/share/proj`;
5. the Windows-style `sys.prefix/Library/share/proj` location;
6. a PROJ data tree found relative to `proj` on the prefix or `PATH`.

The environment lookup prefers `PROJ_DATA` when it is present; an invalid
`PROJ_DATA` does not become a fallback to `PROJ_LIB` in the same lookup. Unset
or correct the invalid variable when diagnosing a misleading selection.

```python
from pathlib import Path
from pyproj import datadir

selected = datadir.get_data_dir()              # str; requires proj.db
user = datadir.get_user_data_dir()             # str; no creation
user_for_sync = datadir.get_user_data_dir(True)  # may create the directory

datadir.set_data_dir(Path("/chosen/proj/share/proj"))
datadir.append_data_dir(Path("/chosen/extra-grids"))
```

`set_data_dir` accepts `str` or `Path`, resets validation, and reinitializes
the current PROJ context. `append_data_dir` preserves the existing path first
and adds another path using the platform path separator. The first selected
path must contain the database; appended locations are useful for grid files.
Changing environment variables after import does not by itself rewrite an
already-created context. Start a new process, or use the documented setter for
the intended current-process change.

## Network and certificates

Network access defaults to off unless `PROJ_NETWORK` is truthy. The public API
is:

```python
from pyproj import network

network.is_network_enabled()       # -> bool
network.set_network_enabled(True)  # force remote grid access
network.set_network_enabled(False) # force it off
network.set_network_enabled(None)  # re-read PROJ_NETWORK/default
```

These calls configure the PROJ context; they do not download a grid by
 themselves. Enable only for a bounded, approved operation. For TLS:

```python
network.set_ca_bundle_path()       # certifi fallback if no env override
network.set_ca_bundle_path(True)   # force certifi
network.set_ca_bundle_path(False)  # use system/env configuration
network.set_ca_bundle_path("/path/to/ca-bundle.pem")
```

The environment names consulted for the default/system path are
`PROJ_CURL_CA_BUNDLE`, `CURL_CA_BUNDLE`, and `SSL_CERT_FILE`. A custom path is
passed to the PROJ context; check that it exists and is readable before a
network operation.

## Version and import diagnostics

Use `scripts/diagnose_pyproj.py --help` and then its default invocation for a
read-only report. It reports Python, pyproj, runtime/compiled PROJ versions,
network state, selected/user data directories, `proj.db` presence, and relevant
PROJ environment settings without calling a download API or creating the user
directory.

`pyproj -v`/`pyproj.show_versions()` additionally reports PROJ database metadata
such as recommended PROJ-data, PROJ database layout, EPSG, ESRI, and IGNF
versions. Runtime and compiled PROJ versions should normally agree. A validated
installation for this skill reports PROJ `9.8.1` for both values; the values in
the active runtime are authoritative and may differ by installation.
