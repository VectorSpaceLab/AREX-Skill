---
name: dask
description: "Use this repo skill for Dask, the Python parallel computing
  library, when working with lazy task graphs, schedulers, Dask Array, Dask
  DataFrame, Dask Bag/bytes IO, configuration, diagnostics, CLI usage, or
  contributor validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Dask Repo Skill

Use this skill when a task involves Dask's public APIs, internal task-graph model, collection workflows, configuration, diagnostics, or contributor test/build practices. Dask provides lazy parallel collections and schedulers for Python analytics: delayed objects, arrays, dataframes, bags, low-level task graphs, and local/distributed execution integrations.

## First Checks

- Import check: `python -c "import dask; print(dask.__version__)"`.
- CLI check: `dask --help` should show `config`, `docs`, and `info` command groups.
- Minimal compute check: `python scripts/dask_package_smoke.py --scheduler synchronous`.
- Install extras: use `dask[array]` for array workflows, `dask[dataframe]` for dataframe workflows, `dask[diagnostics]` for local dashboard/profiling helpers, and `dask[distributed]` only when remote cluster APIs are needed.

## Route By Task

- **Core graphs and schedulers:** Use `sub-skills/core-graphs-schedulers/SKILL.md` for `dask.delayed`, `compute`, `persist`, `optimize`, annotations, tokenization, HighLevelGraph, low-level task specs, scheduler choice, and graph debugging.
- **Array workflows:** Use `sub-skills/array-workflows/SKILL.md` for `dask.array`, chunk planning, `from_array`, slicing, `map_blocks`, `blockwise`, reductions, overlap, rechunking, gufuncs, random arrays, linalg, FFT, stats, and array backend caveats.
- **DataFrame workflows:** Use `sub-skills/dataframe-workflows/SKILL.md` for `dask.dataframe`, pandas-like APIs, CSV/Parquet/JSON/SQL IO, partitions/divisions, joins, groupby, shuffle, repartitioning, pyarrow strings, categoricals, and `dask_expr` query planning.
- **Bag and bytes workflows:** Use `sub-skills/bag-bytes-workflows/SKILL.md` for `dask.bag`, `dask.bytes`, text and byte IO, JSON-like records, Avro, fsspec URLs, compression, `foldby`, and small-file object pipelines.
- **Configuration, diagnostics, and CLI:** Use `sub-skills/configuration-diagnostics-cli/SKILL.md` for `dask.config`, YAML config paths, environment variables, `dask config`, `dask info`, local profilers, progress bars, callbacks/cache, install extras, and contributor validation commands.

## Shared References

- Read `references/installation-and-environment.md` when choosing extras, verifying imports, or diagnosing optional dependency availability.
- Read `references/troubleshooting.md` for cross-cutting failures that affect multiple Dask collections or schedulers.
- Read `references/repo-provenance.md` before relying on this skill for a changed checkout; refresh the skill when commit, package version, or major evidence paths drift.

## Dask Working Rules

- Keep graph construction lazy. Do not call `.compute()` or `.persist()` inside collection methods or while defining a reusable graph unless the user explicitly wants materialization.
- Use metadata, divisions, chunks, dtypes, and `meta` objects to infer output shape/schema instead of computing sample data.
- Choose the smallest collection that matches the data model: delayed for arbitrary Python functions, array for NumPy-like blocked tensors, dataframe for pandas-like tabular data, bag for unordered Python records, and bytes for low-level file blocks.
- Prefer explicit scheduler and config scopes when reproducing behavior: `with dask.config.set({...}): ...` and `compute(..., scheduler="synchronous")` for deterministic local debugging.
- Treat `array.query-planning` and `dataframe.query-planning` as import-time configuration; set them before importing the relevant collection modules in a fresh process.
- For dataframe and array APIs, validate `meta`, chunks, divisions, and optional dependency requirements before changing algorithms.

## Validation Pattern

1. Run the root smoke script for package-level sanity.
2. Run the owning sub-skill smoke script for the collection or support workflow.
3. Add a tiny fixture or in-memory example that exercises the changed route.
4. For repo contribution work, run the narrowest relevant pytest selection before broader suites.
5. Record skipped native cases separately when they require network, GPU, distributed services, large data, or credentials.

## Common Pitfalls

- Importing `dask.dataframe` without the dataframe extra can fail due to missing pandas or pyarrow.
- Unknown chunks or divisions often make otherwise valid operations expensive, ambiguous, or unsupported.
- Multiprocessing schedulers require pickleable functions and guarded entry points; use threads or synchronous mode for quick debugging.
- Config files may be read from multiple paths; `dask config find <key>` is the safest way to diagnose where a value comes from.
- Optional GPU/cloud/storage backends are not part of the base package; keep those checks conditional and skip unsafe native cases unless dependencies and hardware are available.
