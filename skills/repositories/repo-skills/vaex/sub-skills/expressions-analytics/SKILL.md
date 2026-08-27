---
name: expressions-analytics
description: "Use Vaex expressions, virtual columns, selections, statistics,
  groupby/binby grids, joins, sorting, accessors, and analytic validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# expressions-analytics

Use this sub-skill when the task is to transform, aggregate, validate, or join data that is already represented as a Vaex DataFrame. Keep the DataFrame lazy where possible: express calculations as Vaex expressions or virtual columns, then ask Vaex for statistics, grouped results, grids, or a bounded evaluated slice.

## Route first

- DataFrame construction, basic lazy semantics, and minimal inspection: [../dataframe-core/SKILL.md](../dataframe-core/SKILL.md).
- File import/export/conversion or materializing a persisted dataset: [../io-conversion/SKILL.md](../io-conversion/SKILL.md).
- Plotting histograms, heatmaps, scatter plots, or Jupyter widgets from analytic grids: [../visualization-jupyter/SKILL.md](../visualization-jupyter/SKILL.md).
- ML feature pipelines, encoders, scalers, predictors, and pipeline persistence: [../ml-pipelines/SKILL.md](../ml-pipelines/SKILL.md).

## Operating rules

1. Prefer Vaex expressions over eager arrays: `df.x + df.y`, `df['column with spaces']`, and NumPy ufuncs on expressions stay lazy.
2. Add reusable derived data as virtual columns with `df['new'] = expr` or `df.add_virtual_column('new', expr)`; do not call `.values`, `.to_numpy()`, `np.array(df)`, or `to_pandas_df()` unless the requested result is known to fit in memory.
3. Validate expressions on a slice before full execution: `df.evaluate(expr, i1=0, i2=min(5, len(df)))` or `expr.evaluate(i1=0, i2=5)`.
4. Use selections for repeated subset statistics and filtered DataFrames for Pandas-like narrowing. Remember that joins ignore filters unless a filtered DataFrame is first extracted.
5. For aggregations, use Vaex statistics (`mean`, `sum`, `std`, `count`, `minmax`, `correlation`, `percentile_approx`, `mutual_information`) and `df.groupby(..., agg=...)`/`vaex.agg` rather than materializing intermediate arrays.
6. For high-cardinality groupby or join keys, check cardinality (`unique`, `value_counts`, `row_limit`) and missing-value semantics before running a large job.
7. Joins default to left joins and build lookup/index structures rather than copying the whole right table. Diagnose duplicate right keys before using `allow_duplication=True`.

## Reference map

- [references/expressions-and-selections.md](references/expressions-and-selections.md): expression objects, virtual columns, selections/filters, bounded evaluation, string/datetime/struct/geo accessors, and derived-column recipes.
- [references/analytics-reference.md](references/analytics-reference.md): statistics, groupby/binby grids, joins, sorting, API signatures, and analytic validation patterns.
- [references/troubleshooting.md](references/troubleshooting.md): expression parse/name errors, non-identifier columns, missing/NaN/category groups, materialization surprises, join cardinality, grid shape/limit issues, and accessor failures.

## Bundled check

Run a tiny installed-package smoke check after editing this sub-skill or when diagnosing an environment:

```bash
python scripts/analytics_smoke.py --help
python scripts/analytics_smoke.py
```

The script creates in-memory DataFrames only, uses public Vaex APIs, and asserts expression, virtual-column, selection, statistic, groupby, binby, join, sorting, and accessor behavior.
