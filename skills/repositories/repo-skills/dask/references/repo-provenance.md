# Repository Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from repository evidence for the Dask Python package.

## Source Snapshot

| Field | Value |
| --- | --- |
| VCS | git |
| Commit | `c9d1df34ccba182ddf43c2dbe4315c4d9c8c44e1` |
| Branch | `main` |
| Exact tag | none detected |
| Remote URL | https://github.com/dask/dask |
| Working tree state at generation | dirty: generated `skills/` tree was untracked during skill creation |
| Package distribution | `dask` |
| Package version observed during inspection | `0.0.post1+gc9d1df34c` |

## Evidence Paths

- `pyproject.toml`
- `README.rst`
- `dask/__init__.py`
- `dask/__main__.py`
- `dask/cli.py`
- `dask/config.py`
- `dask/dask.yaml`
- `dask/dask-schema.yaml`
- `dask/base.py`
- `dask/delayed.py`
- `dask/core.py`
- `dask/highlevelgraph.py`
- `dask/blockwise.py`
- `dask/_expr.py`
- `dask/_task_spec.py`
- `dask/array/`
- `dask/array/_array_expr/`
- `dask/dataframe/`
- `dask/dataframe/dask_expr/`
- `dask/bag/`
- `dask/bytes/`
- `dask/diagnostics/`
- `dask/tests/`
- `dask/array/tests/`
- `dask/dataframe/tests/`
- `dask/bag/tests/`
- `dask/bytes/tests/`
- `dask/diagnostics/tests/`
- `docs/source/10-minutes-to-dask.rst`
- `docs/source/api.rst`
- `docs/source/array*.rst`
- `docs/source/dataframe*.rst`
- `docs/source/bag*.rst`
- `docs/source/configuration.rst`
- `docs/source/cli.rst`
- `docs/source/diagnostics-local.rst`
- `docs/source/debugging-performance.rst`
- `docs/source/scheduling*.rst`
- `docs/source/best-practices.rst`
- `docs/source/install.rst`
- `pixi.toml`

## Refresh Guidance

Refresh this skill when any of these change substantially:

- Dask public API signatures, collection behavior, scheduler semantics, config defaults, or CLI commands.
- Optional dependency groups, supported Python versions, or the `distributed` version pin.
- The dataframe or array expression systems, query-planning defaults, shuffle behavior, parquet/pyarrow integration, or backend registration.
- Documentation for install, best practices, configuration, diagnostics, scheduling, array, dataframe, bag, or deployment workflows.
- Native tests that encode user-visible behavior for the covered workflows.
