# Squidpy Repo Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from a Squidpy source checkout and live package inspection. It is intended to be self-contained for future agents; source repository files were evidence, not runtime dependencies.

## Source Snapshot

| Field | Value |
| --- | --- |
| VCS | git |
| Commit | `9f9d5002885fc63cf7f4281f07303af660879704` |
| Branch | `main` |
| Exact tag | none detected |
| Working tree state | dirty: untracked `skills/` directory present |
| Package distribution | `squidpy` |
| Inspected package version | `0.1.dev1+g9f9d50028` |
| Remote URL | https://github.com/scverse/squidpy |

## Evidence Paths

- `pyproject.toml`
- `hatch.toml`
- `README.md`
- `docs/index.md`
- `docs/installation.md`
- `docs/api.md`
- `docs/classes.md`
- `docs/extensibility.md`
- `src/squidpy/__init__.py`
- `src/squidpy/datasets/`
- `src/squidpy/read/`
- `src/squidpy/gr/`
- `src/squidpy/im/`
- `src/squidpy/pl/`
- `src/squidpy/tl/`
- `src/squidpy/experimental/`
- `tests/datasets/`
- `tests/read/`
- `tests/graph/`
- `tests/image/`
- `tests/plotting/`
- `tests/tools/`
- `tests/experimental/`
- `tests/conftest.py`
- `tests/_data/spatial/`
- `skills/squidpy/`

## Scope Notes

Included public runtime surfaces: data loading/readers, spatial graph/statistical analysis, stable image APIs, plotting APIs, tool-layer workflows, and experimental SpatialData imaging. Excluded development-only caches, generated files, review artifacts, CI-only notebook execution, and broad dev/docs dependency groups.

The checkout was dirty because generated skill/review files were present under `skills/`. Future refreshes should compare both the commit and the relative changed-path summary rather than relying on commit alone.
