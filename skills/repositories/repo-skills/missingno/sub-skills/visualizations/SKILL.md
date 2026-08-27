---
name: visualizations
description: "Guides missingno matrix, bar, heatmap, and dendrogram missing-data
  visualization workflows, configuration, interpretation, and plotting
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# missingno Visualizations

Use this sub-skill when a task asks how to make, configure, interpret, save, or
troubleshoot `missingno` plots for pandas DataFrames.

## Choose the plot

| Need | Use | Why |
| --- | --- | --- |
| See row-by-row and column-by-column missingness patterns | `msno.matrix(df, ...)` | Dense nullity matrix with optional sparkline for row completeness. |
| Compare per-column completeness counts/ratios | `msno.bar(df, ...)` | Simpler bar view for variable completeness, with optional log scale. |
| Find pairwise nullity correlation between variables | `msno.heatmap(df, ...)` | Correlates missing/present masks and annotates relationships. |
| Group variables by similar missingness patterns | `msno.dendrogram(df, ...)` | Uses SciPy hierarchical clustering of nullity masks. |

For column filtering or completeness sorting before plotting, read
[../nullity-utilities/SKILL.md](../nullity-utilities/SKILL.md).

## Fast workflow

```python
import matplotlib.pyplot as plt
import missingno as msno

# df is a pandas.DataFrame.
ax = msno.matrix(df, sparkline=False)
ax.figure.savefig("missingness-matrix.png", bbox_inches="tight")
plt.close(ax.figure)
```

In headless environments, set `MPLBACKEND=Agg` before running the script. For a
safe end-to-end package check, run the root helper:
[../../scripts/missingno_smoke_check.py](../../scripts/missingno_smoke_check.py).

## References

- Read [references/workflows.md](references/workflows.md) for plot-selection
  recipes, interpretation notes, saving figures, large-column handling, and
  time-index examples.
- Read [references/api-reference.md](references/api-reference.md) for verified
  function signatures, parameter behavior, return values, and source-backed
  implementation notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  headless matplotlib, label overlap, `freq` errors, dropped heatmap columns,
  stale `inline`/`geoplot` mentions, and dependency issues.

## Decision points

1. If a user asks for a single visual overview, start with `matrix` for small to
   medium column counts and `bar` when only completeness percentages are needed.
2. If a user asks whether missingness in two columns is related, use `heatmap`;
   explain that columns that are always full or always empty are removed before
   correlation.
3. If a user asks about broader missingness groups or many variables, use
   `dendrogram`; consider filtering to relevant columns first.
4. If a plot is unreadable because there are many variables, reduce labels,
   change orientation where supported, or route to
   [../nullity-utilities/SKILL.md](../nullity-utilities/SKILL.md) for
   `filter='bottom'`, `n=...`, and `p=...` preparation.
5. If the task uses a time index with `matrix(freq=...)`, confirm the DataFrame
   index is a `PeriodIndex` or `DatetimeIndex` and that the requested frequency
   produces ticks found in the index range.

## Boundaries

- This sub-skill does not cover generic seaborn/matplotlib styling except where
  needed to save/customize returned axes.
- This sub-skill does not claim `geoplot` or `inline` support for this snapshot.
- This sub-skill does not require network sample data; use small synthetic
  frames for examples and checks.
