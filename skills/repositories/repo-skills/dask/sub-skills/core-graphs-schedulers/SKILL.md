---
name: core-graphs-schedulers
description: "Use this sub-skill for Dask delayed, task graph inspection,
  HighLevelGraph concepts, scheduler selection,
  compute/persist/optimize/annotate behavior, tokenization, graph manipulation,
  and custom collection basics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Core Graphs and Schedulers

Use this sub-skill when the task is about Dask's core lazy execution model rather than a collection-specific API.

## Route Here For

- Building lazy graphs with `dask.delayed`, `dask.compute`, `dask.persist`, `dask.optimize`, and `dask.annotate`.
- Inspecting low-level task dicts, `HighLevelGraph` layers/dependencies, task keys, tokenization, and scheduler inputs.
- Choosing local schedulers: `synchronous`, `threads`, `processes`, or explicit scheduler get functions.
- Debugging graph construction, optimization/fusion, multiprocessing serialization, graph visualization, or non-deterministic tokens.
- Implementing or reviewing custom Dask collections that expose the `__dask_*__` protocol.

## Route Elsewhere

- NumPy-like arrays, chunks, blockwise array operations, reductions, gufuncs, or rechunking: `../array-workflows/SKILL.md`.
- Pandas-like dataframes, partitions, IO, groupby, joins, shuffle, or query planning: `../dataframe-workflows/SKILL.md`.
- Bag, text, JSON, bytes, compression, and filesystem ingestion workflows: `../bag-bytes-workflows/SKILL.md`.
- Config files, CLI commands, diagnostics, progress bars, profilers, and install/runtime environment checks: `../configuration-diagnostics-cli/SKILL.md`.

## Start Here

1. Decide whether the user needs lazy graph construction, graph inspection, scheduler selection, or custom collection internals.
2. Keep graph definition lazy: build Dask collections first, then call `compute()` or `persist()` once at the boundary.
3. Prefer collection APIs when the work naturally fits arrays, dataframes, or bags; use `delayed` as a release valve for custom Python functions.
4. Use `scheduler="synchronous"` and `optimize_graph=False` for debugging; switch to `threads` or `processes` only after graph structure is correct.
5. For multiprocessing, use importable top-level functions and a `if __name__ == "__main__":` guard in scripts.

## Bundled References

- `references/api-reference.md`: API signatures, graph objects, scheduler get functions, tokenization, graph manipulation, and custom collection hooks.
- `references/workflows.md`: common lazy graph workflows, scheduler-choice recipes, graph inspection patterns, and custom collection checklist.
- `references/troubleshooting.md`: fixes for eager execution, scheduler mismatches, pickling failures, non-deterministic tokens, Graphviz, and optimization surprises.

## Bundled Script

Run `scripts/core_smoke.py --help` for options. The script builds delayed tasks, inspects graph metadata, computes the result with a chosen scheduler, and prints JSON suitable for quick environment checks.
