---
name: array-workflows
description: "Use when working with Dask Array: chunked NumPy-like arrays,
  `dask.array.from_array`, chunk planning, slicing, `map_blocks`, `blockwise`,
  reductions, overlap, rechunking, generalized ufuncs, random arrays,
  linalg/FFT/stats, optional array backends, or array query-planning caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Dask Array Workflows

Use this sub-skill for Dask Array workflows where the primary object is `dask.array.Array`, a lazy blocked array built from NumPy or NumPy-like chunks. Dask Array is best for arrays too large for memory, multi-file/image stacks, blocked numerical algorithms, and NumPy-style code that can run independently on chunks.

## Route First

- For generic graph construction, scheduler choice, `compute`, `persist`, annotations, delayed objects, or HighLevelGraph internals, route to `../core-graphs-schedulers/SKILL.md`.
- For converting Dask DataFrame partitions to arrays, unknown row counts from dataframe conversion, or dataframe IO/shuffle decisions, route to `../dataframe-workflows/SKILL.md` and return here for array-only operations.
- For `array.chunk-size`, `array.rechunk.*`, `array.slicing.split_large_chunks`, `array.query-planning`, CLI inspection, diagnostics, or profiling, route to `../configuration-diagnostics-cli/SKILL.md`.

## Start Here

1. Identify the source array: in-memory NumPy, HDF5/Zarr/NetCDF-like object with NumPy slicing, delayed image/file loader, random generator, dataframe conversion, or optional backend such as CuPy or sparse.
2. Choose chunks before building the graph. Prefer chunks that fit comfortably in memory, do meaningful work per task, align with storage chunks, and match the main access/reduction pattern.
3. Keep operations lazy while defining arrays. Do not call `compute()` or `persist()` in the middle of graph construction unless the user explicitly requests materialization or chunk-size discovery.
4. Use high-level operations first: arithmetic/ufuncs, slicing, reductions, `stack`, `concatenate`, `rechunk`, `map_blocks`, `map_overlap`, `blockwise`, and `apply_gufunc`.
5. Validate shape, dtype, chunks, and graph size before broad execution; use tiny local examples when diagnosing shape or metadata issues.

## Reference Map

- `references/api-reference.md` lists the core Dask Array APIs, signatures, and when to use each family.
- `references/workflows.md` gives task-oriented recipes for creation, slicing, reductions, `map_blocks`, `blockwise`, overlap, gufuncs, random, linalg, FFT, stats, and optional backends.
- `references/chunking-and-performance.md` explains chunk forms, unknown chunks, storage alignment, rechunk planning, slicing chunk warnings, and query-planning flags.
- `references/troubleshooting.md` maps common Dask Array errors and performance symptoms to fixes.
- `scripts/array_smoke.py` is a fixture-free smoke check for array creation, chunks, `map_blocks`, overlap, rechunk, and compute.

## Safe Smoke Check

From the sub-skill directory or a copied skill installation, run:

```bash
python scripts/array_smoke.py --help
python scripts/array_smoke.py
```

The script uses only tiny in-memory arrays and asserts chunk metadata plus computed values. It does not require a source checkout, GPU, network, or external data files.
