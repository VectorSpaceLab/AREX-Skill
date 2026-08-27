---
name: core-pandas-api
description: "Use Modin's pandas-compatible DataFrame and Series API safely and
  verify results against pandas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modin core pandas API

Use this sub-skill when a task asks to replace `import pandas as pd` with `import modin.pandas as pd`, migrate a DataFrame/Series workflow, read CSV-like data into Modin, validate Modin results against pandas, or diagnose default-to-pandas behavior for ordinary pandas-style operations.

## Start here

1. Read [references/workflows.md](references/workflows.md) for migration patterns, correctness checks, and a taxi-style local fixture workflow.
2. Read [references/api-compatibility.md](references/api-compatibility.md) before assuming an operation is parallel, fully implemented, or safe to materialize.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for pandas warnings, dtype/index surprises, multiprocessing guards, performance warmup, and memory pitfalls.
4. Run [scripts/taxi_groupby_smoke.py](scripts/taxi_groupby_smoke.py) to prove the installed package can read a tiny CSV and match pandas for filters/groupby/aggregates.

## Routing boundaries

This sub-skill owns stable `modin.pandas` DataFrame/Series usage, import replacement, small local correctness fixtures, pandas comparisons, `concat`, `merge`, `groupby`, `apply`, `read_csv` starter workflows, and `to_pandas()` validation on bounded samples.

Route engine/backend/resource decisions to `../engines-configuration/SKILL.md`; nontrivial I/O, SQL, glob, Arrow/Ray/Dask conversion, and direct partitions to `../io-interoperability/SKILL.md`; and `modin.experimental`, Modin NumPy, Modin Polars, Batch Pipeline, or Modin XGBoost work to `../advanced-extensions/SKILL.md`.

## Operating pattern

1. Configure the engine before importing Modin if the task names Ray, Dask, Python, Native, or cluster resources.
2. Replace the pandas import only after checking unsupported operations and materialization points.
3. Keep a pandas baseline for tiny fixtures or sampled production data.
4. Compare schema, dtypes where they matter, sorted/index-normalized results, and floating tolerances.
5. Treat `defaulting to pandas` as a performance warning first; verify correctness before rewriting.
6. Avoid calling `to_pandas()` on full distributed data unless the task explicitly requires local materialization.
