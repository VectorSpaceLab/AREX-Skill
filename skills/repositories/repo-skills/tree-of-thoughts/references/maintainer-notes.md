# Maintainer and source-script notes

Read this only when a task asks about repository maintenance, scripts, tests, packaging, or stale automation. Routine package use should route to the sub-skills instead.

## Repository-maintained scripts

The checkout contains several development scripts, but they are not reliable runtime entry points for future agents:

| Source artifact | Status | Reason |
|---|---|---|
| `scripts/auto_docs.py` | reference-only | References removed or renamed symbols such as `ToTAgent` and `tree_of_thoughts.search_algorithms`; calls an OpenAI-backed doc generator and writes docs. |
| `scripts/auto_tests.py` | reference-only | Same stale imports; generates and writes tests with an OpenAI model. |
| `scripts/auto_tests_docs/*.py` | reference-only | Helper prompts and utilities for the stale auto-doc/test flow; not a public package workflow. |
| `scripts/get_package_requirements.py` | adapted | Its dependency-inspection intent is replaced by `scripts/check_tree_of_thoughts_env.py`, which does not mutate repo files. |
| `scripts/requirementstxt_to_pyproject.py` | excluded | Mutates `pyproject.toml` dependency pins in place. |
| `scripts/code_quality.sh` | excluded | References unrelated `zeta/` path and performs formatting mutations. |
| `scripts/del_pycache.sh` | excluded | Destructive cleanup helper. |
| `scripts/playground_to_examples.sh` | excluded | Renames files under an absent `playground/` directory. |
| `scripts/test_name.sh` | excluded | Renames test files; destructive and no tests directory exists in this checkout. |
| `scripts/tests.sh` | reference-only | Simple `pytest` loop over `tests/`, but no tests directory is present in this snapshot. |

Do not tell a future Researcher to run these original source scripts as package usage instructions. If a maintainer task needs to recover them, inspect the current checkout and update imports against the current public modules first.

## Packaging and release evidence

- Distribution name: `tree-of-thoughts`.
- Import package: `tree_of_thoughts`.
- Source package version in metadata: `0.6.5`.
- Build backend: Poetry core.
- Runtime dependencies in metadata/requirements include `swarms`, `swarm-models`, `pydantic`, `loguru`, `python-dotenv`, and `numpy`.
- The release workflow builds a Python package and publishes to PyPI on GitHub release publication.

## Maintenance caveats

- README says license `Apache`, while package metadata says `MIT` and the repository contains a `LICENSE` file. Check the current `LICENSE` before making legal or packaging statements.
- README TODO notes DFS depth/max-loop completion, BFS completion, Monte Carlo search, and visualization as unfinished or desired work. Treat BFS as present but less surfaced because it is not exported by root `__all__` and its example file is empty.
- The package imports `.env` at module import time through `python-dotenv`; maintainer tests should isolate environment variables.
- `string_to_dict` uses `eval`, so hardening this parser would be a high-value maintenance change.
