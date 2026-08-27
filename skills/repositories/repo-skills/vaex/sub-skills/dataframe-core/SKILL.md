---
name: dataframe-core
description: "Create, inspect, filter, and validate Vaex DataFrames while
  preserving lazy out-of-core semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# dataframe-core

Use this sub-skill when a task is about the Vaex `DataFrame` object itself: creating small or large DataFrames, inspecting columns and shape, writing filters or selections, adding virtual columns, validating expressions, and debugging missing values or unusual column names without accidentally materializing an out-of-core dataset.

## Load these references

- Start with [references/dataframe-workflows.md](references/dataframe-workflows.md) for concrete recipes: constructors, inspection, slicing/filtering, selections, virtual columns, non-identifier column names, missing values, and Pandas-to-Vaex translations.
- Use [references/api-reference.md](references/api-reference.md) for verified signatures and object-method notes.
- Use [references/troubleshooting.md](references/troubleshooting.md) when imports, file opening, expressions, filters, missing values, or memory use surprise the user.
- Run [scripts/dataframe_smoke.py](scripts/dataframe_smoke.py) as a safe installed-package check before relying on Vaex core behavior in a new environment.

## Core operating rules

1. Treat Vaex as lazy and out-of-core by default. Prefer expressions, virtual columns, selections, filters, `count`, and aggregations over `.values`, `.to_numpy()`, `np.array(df)`, `to_pandas_df`, or full `evaluate` calls.
2. Use `evaluate` intentionally and bounded: pass `i1`/`i2`, `selection=...`, `array_type=...`, or iterate with chunks when the result may be large.
3. For column names that contain spaces, punctuation, keywords, or symbols, use bracket access (`df['column name']`) or pass the `Expression` object to methods instead of relying on attribute access or raw expression strings.
4. Distinguish filters from selections. `df[df.x > 0]` and `df.filter(...)` return shallow filtered DataFrames; `df.select(...)` stores a named selection on the same DataFrame for statistics, evaluation, and visualization.
5. Add derived columns as virtual columns (`df['new'] = expression` or `df.add_virtual_column(...)`) unless an in-memory array is intentionally small and has the unfiltered DataFrame length.

## Boundaries

- Route detailed file formats, export, conversion, cloud/open plugin setup, and CLI conversion tasks to `../io-conversion/SKILL.md`.
- Route statistical, groupby, binby/grid, join, sort, unique, and value-count recipes to `../expressions-analytics/SKILL.md`; this sub-skill only introduces the concepts needed to inspect or validate the DataFrame.
- Route ML transformations, `vaex.ml`, pipelines, encoders, scalers, and sklearn integration to `../ml-pipelines/SKILL.md`.
- Route plotting, Jupyter widgets, progress-bar UI, and visualization troubleshooting to `../visualization-jupyter/SKILL.md`.
